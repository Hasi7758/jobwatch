#!/usr/bin/env python3
"""
对白名单里慕尼黑周边的公司,逐一"打开它的招聘官网"识别招聘系统。
两条腿:(A) 猜域名抓招聘页,从 HTML 里认 ATS  (B) 猜 slug 直连 14 套系统 API
命中的写进 companies.yaml。
"""
import math, re, sys, time
import requests, yaml
from pathlib import Path
from names import slug_candidates, tokens

BASE = Path(__file__).resolve().parent
MUC = (48.137, 11.575)
RADIUS_KM = 60
S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
                  "Accept-Language": "de-DE,de;q=0.9,en;q=0.8"})

# HTML 里出现这些域名 = 用的这套系统
SIG = [
    ("personio",        r"([a-z0-9-]+)\.jobs\.personio\.(?:de|com)"),
    ("softgarden",      r"([a-z0-9-]+)\.softgarden\.io"),
    ("greenhouse",      r"boards\.greenhouse\.io/([a-z0-9]+)"),
    ("smartrecruiters", r"jobs\.smartrecruiters\.com/([A-Za-z0-9]+)"),
    ("lever",           r"jobs\.lever\.co/([a-z0-9-]+)"),
    ("ashby",           r"jobs\.ashbyhq\.com/([a-z0-9-]+)"),
    ("recruitee",       r"([a-z0-9-]+)\.recruitee\.com"),
    ("workable",        r"apply\.workable\.com/([a-z0-9-]+)"),
    ("join",            r"join\.com/companies/([a-z0-9-]+)"),
    ("teamtailor",      r"([a-z0-9-]+)\.teamtailor\.com"),
    ("dvinci",          r"([a-z0-9-]+)\.dvinci(?:hr)?\.(?:com|de)"),
    ("rexx",            r"([a-z0-9-]+)\.rexx-systems\.com"),
    ("concludis",       r"([a-z0-9-]+)\.concludis\.de"),
    ("successfactors",  r"([a-z0-9-]+)\.(?:jobs\.)?(?:successfactors|sapsf)\.(?:com|eu)"),
    ("workday",         r"([a-z0-9-]+)\.(wd\d)\.myworkdayjobs\.com/(?:[a-z-]{2,5}/)?([^/\"'?#]+)"),
]

# slug 直连 API
API = [
    ("personio",        lambda s: f"https://{s}.jobs.personio.de/xml"),
    ("softgarden",      lambda s: f"https://{s}.softgarden.io/api/rest/frontend/v3/job-postings?limit=5"),
    ("greenhouse",      lambda s: f"https://boards-api.greenhouse.io/v1/boards/{s}/jobs"),
    ("smartrecruiters", lambda s: f"https://api.smartrecruiters.com/v1/companies/{s}/postings?limit=5"),
    ("lever",           lambda s: f"https://api.lever.co/v0/postings/{s}?mode=json"),
    ("ashby",           lambda s: f"https://api.ashbyhq.com/posting-api/job-board/{s}"),
    ("recruitee",       lambda s: f"https://{s}.recruitee.com/api/offers/"),
    ("workable",        lambda s: f"https://apply.workable.com/api/v1/widget/accounts/{s}?details=true"),
    ("join",            lambda s: f"https://api.join.com/api/v1/companies/{s}/jobs"),
]

PATHS = ["/karriere", "/de/karriere", "/karriere/stellenangebote", "/jobs",
         "/karriere/jobs", "/unternehmen/karriere", "/careers", "/de/jobs", "/"]


def dist(lat, lon):
    dy = (lat - MUC[0]) * 111.0
    dx = (lon - MUC[1]) * 111.0 * math.cos(math.radians(MUC[0]))
    return math.hypot(dx, dy)


def domain_candidates(name):
    ts = tokens(name)
    if not ts:
        return []
    out = []
    for stem in ["".join(ts[:2]), ts[0], "-".join(ts[:2])]:
        if len(stem) < 3:
            continue
        for tld in (".de", ".com"):
            d = stem + tld
            if d not in out:
                out.append(d)
    return out[:4]


def probe_web(name):
    """打开公司官网的招聘页,认它用的什么系统。"""
    for dom in domain_candidates(name):
        for host in (f"https://www.{dom}", f"https://{dom}"):
            for path in PATHS:
                try:
                    r = S.get(host + path, timeout=10, allow_redirects=True)
                except Exception:
                    continue
                if r.status_code != 200 or len(r.text) < 500:
                    continue
                blob = r.text + " " + r.url
                for ats, pat in SIG:
                    m = re.search(pat, blob, re.I)
                    if m:
                        return ats, m.groups(), r.url
                break   # 该 host 通了但没认出来,换下一个域名
    return None


def probe_api(name):
    for slug in slug_candidates(name)[:3]:
        for ats, mk in API:
            try:
                r = S.get(mk(slug), timeout=8)
            except Exception:
                continue
            if r.status_code != 200 or len(r.content) < 60:
                continue
            n = len(re.findall(r'"id"\s*:|<position>', r.text))
            if n:
                return ats, slug, n
    return None


igm = yaml.safe_load((BASE / "igmetall.yaml").read_text(encoding="utf-8"))["employers"]
targets = [e for e in igm if "lat" in e and dist(e["lat"], e["lon"]) <= RADIUS_KM]
print(f"慕尼黑 {RADIUS_KM}km 内 IG Metall 企业: {len(targets)} 家\n", flush=True)

conf = yaml.safe_load((BASE / "companies.yaml").read_text(encoding="utf-8")) or {}
comp = conf.get("companies") or []
have = {(c.get("ats"), c.get("slug") or c.get("url")) for c in comp}

added = 0
for i, e in enumerate(targets, 1):
    name = e["name"]
    entry = None
    w = probe_web(name)
    if w:
        ats, groups, src = w
        if ats == "workday" and len(groups) >= 3:
            tn, wd, site = groups[0], groups[1], groups[2]
            entry = {"name": name, "ats": "workday",
                     "url": f"https://{tn}.{wd}.myworkdayjobs.com/wday/cxs/{tn}/{site}/jobs",
                     "search": "München"}
        elif ats == "successfactors":
            entry = None   # 需要门户地址,自动拼不可靠,跳过
        elif ats in ("personio", "softgarden", "greenhouse", "smartrecruiters",
                     "lever", "ashby", "recruitee", "workable", "join"):
            entry = {"name": name, "ats": ats, "slug": groups[0]}
        if entry:
            print(f"[{i}/{len(targets)}] ✓web {name[:40]:<42} {ats:<16} {groups[0]}", flush=True)
    if not entry:
        a = probe_api(name)
        if a:
            ats, slug, n = a
            entry = {"name": name, "ats": ats, "slug": slug}
            print(f"[{i}/{len(targets)}] ✓api {name[:40]:<42} {ats:<16} {slug} (~{n})", flush=True)
    if entry:
        key = (entry.get("ats"), entry.get("slug") or entry.get("url"))
        if key not in have:
            have.add(key); comp.append(entry); added += 1
    else:
        print(f"[{i}/{len(targets)}] ·    {name[:40]}", flush=True)

(BASE / "companies.yaml").write_text(
    "# 由 discover_web.py / discover_all.py 生成\n"
    + yaml.safe_dump({"companies": comp}, allow_unicode=True, sort_keys=False)
    + "\n# Workday: {name:, ats: workday, url: .../wday/cxs/T/SITE/jobs, search: München}\n",
    encoding="utf-8")
print(f"\n新增 {added} 家,共 {len(comp)} 家")
