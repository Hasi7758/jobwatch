#!/usr/bin/env python3
"""
munich-jobwatch
================
每天抓一次慕尼黑相关职位,只报告"今天第一次见到"的那些。

核心思路:不相信任何平台标注的发布日期(StepStone 之类经常滞后半个月),
而是自己建库记录每个职位 ID 第一次出现的时间。首次出现 = 新职位。

用法:
    python jobwatch.py run                # 抓取 + 差分 + 生成报告
    python jobwatch.py discover <slug>... # 探测某公司用的是哪套招聘系统
    python jobwatch.py stats              # 看数据库里有多少条
    python jobwatch.py reset              # 清空数据库重新开始
"""

import argparse
import html
import json
import os
import re
import sqlite3
import sys
import time
import webbrowser
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

try:
    import requests
except ImportError:
    sys.exit("缺少依赖,请先运行:  pip install requests pyyaml")

try:
    import yaml
except ImportError:
    sys.exit("缺少依赖,请先运行:  pip install requests pyyaml")

from names import NameMatcher


BASE = Path(__file__).resolve().parent
IGM_PATH = BASE / "igmetall.yaml"
DB_PATH = BASE / "jobs.db"
CONFIG_PATH = BASE / "config.yaml"
COMPANIES_PATH = BASE / "companies.yaml"
OUT_HTML = BASE / "digest.html"
DOCS_HTML = BASE / "docs" / "index.html"   # GitHub Pages 用
IN_CI = bool(os.environ.get("GITHUB_ACTIONS") or os.environ.get("CI"))

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 " \
     "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"

session = requests.Session()
session.headers.update({"User-Agent": UA, "Accept": "application/json, text/xml, */*"})


# ----------------------------------------------------------------------------
# 数据结构
# ----------------------------------------------------------------------------

@dataclass
class Job:
    uid: str            # 全局唯一 key,用于差分
    source: str         # 来源标识
    company: str
    title: str
    location: str
    url: str
    posted: str = ""    # 来源自己声称的发布日期(仅供参考,不作为判断依据)
    extra: dict = field(default_factory=dict)


# ----------------------------------------------------------------------------
# 配置
# ----------------------------------------------------------------------------

