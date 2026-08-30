#!/usr/bin/env python3
"""
从 IG Metall 雇主名单站导入公司列表。

因为那是个纯前端 SPA,数据几乎肯定是一个静态 JSON 文件。
本脚本会:
  1. 抓首页 HTML,找出所有 JS/JSON 资源
  2. 在 JS 里搜 .json 引用,顺藤摸瓜找到数据文件
  3. 也直接试一批常见路径
  4. 都失败就走手动模式(见下面的说明)

用法:
    python import_igm.py auto                      # 自动探测
    python import_igm.py file igm_raw.json         # 用手动保存的文件
    python import_igm.py file igm_raw.json --region bayern   # 只要巴伐利亚
    python import_igm.py show                      # 看看导入了什么

手动模式怎么拿文件:
    打开 https://arbeitgeberliste.netlify.app/
    F12 → Network 标签 → 刷新页面 → 按 Size 排序,最大的那个 .json 就是
    → 右键 → Copy → Copy response → 存成 igm_raw.json
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin

try:
    import requests
    import yaml
except ImportError:
    sys.exit("请先运行:  pip install requests pyyaml")

from names import slug_candidates

BASE = Path(__file__).resolve().parent
OUT = BASE / "igmetall.yaml"
SITE = "https://arbeitgeberliste.netlify.app/"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
S = requests.Session()
S.headers.update({"User-Agent": UA})

COMMON_PATHS = [
    "data.json", "companies.json", "arbeitgeber.json", "arbeitgeberliste.json",
    "db.json", "list.json", "firmen.json", "betriebe.json",
    "data/data.json", "data/companies.json", "assets/data.json",
    "static/data.json", "public/data.json",
]

# 可能装着公司名的字段名(德/英)
NAME_KEYS = ["name", "firma", "firmenname", "unternehmen", "arbeitgeber",
             "betrieb", "company", "title", "bezeichnung"]
PLACE_KEYS = ["ort", "stadt", "city", "standort", "sitz", "adresse", "address",
              "plz", "postleitzahl", "zip"]
REGION_KEYS = ["bundesland", "region", "bezirk", "land", "state", "gebiet",
               "tarifgebiet", "tarifbezirk"]



# ---------------------------------------------------------------- HTML 表格解析
# 该站的数据不是 JSON,是直接写在首页里的一张 <table>(tablefilter.js 筛选)。
# 列:Bundesland | Kreis | Stadt/Gemeinde | Unternehmen | Links | ... | Ort (Werk) | Lat | Lon

import html as _html

def _strip_tags(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    s = _html.unescape(s).replace("\u00ad", "")   # 软连字符
    return re.sub(r"\s+", " ", s).strip()


def parse_html_table(page):
    thead = re.search(r"<thead.*?</thead>", page, re.S)
    if not thead:
        return None
    headers = [_strip_tags(h).lower()
               for h in re.findall(r"<th[^>]*>(.*?)</th>", thead.group(0), re.S)]

    def col(*needles):
        for i, h in enumerate(headers):
            if any(n == h for n in needles):
                return i
        for i, h in enumerate(headers):
            if any(n in h for n in needles):
                return i
        return None

    i_name = col("unternehmen", "firma", "company")
    i_land = col("bundesland")
    i_stadt = col("stadt / gemeinde", "stadt", "gemeinde")
    i_werk = col("ort (werk)", "werk")
    i_lat, i_lon = col("lat"), col("lon")
    if i_name is None:
        return None

    out = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if len(tds) <= i_name:
            continue

        def cell(i):
            return _strip_tags(tds[i]) if i is not None and i < len(tds) else ""

        name = cell(i_name)
        if not name:
            continue
        e = {"name": name}
        ort = " ".join(x for x in [cell(i_stadt), cell(i_werk)] if x)
        if ort:
            e["ort"] = ort
        if cell(i_land):
            e["region"] = cell(i_land)
        try:
            e["lat"], e["lon"] = float(cell(i_lat)), float(cell(i_lon))
        except (ValueError, TypeError):
            pass
        out.append(e)
    return out if len(out) >= 20 else None



# ---------------------------------------------------------------- 交互地图解析
# 地图页把 4700+ 个点内嵌在一个 5MB 的 OpenLayers 脚本里,四个图层:
#   vectorLayer  = IG Metall: Flächentarif oder Haustarif   <- 我们要的
#   vectorLayer2/3/4 = IG BCE 各类
MAP_URL = ("https://arbeitgeberliste.netlify.app/interaktive-karte/"
           "unternehmen-mit-ig-metall-flaechentarif-oder-haustarif-sowie-ig-bce")
MUC_LATLON = (48.137, 11.575)

_FEAT = re.compile(
    r"Geometry\.Point\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)"
    r".{0,120}?\{\s*description:\s*`(.*?)`\s*\}\s*\)\s*;?\s*"
    r"(vectorLayer\d*)\.addFeatures", re.S)

_LAYER = {"vectorLayer": "IG Metall", "vectorLayer2": "IG BCE Flächentarif",
          "vectorLayer3": "IG BCE Haustarif", "vectorLayer4": "IG BCE kein Tarif"}


def _dist_muc(lat, lon):
    import math
    dy = (lat - MUC_LATLON[0]) * 111.0
    dx = (lon - MUC_LATLON[1]) * 111.0 * math.cos(math.radians(MUC_LATLON[0]))
    return math.hypot(dx, dy)


def parse_map(only_ig_metall=True):
    print(f"抓取交互地图 {MAP_URL[:60]}…")
    page = S.get(MAP_URL, timeout=90).text
    m = max(re.finditer(r"<script(?![^>]*src)[^>]*>(.*?)</script>", page, re.S),
            key=lambda x: len(x.group(1)), default=None)
    if not m:
        return None
    js = m.group(1)
    best = {}   # 归一名 -> entry(取离慕尼黑最近的厂区坐标)
    n_raw = 0
    for lon, lat, desc, layer in _FEAT.findall(js):
        cat = _LAYER.get(layer, layer)
        if only_ig_metall and cat != "IG Metall":
            continue
        nm = re.search(r">([^<]{2,140})</a>", _html.unescape(desc))
        if not nm:
            continue
        name = re.sub(r"\s+", " ", nm.group(1)).strip()
        lat, lon = float(lat), float(lon)
        n_raw += 1
        k = name.lower()
        e = {"name": name, "tarif": cat, "lat": lat, "lon": lon}
        if k not in best or _dist_muc(lat, lon) < _dist_muc(best[k]["lat"], best[k]["lon"]):
            best[k] = e
    out = list(best.values())
    if not out:
        return None
    near = sum(1 for e in out if _dist_muc(e["lat"], e["lon"]) <= 80)
    print(f"  ✓ 地图解析成功: 点位 {n_raw} 个, 去重后 {len(out)} 家 IG Metall 公司,"
          f" 慕尼黑 80km 内 {near} 家")
    return out


# ---------------------------------------------------------------- 自动探测

def try_json(url):
    try:
        r = S.get(url, timeout=20)
        if r.status_code != 200:
            return None
        ct = r.headers.get("content-type", "")
        if "json" not in ct and not r.text.lstrip().startswith(("[", "{")):
            return None
        return r.json()
    except Exception:
        return None


def auto_discover():
    try:
        mp = parse_map()
        if mp:
            return mp
    except Exception as e:
        print(f"  地图解析异常: {type(e).__name__} {e}, 退回表格")

    print(f"抓取 {SITE}")
    try:
        html = S.get(SITE, timeout=20).text
    except Exception as e:
        sys.exit(f"抓不到首页: {e}\n改用手动模式,见文件顶部说明。")
    tbl = parse_html_table(html)
    if tbl:
        print(f"  ✓ 首页 HTML 表格解析成功: {len(tbl)} 家公司")
        return tbl

    # 直接在 HTML 里出现的 .json
    urls = []
    for m in re.findall(r'["\'\(]([^"\'\)\s]+\.json)["\'\)]', html):
        urls.append(urljoin(SITE, m))

    # 从 JS bundle 里挖
    scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html)
    for s in scripts[:8]:
        js_url = urljoin(SITE, s)
        try:
            js = S.get(js_url, timeout=25).text
        except Exception:
            continue
        for m in re.findall(r'["\'\(]([^"\'\)\s]{3,120}\.json)["\'\)]', js):
            urls.append(urljoin(js_url, m))
            urls.append(urljoin(SITE, m.lstrip("./")))

    urls += [urljoin(SITE, p) for p in COMMON_PATHS]

    seen, best, best_n = set(), None, 0
    for u in urls:
        if u in seen:
            continue
        seen.add(u)
        data = try_json(u)
        if data is None:
            continue
        recs = find_records(data)
        if recs and len(recs) > best_n:
            best, best_n = (u, data, recs), len(recs)
            print(f"  ✓ {u}  →  {len(recs)} 条记录")
        else:
            print(f"  · {u}  (不像数据文件)")

    if not best:
        print("\n自动探测失败。请走手动模式:")
        print("  F12 → Network → 刷新 → 找最大的 .json → Copy response")
        print("  存成 igm_raw.json,然后:  python import_igm.py file igm_raw.json")
        sys.exit(1)

    url, data, recs = best
    print(f"\n采用 {url}({len(recs)} 条)")
    return recs


# ---------------------------------------------------------------- 解析

def find_records(data, depth=0):
    """在任意嵌套结构里找出"看起来像公司列表"的那个数组。"""
    if depth > 5:
        return None
    if isinstance(data, list):
        if len(data) >= 5 and all(isinstance(x, dict) for x in data[:5]):
            keys = {k.lower() for k in data[0]}
            if any(nk in keys for nk in NAME_KEYS):
                return data
        if len(data) >= 5 and all(isinstance(x, str) for x in data[:5]):
            return [{"name": x} for x in data]
        return None
    if isinstance(data, dict):
        best = None
        for v in data.values():
            r = find_records(v, depth + 1)
            if r and (best is None or len(r) > len(best)):
                best = r
        return best
    return None


def pick_key(records, candidates):
    """在记录里挑一个最可能的字段名。"""
    keys = Counter()
    for r in records[:200]:
        for k in r:
            keys[k.lower()] += 1
    for c in candidates:
        for k in keys:
            if k == c:
                return k
    for c in candidates:
        for k in keys:
            if c in k:
                return k
    return None


def apply_region(entries, region_filter):
    if not region_filter:
        return entries
    keep = [e for e in entries
            if region_filter.lower() in f"{e.get('ort','')} {e.get('region','')}".lower()]
    print(f"地区过滤 '{region_filter}': 保留 {len(keep)} / {len(entries)}")
    return keep


def extract(records, region_filter=None):
    if not records:
        sys.exit("没解析出记录。")

    # 统一小写键,方便取值
    recs = [{str(k).lower(): v for k, v in r.items()} for r in records]

    nk = pick_key(recs, NAME_KEYS)
    pk = pick_key(recs, PLACE_KEYS)
    rk = pick_key(recs, REGION_KEYS)
    print(f"字段识别:  公司名={nk}   地点={pk}   地区={rk}")
    if not nk:
        print("\n没找到公司名字段。记录长这样:")
        print(json.dumps(records[0], ensure_ascii=False, indent=2)[:600])
        sys.exit("请手动把正确字段名加到 import_igm.py 顶部的 NAME_KEYS 里。")

    out, skipped = [], 0
    for r in recs:
        name = r.get(nk)
        if not name or not str(name).strip():
            continue
        name = str(name).strip()
        place = str(r.get(pk) or "").strip() if pk else ""
        region = str(r.get(rk) or "").strip() if rk else ""

        if region_filter:
            hay = f"{place} {region}".lower()
            if region_filter.lower() not in hay:
                skipped += 1
                continue

        e = {"name": name}
        if place:
            e["ort"] = place
        if region:
            e["region"] = region
        out.append(e)

    # 去重
    seen, uniq = set(), []
    for e in out:
        k = e["name"].lower()
        if k not in seen:
            seen.add(k)
            uniq.append(e)

    if region_filter:
        print(f"地区过滤 '{region_filter}':保留 {len(uniq)},排除 {skipped}")
    return uniq


def save(entries):
    OUT.write_text(
        "# 由 import_igm.py 生成 —— IG Metall 雇主白名单\n"
        "# jobwatch.py 会用它过滤职位:只保留这些公司发布的岗位\n\n"
        + yaml.safe_dump({"employers": entries}, allow_unicode=True,
                         sort_keys=False, width=200),
        encoding="utf-8")
    print(f"\n已写入 {OUT}  ({len(entries)} 家公司)")

    munich = [e for e in entries
              if ("lat" in e and _dist_muc(e["lat"], e["lon"]) <= 80)
              or "münch" in f"{e.get('ort','')}".lower()
              or "munich" in f"{e.get('ort','')}".lower()]
    if munich:
        print(f"其中地点含慕尼黑的:{len(munich)} 家")

    print("\n接下来可以拿这些去探测 ATS(一次 8 个左右):")
    pool = munich or entries
    cands = []
    for e in pool[:8]:
        cands += slug_candidates(e["name"])[:2]
    print("  python jobwatch.py discover " + " ".join(cands[:16]))


# ---------------------------------------------------------------- CLI

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd")

    a = sub.add_parser("auto", help="自动探测站点的数据文件")
    a.add_argument("--region", help="只保留地点/地区含此关键词的,例:bayern")

    f = sub.add_parser("file", help="解析手动保存的 json")
    f.add_argument("path")
    f.add_argument("--region")

    sub.add_parser("show", help="看已导入的内容")
    args = ap.parse_args()

    if args.cmd == "auto":
        recs = auto_discover()
        if recs and isinstance(recs[0], dict) and "name" in recs[0] and "lat" in str(recs[0].keys()) + "lat":
            pass
        if recs and all("name" in r for r in recs[:5]):
            save(apply_region(recs, args.region))
        else:
            save(extract(recs, args.region))

    elif args.cmd == "file":
        p = Path(args.path)
        if not p.exists():
            sys.exit(f"找不到 {p}")
        txt = p.read_text(encoding="utf-8")
        if txt.lstrip().startswith("<"):
            tbl = parse_html_table(txt)
            if tbl:
                print(f"HTML 表格: {len(tbl)} 家公司")
                save(apply_region(tbl, args.region)); return
        raw = json.loads(txt)
        recs = find_records(raw)
        if not recs:
            print("自动定位数组失败,顶层结构:")
            print(json.dumps(raw, ensure_ascii=False)[:800])
            sys.exit("把这段贴给我,我帮你改解析逻辑。")
        print(f"找到 {len(recs)} 条记录")
        save(extract(recs, args.region))

    elif args.cmd == "show":
        if not OUT.exists():
            sys.exit("还没导入。先跑 python import_igm.py auto")
        d = yaml.safe_load(OUT.read_text(encoding="utf-8"))
        emps = d.get("employers", [])
        print(f"{len(emps)} 家公司,前 20 家:")
        for e in emps[:20]:
            print(f"  {e['name']:<50} {e.get('ort','')}")

    else:
        ap.print_help()


if __name__ == "__main__":
    main()
