#!/usr/bin/env python3
"""
批量探测:对 IG Metall 名单里慕尼黑周边的公司,逐一试探它们用的招聘系统。
探到的直接合并进 companies.yaml。设计为在 GitHub Actions 里手动触发。
"""
import math, re, time, sys
import yaml
from pathlib import Path
from jobwatch import PROBES, _get
from names import slug_candidates

BASE = Path(__file__).resolve().parent
MUC = (48.137, 11.575)
RADIUS_KM = 80
MAX_COMPANIES = 350

def dist_km(lat, lon):
    dy = (lat - MUC[0]) * 111.0
    dx = (lon - MUC[1]) * 111.0 * math.cos(math.radians(MUC[0]))
    return math.hypot(dx, dy)

igm = yaml.safe_load((BASE / "igmetall.yaml").read_text(encoding="utf-8")) or {}
emps = igm.get("employers") or []
targets = []
for e in emps:
    lat, lon = e.get("lat"), e.get("lon")
    near = (isinstance(lat, (int, float)) and dist_km(lat, lon) <= RADIUS_KM)
    bayern = "bayern" in str(e.get("region", "")).lower()
    hay = f"{e.get('ort','')}".lower()
    muc_word = "münchen" in hay or "munich" in hay
    if near or muc_word:
        targets.append(e)
# 名单站不覆盖慕尼黑,这里补一份慕尼黑周边金属电气大厂(多为 Tarif 企业,
# 但 Tarifbindung 未逐一核实),让探测器找它们的直连接口:
CURATED = [
    "Knorr-Bremse", "KraussMaffei", "Webasto", "Brainlab", "Kuka",
    "Renk", "MTU Aero Engines", "Premium Aerotec", "Linde", "ams OSRAM",
    "Rohde Schwarz", "Wacker Neuson", "Zeppelin", "HAWE Hydraulik", "ARRI",
    "Giesecke Devrient", "Baader", "Multivac", "Grob Werke", "Fendt",
    "Agile Robots", "Isar Aerospace", "Konux", "Proglove", "Tado",
    "Magirus", "Deckel Maho", "Zollner", "Rohde", "Siltronic",
]
for n in CURATED:
    targets.append({"name": n})
targets = targets[:MAX_COMPANIES]
print(f"名单共 {len(emps)} 家;慕尼黑 {RADIUS_KM}km 内/巴伐利亚待探测 {len(targets)} 家\n")

existing = yaml.safe_load((BASE / "companies.yaml").read_text(encoding="utf-8")) or {}
comp = existing.get("companies") or []
known = {(c.get("ats"), c.get("slug")) for c in comp}

found = 0
for idx, e in enumerate(targets, 1):
    name = e["name"]
    hit = None
    for slug in slug_candidates(name)[:3]:
        for ats, mk in PROBES:
            try:
                r = _get(mk(slug), timeout=8)
                if r.status_code != 200 or len(r.content) < 40:
                    continue
                n = len(re.findall(r'"id"\s*:|<position>', r.text))
                if n == 0:
                    continue
                hit = (ats, slug, n)
                break
            except Exception:
                continue
            finally:
                time.sleep(0.12)
        if hit:
            break
    if hit:
        ats, slug, n = hit
        if (ats, slug) not in known:
            comp.append({"name": name, "ats": ats, "slug": slug})
            known.add((ats, slug))
            found += 1
        print(f"[{idx}/{len(targets)}] ✓ {name[:44]:<46} {ats:<15} ~{n} 职位")
    else:
        print(f"[{idx}/{len(targets)}] · {name[:44]}")

out = {"companies": comp}
(BASE / "companies.yaml").write_text(
    "# 由 discover_all.py 自动生成/合并。手工加 Workday 公司也写在这里,格式见文件末注释。\n"
    + yaml.safe_dump(out, allow_unicode=True, sort_keys=False)
    + "\n# Workday 格式: {name: 公司, ats: workday, url: https://x.wdN.myworkdayjobs.com/wday/cxs/x/SITE/jobs}\n",
    encoding="utf-8")
print(f"\n新增 {found} 家,companies.yaml 现共 {len(comp)} 家")