def load_yaml(path, default=None):
    if not path.exists():
        return default if default is not None else {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or (default if default is not None else {})


def load_config():
    cfg = load_yaml(CONFIG_PATH)
    if not cfg:
        sys.exit(f"找不到配置文件 {CONFIG_PATH}")
    cfg.setdefault("keywords", {})
    cfg["keywords"].setdefault("include", [])
    cfg["keywords"].setdefault("exclude", [])
    cfg.setdefault("location", {})
    cfg["location"].setdefault("terms", ["münchen", "munich", "muenchen"])
    cfg["location"].setdefault("allow_remote", True)
    cfg["location"].setdefault("plz_prefixes", ["80", "81", "82", "85"])
    cfg.setdefault("arbeitsagentur", {})
    cfg["arbeitsagentur"].setdefault("enabled", True)
    cfg["arbeitsagentur"].setdefault("radius_km", 25)
    cfg["arbeitsagentur"].setdefault("published_within_days", 2)
    cfg["arbeitsagentur"].setdefault("queries", [""])
    cfg.setdefault("telegram", {})
    cfg["telegram"].setdefault("enabled", False)
    cfg.setdefault("employers", {})
    cfg["employers"].setdefault("enabled", False)
    cfg["employers"].setdefault("mode", "strict")
    cfg.setdefault("open_browser", True)
    return cfg


def load_matcher(cfg):
    """加载 IG Metall 雇主白名单。"""
    if not cfg["employers"].get("enabled"):
        return None
    if not IGM_PATH.exists():
        print("  [白名单] 找不到 igmetall.yaml,先跑 import_igm.py。本次跳过过滤。")
        return None
    d = load_yaml(IGM_PATH, default={})
    names = [e.get("name") if isinstance(e, dict) else str(e)
             for e in (d.get("employers") or [])]
    aliases = cfg["employers"].get("aliases") or {}
    m = NameMatcher([n for n in names if n], aliases=aliases)
    print(f"  [白名单] 载入 {len(m)} 家 IG Metall 雇主"
          + (f"(含 {len(aliases)} 条别名)" if aliases else ""))
    return m if len(m) else None


# ----------------------------------------------------------------------------
# 数据库(差分的核心)
# ----------------------------------------------------------------------------

def db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            uid        TEXT PRIMARY KEY,
            source     TEXT,
            company    TEXT,
            title      TEXT,
            location   TEXT,
            url        TEXT,
            posted     TEXT,
            first_seen TEXT,
            igm        TEXT DEFAULT ''
        )
    """)
    conn.execute("CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT)")
    conn.commit()
    return conn


def is_first_run(conn):
    row = conn.execute("SELECT v FROM meta WHERE k='seeded'").fetchone()
    return row is None


def mark_seeded(conn):
    # 记下基线里最晚的 first_seen,之后凡是严格大于它的才算"新"
    row = conn.execute("SELECT COALESCE(MAX(first_seen),'') FROM jobs").fetchone()
    conn.execute("INSERT OR REPLACE INTO meta VALUES ('seeded', ?)", (row[0],))
    conn.commit()


def split_new(conn, jobs):
    """返回数据库里还没有的职位,并把全部职位写入库。"""
    known = {r[0] for r in conn.execute("SELECT uid FROM jobs")}
    now = datetime.now(timezone.utc).isoformat()
    fresh = []
    for j in jobs:
        if j.uid in known:
            continue
        known.add(j.uid)
        fresh.append(j)
        conn.execute(
            "INSERT OR IGNORE INTO jobs VALUES (?,?,?,?,?,?,?,?,?)",
            (j.uid, j.source, j.company, j.title, j.location, j.url,
             j.posted, now, j.extra.get("igm", "")),
        )
    conn.commit()
    return fresh


def recent_days(conn, days=7):
    """基线之后、最近 N 天内首次出现的职位,按日期分组(新的在前)。"""
    row = conn.execute("SELECT v FROM meta WHERE k='seeded'").fetchone()
    seeded = row[0] if row else ""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    rows = conn.execute(
        "SELECT company,title,location,url,posted,source,first_seen,igm "
        "FROM jobs WHERE first_seen > ? AND first_seen >= ? "
        "ORDER BY first_seen DESC",
        (seeded, cutoff)).fetchall()
    groups = {}
    for c, t, l, u, p, s, fs, igm in rows:
        j = Job(uid="", source=s, company=c, title=t, location=l, url=u, posted=p)
        if igm:
            j.extra["igm"] = igm
        groups.setdefault(fs[:10], []).append(j)
    return sorted(groups.items(), reverse=True)


# ----------------------------------------------------------------------------
# 过滤
# ----------------------------------------------------------------------------

def matches_keywords(job, kw):
    hay = f"{job.title} {job.company}".lower()
    inc, exc = kw.get("include") or [], kw.get("exclude") or []
    if any(e.lower() in hay for e in exc):
        return False
    if not inc:
        return True
    return any(i.lower() in hay for i in inc)


def matches_location(job, loc):
    text = f"{job.location}".lower()
    if not text.strip():
        return True  # 位置信息缺失时不误杀,交给关键词过滤
    if any(t.lower() in text for t in loc.get("terms", [])):
        return True
    if loc.get("allow_remote") and re.search(r"remote|home\s?office|ortsunabh", text):
        return True
    for p in loc.get("plz_prefixes", []):
        if re.search(rf"\b{p}\d{{3}}\b", text):
            return True
    return False


# ----------------------------------------------------------------------------
# 来源 1:德国联邦劳动局官方 API(免费,覆盖面最广)
# ----------------------------------------------------------------------------

AA_URL = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs"
AA_KEY = "jobboerse-jobsuche"   # 这是官方公开的固定 key,不是私人凭证


def fetch_arbeitsagentur(cfg):
    ac = cfg["arbeitsagentur"]
    if not ac.get("enabled"):
        return []
    out, seen = [], set()
    for query in ac.get("queries") or [""]:
        for page in range(1, 11):          # 最多 10 页,每页 100 条
            params = {
                "wo": ac.get("city", "München"),
                "umkreis": ac["radius_km"],
                "veroeffentlichtseit": ac["published_within_days"],
                "size": 100,
                "page": page,
                "angebotsart": 1,          # 1 = 普通岗位
            }
            if query:
                params["was"] = query
            try:
                r = session.get(AA_URL, params=params,
                                headers={"X-API-Key": AA_KEY}, timeout=25)
                if r.status_code != 200:
                    print(f"  [劳动局] HTTP {r.status_code}"
                          f"{' — 接口可能已变更,见 README 说明' if r.status_code == 404 else ''}")
                    break
                data = r.json()
            except Exception as e:
                print(f"  [劳动局] 请求失败: {e}")
                break

            items = data.get("stellenangebote") or []
            for it in items:
                refnr = it.get("refnr") or it.get("hashId") or ""
                if not refnr or refnr in seen:
                    continue
                seen.add(refnr)
                ort = it.get("arbeitsort") or {}
                loc = " ".join(str(x) for x in
                               [ort.get("plz"), ort.get("ort"), ort.get("region")] if x)
                out.append(Job(
                    uid=f"aa:{refnr}",
                    source="Arbeitsagentur",
                    company=it.get("arbeitgeber") or "—",
                    title=it.get("titel") or it.get("beruf") or "—",
                    location=loc,
                    url=f"https://www.arbeitsagentur.de/jobsuche/jobdetail/{quote(refnr, safe='')}",
                    posted=it.get("aktuelleVeroeffentlichungsdatum")
                           or it.get("eintrittsdatum") or "",
                ))
            if len(items) < 100:
                break
            time.sleep(0.4)
    return out


# ----------------------------------------------------------------------------
# 来源 2:公司自己的 ATS 接口(比任何聚合平台都早)
# ----------------------------------------------------------------------------

def _get(url, **kw):
    kw.setdefault("timeout", 20)
    return session.get(url, **kw)


def ats_personio(slug, name):
    import xml.etree.ElementTree as ET
    r = _get(f"https://{slug}.jobs.personio.de/xml")
    r.raise_for_status()
    root = ET.fromstring(r.content)
    jobs = []
    for p in root.iter("position"):
        def t(tag):
            el = p.find(tag)
            return (el.text or "").strip() if el is not None and el.text else ""
        jid = t("id")
        if not jid:
            continue
        jobs.append(Job(
            uid=f"personio:{slug}:{jid}",
            source="Personio",
            company=name,
            title=t("name"),
            location=" ".join(x for x in [t("office"), t("department")] if x),
            url=f"https://{slug}.jobs.personio.de/job/{jid}",
            posted=t("createdAt"),
        ))
    return jobs


def ats_greenhouse(slug, name):
    r = _get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
    r.raise_for_status()
    return [Job(
        uid=f"gh:{slug}:{j['id']}",
        source="Greenhouse",
        company=name,
        title=j.get("title", ""),
        location=(j.get("location") or {}).get("name", ""),
        url=j.get("absolute_url", ""),
        posted=j.get("updated_at", ""),
    ) for j in r.json().get("jobs", [])]


def ats_lever(slug, name):
    r = _get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    r.raise_for_status()
    jobs = []
    for j in r.json():
        cat = j.get("categories") or {}
        ts = j.get("createdAt")
        jobs.append(Job(
            uid=f"lever:{slug}:{j.get('id')}",
            source="Lever",
            company=name,
            title=j.get("text", ""),
            location=cat.get("location", "") or "",
            url=j.get("hostedUrl", ""),
            posted=datetime.fromtimestamp(ts / 1000, timezone.utc).date().isoformat() if ts else "",
        ))
    return jobs


def ats_smartrecruiters(slug, name):
    jobs, offset = [], 0
    while offset < 400:
        r = _get(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings",
                 params={"limit": 100, "offset": offset})
        r.raise_for_status()
        data = r.json()
        items = data.get("content") or []
        for j in items:
            loc = j.get("location") or {}
            jobs.append(Job(
                uid=f"sr:{slug}:{j.get('id')}",
                source="SmartRecruiters",
                company=name,
                title=j.get("name", ""),
                location=" ".join(str(x) for x in [loc.get("city"), loc.get("country")] if x),
                url=f"https://jobs.smartrecruiters.com/{slug}/{j.get('id')}",
                posted=(j.get("releasedDate") or "")[:10],
            ))
        if len(items) < 100:
            break
        offset += 100
    return jobs


def ats_recruitee(slug, name):
    r = _get(f"https://{slug}.recruitee.com/api/offers/")
    r.raise_for_status()
    return [Job(
        uid=f"rc:{slug}:{j.get('id')}",
        source="Recruitee",
        company=name,
        title=j.get("title", ""),
        location=" ".join(str(x) for x in [j.get("city"), j.get("country")] if x),
        url=j.get("careers_url") or j.get("careers_apply_url", ""),
        posted=(j.get("published_at") or "")[:10],
    ) for j in r.json().get("offers", [])]


def ats_ashby(slug, name):
    r = _get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
    r.raise_for_status()
    return [Job(
        uid=f"ashby:{slug}:{j.get('id')}",
        source="Ashby",
        company=name,
        title=j.get("title", ""),
        location=j.get("location", "") or "",
        url=j.get("jobUrl", ""),
        posted=(j.get("publishedAt") or "")[:10],
    ) for j in r.json().get("jobs", [])]


def ats_workable(slug, name):
    r = _get(f"https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true")
    r.raise_for_status()
    return [Job(
        uid=f"wk:{slug}:{j.get('shortcode')}",
        source="Workable",
        company=name,
        title=j.get("title", ""),
        location=" ".join(str(x) for x in [j.get("city"), j.get("country")] if x),
        url=j.get("url") or j.get("application_url", ""),
        posted=(j.get("published_on") or "")[:10],
    ) for j in r.json().get("jobs", [])]


def ats_join(slug, name):
    r = _get(f"https://api.join.com/api/v1/companies/{slug}/jobs")
    r.raise_for_status()
    data = r.json()
    items = data if isinstance(data, list) else data.get("data") or data.get("jobs") or []
    return [Job(
        uid=f"join:{slug}:{j.get('id')}",
        source="JOIN",
        company=name,
        title=j.get("title", ""),
        location=str(j.get("location") or j.get("city") or ""),
        url=j.get("url", ""),
        posted=(str(j.get("publishedAt") or ""))[:10],
    ) for j in items]


def ats_workday(cfg_entry, name):
    """Workday 需要 POST,且每家公司的 tenant/site 不同。"""
    url = cfg_entry["url"]          # 例:https://x.wd3.myworkdayjobs.com/wday/cxs/x/Careers/jobs
    base = url.split("/wday/")[0]
    jobs, offset = [], 0
    while offset < 400:
        r = session.post(url, json={"appliedFacets": {}, "limit": 20,
                                    "offset": offset, "searchText": ""},
                         timeout=25)
        r.raise_for_status()
        data = r.json()
        items = data.get("jobPostings") or []
        for j in items:
            path = j.get("externalPath", "")
            jobs.append(Job(
                uid=f"wd:{name}:{path}",
                source="Workday",
                company=name,
                title=j.get("title", ""),
                location=j.get("locationsText", "") or "",
                url=base + path,
                posted=j.get("postedOn", ""),
            ))
        if len(items) < 20:
            break
        offset += 20
    return jobs


ATS_FETCHERS = {
    "personio": ats_personio,
    "greenhouse": ats_greenhouse,
    "lever": ats_lever,
    "smartrecruiters": ats_smartrecruiters,
    "recruitee": ats_recruitee,
    "ashby": ats_ashby,
    "workable": ats_workable,
    "join": ats_join,
}


def fetch_companies():
    conf = load_yaml(COMPANIES_PATH, default={"companies": []})
    out = []
    for c in conf.get("companies") or []:
        name = c.get("name") or c.get("slug", "?")
        ats = (c.get("ats") or "").lower()
        try:
            if ats == "workday":
                out += ats_workday(c, name)
            elif ats in ATS_FETCHERS:
                out += ATS_FETCHERS[ats](c["slug"], name)
            else:
                print(f"  [跳过] {name}: 未知 ats '{ats}'")
                continue
            print(f"  [OK] {name} ({ats})")
        except Exception as e:
            print(f"  [失败] {name} ({ats}): {type(e).__name__} {e}")
        time.sleep(0.3)
    return out


# ----------------------------------------------------------------------------
# ATS 自动探测:给公司名,猜它用的哪套系统
# ----------------------------------------------------------------------------

PROBES = [
    ("personio",       lambda s: f"https://{s}.jobs.personio.de/xml"),
    ("greenhouse",     lambda s: f"https://boards-api.greenhouse.io/v1/boards/{s}/jobs"),
    ("lever",          lambda s: f"https://api.lever.co/v0/postings/{s}?mode=json"),
    ("smartrecruiters", lambda s: f"https://api.smartrecruiters.com/v1/companies/{s}/postings?limit=1"),
    ("recruitee",      lambda s: f"https://{s}.recruitee.com/api/offers/"),
    ("ashby",          lambda s: f"https://api.ashbyhq.com/posting-api/job-board/{s}"),
    ("workable",       lambda s: f"https://apply.workable.com/api/v1/widget/accounts/{s}?details=true"),
]


def cmd_discover(slugs):
    print("探测中(slug 通常是公司名小写去空格,例:BMW Group -> bmwgroup)\n")
    found = []
    for slug in slugs:
        hits = []
        for ats, mk in PROBES:
            url = mk(slug)
            try:
                r = _get(url, timeout=10)
                if r.status_code != 200 or len(r.content) < 40:
                    continue
                # 粗略数一下有多少职位,避免把空壳页面当成命中
                n = len(re.findall(r'"id"\s*:|<position>', r.text))
                hits.append((ats, n))
            except Exception:
                pass
        if hits:
            for ats, n in hits:
                print(f"  ✓ {slug:<24} {ats:<16} 约 {n} 个职位")
                found.append({"name": slug, "ats": ats, "slug": slug})
        else:
            print(f"  ✗ {slug:<24} 没探到 — 手动打开它的招聘页,看 URL 跳到哪个域名")
    if found:
        print("\n把下面这段贴进 companies.yaml 的 companies: 下面(注意缩进):\n")
        print(yaml.safe_dump(found, allow_unicode=True, sort_keys=False))


# ----------------------------------------------------------------------------
# 输出
# ----------------------------------------------------------------------------

CSS = """
:root{--bg:#faf9f7;--card:#fff;--tx:#1a1a18;--mut:#6b6862;--line:#e6e3dd;--acc:#b8562f}
*{box-sizing:border-box}
body{margin:0;padding:32px 20px;background:var(--bg);color:var(--tx);
     font:15px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",sans-serif}
.wrap{max-width:860px;margin:0 auto}
h1{font-size:23px;margin:0 0 4px;letter-spacing:-.01em}
.sub{color:var(--mut);font-size:13px;margin-bottom:26px}
.grp{font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--mut);
     margin:28px 0 10px;padding-bottom:6px;border-bottom:1px solid var(--line)}
.j{background:var(--card);border:1px solid var(--line);border-radius:9px;
   padding:13px 15px;margin-bottom:8px}
.j a{color:var(--tx);text-decoration:none;font-weight:600}
.j a:hover{color:var(--acc)}
.meta{color:var(--mut);font-size:12.5px;margin-top:4px}
.tag{display:inline-block;background:#f0ede7;border-radius:4px;padding:1px 6px;
     font-size:11px;color:var(--mut);margin-left:6px}
.tag.igm{background:#e8f0e4;color:#3d6b2e;font-weight:600;cursor:help}
.empty{color:var(--mut);padding:40px 0;text-align:center}
"""


def _job_card(j):
    posted = f'<span class=tag>来源标注 {html.escape(j.posted[:10])}</span>' if j.posted else ""
    igm = ""
    if j.extra.get("igm"):
        igm = (f'<span class="tag igm" title="名单上写作:'
               f'{html.escape(j.extra["igm"])}({html.escape(j.extra.get("igm_how", ""))})">'
               f'IG Metall</span>')
    return (f'<div class=j><a href="{html.escape(j.url)}" target=_blank rel=noopener>'
            f'{html.escape(j.title)}</a>{igm}{posted}'
            f'<div class=meta>{html.escape(j.company)} · '
            f'{html.escape(j.source)} · '
            f'{html.escape(j.location) or "地点未标注"}</div></div>')


def render_html(day_groups, new_today, total_seen, first_run, cfg):
    """day_groups: [(日期, [Job,...]), ...] 最近 7 天,新的在前。"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    today = datetime.now(timezone.utc).date().isoformat()
    yday = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
    n_total_recent = sum(len(js) for _, js in day_groups)

    parts = [f"<!doctype html><meta charset=utf-8>",
             '<meta name=viewport content="width=device-width,initial-scale=1">',
             f"<title>慕尼黑新职位</title><style>{CSS}</style><div class=wrap>",
             "<h1>慕尼黑 · IG Metall 新职位</h1>",
             f"<div class=sub>更新于 {ts} UTC · 本次新增 <b>{new_today}</b> 条 · "
             f"近 7 天 {n_total_recent} 条 · 库中累计 {total_seen} 条</div>"]

    if first_run:
        parts.append("<div class=empty>基线已建立(收录了当前全部在线职位)。<br>"
                     "从下一次运行起,这里只显示真正新发布的职位。</div>")
    elif not day_groups:
        parts.append("<div class=empty>近 7 天没有新职位。<br>"
                     "连续多天为 0 的话,检查关键词是否太窄、白名单是否过严。</div>")
    else:
        for day, js in day_groups:
            label = "今天" if day == today else ("昨天" if day == yday else day)
            parts.append(f"<div class=grp>{label} · {len(js)} 条</div>")
            for j in js:
                parts.append(_job_card(j))

    parts.append("</div>")
    doc = "".join(parts)
    OUT_HTML.write_text(doc, encoding="utf-8")
    DOCS_HTML.parent.mkdir(exist_ok=True)
    DOCS_HTML.write_text(doc, encoding="utf-8")
    (DOCS_HTML.parent / ".nojekyll").touch()


def push_telegram(new_jobs, cfg):
    tg = cfg.get("telegram", {})
    # GitHub Actions 的 Secrets 通过环境变量进来,优先于 config
    token = os.environ.get("TELEGRAM_BOT_TOKEN") or tg.get("bot_token")
    chat = os.environ.get("TELEGRAM_CHAT_ID") or tg.get("chat_id")
    env_enabled = bool(os.environ.get("TELEGRAM_BOT_TOKEN"))
    if not (tg.get("enabled") or env_enabled) or not new_jobs:
        return
    if not token or not chat:
        print("  [Telegram] 缺 bot_token 或 chat_id,跳过")
        return
    lines = [f"<b>慕尼黑新职位 {len(new_jobs)} 条</b>"]
    for j in new_jobs[:30]:
        lines.append(f'· <a href="{html.escape(j.url)}">{html.escape(j.title)}</a> — '
                     f'{html.escape(j.company)}')
    if len(new_jobs) > 30:
        lines.append(f"…另有 {len(new_jobs)-30} 条,见 digest.html")
    try:
        requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                      json={"chat_id": chat, "text": "\n".join(lines),
                            "parse_mode": "HTML",
                            "disable_web_page_preview": True}, timeout=20)
    except Exception as e:
        print(f"  [Telegram] 推送失败: {e}")


# ----------------------------------------------------------------------------
# 主流程
# ----------------------------------------------------------------------------

def cmd_run(cfg):
    print("抓取联邦劳动局…")
    raw = fetch_arbeitsagentur(cfg)
    print(f"  拿到 {len(raw)} 条")

    print("抓取公司 ATS…")
    company_jobs = fetch_companies()
    print(f"  拿到 {len(company_jobs)} 条")
    raw += company_jobs

    kept = [j for j in raw
            if matches_keywords(j, cfg["keywords"]) and matches_location(j, cfg["location"])]
    print(f"\n过滤后 {len(kept)} / {len(raw)} 条符合关键词+地点")

    matcher = load_matcher(cfg)
    if matcher:
        strict = cfg["employers"].get("mode", "strict") == "strict"
        matched = []
        for j in kept:
            hit = matcher.match(j.company)
            if hit:
                j.extra["igm"] = hit[0]
                j.extra["igm_how"] = hit[1]
                matched.append(j)
            elif not strict:
                matched.append(j)
        n_igm = sum(1 for j in matched if j.extra.get("igm"))
        print(f"IG Metall 雇主命中 {n_igm} 条"
              + (f",非白名单已排除 {len(kept)-len(matched)} 条" if strict else "(宽松模式,其余保留)"))
        kept = matched

    conn = db_connect()
    first = is_first_run(conn)
    new = split_new(conn, kept)
    total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]

    if first:
        mark_seeded(conn)
        print(f"\n首次运行:已把现有 {len(new)} 条收作基线,不算新职位。")
        print("从下一次运行起,只会显示真正新增的。")
        render_html([], 0, total, True, cfg)
    else:
        print(f"\n★ 新职位 {len(new)} 条")
        for j in new[:15]:
            print(f"  · {j.title[:60]} — {j.company[:30]}")
        if len(new) > 15:
            print(f"  …另有 {len(new)-15} 条")
        render_html(recent_days(conn), len(new), total, False, cfg)
        push_telegram(new, cfg)

    conn.close()
    print(f"\n报告已生成: {OUT_HTML}")
    if cfg.get("open_browser") and not IN_CI and (first or new):
        try:
            webbrowser.open(OUT_HTML.as_uri())
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser(description="慕尼黑职位每日差分监控")
    sub = ap.add_subparsers(dest="cmd")
    sub.add_parser("run", help="抓取并生成今日报告")
    d = sub.add_parser("discover", help="探测公司用的哪套 ATS")
    d.add_argument("slugs", nargs="+")
    sub.add_parser("stats")
    sub.add_parser("reset")
    args = ap.parse_args()

    if args.cmd == "discover":
        cmd_discover(args.slugs)
    elif args.cmd == "stats":
        conn = db_connect()
        n = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        print(f"数据库共 {n} 条职位")
        for r in conn.execute("SELECT source, COUNT(*) FROM jobs GROUP BY source ORDER BY 2 DESC"):
            print(f"  {r[0]:<20} {r[1]}")
    elif args.cmd == "reset":
        if DB_PATH.exists():
            DB_PATH.unlink()
        print("数据库已清空,下次 run 会重新建立基线。")
    else:
        cmd_run(load_config())


if __name__ == "__main__":
    main()
