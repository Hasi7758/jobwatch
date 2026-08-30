#!/usr/bin/env python3
import re, requests
S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"})

print("##### 1. 名单站表格结构 #####")
h = S.get("https://arbeitgeberliste.netlify.app/", timeout=30).text
print("总长:", len(h), "| table数:", h.count("<table"), "| tr数:", h.count("<tr"))
m = re.search(r'<thead.*?</thead>', h, re.S)
print("THEAD:", (m.group(0)[:800].replace("\n"," ") if m else "无 thead"))
rows = re.findall(r'<tr[^>]*>.*?</tr>', h, re.S)
print(f"共 {len(rows)} 行,第2~4行原文:")
for r in rows[1:4]:
    print("  ", r[:500].replace("\n", " "))

print()
print("##### 2. 替代职位源测试 #####")
try:
    r = S.get("https://www.arbeitnow.com/api/job-board-api", timeout=20)
    print("arbeitnow HTTP", r.status_code)
    if r.status_code == 200:
        d = r.json(); jobs = d.get("data", [])
        print("  字段:", list(jobs[0].keys()) if jobs else "空")
        muc = [j for j in jobs if "münchen" in str(j.get("location","")).lower() or "munich" in str(j.get("location","")).lower()]
        print(f"  本页 {len(jobs)} 条, 慕尼黑 {len(muc)} 条, 样例:", (muc or jobs)[0].get("title","")[:60])
except Exception as e:
    print("arbeitnow 异常:", e)

for name, url in [("AA www域", "https://www.arbeitsagentur.de/jobsuche/"),
                  ("AA rest 根", "https://rest.arbeitsagentur.de/")]:
    try:
        r = S.get(url, timeout=15)
        print(f"{name}: HTTP {r.status_code}, {len(r.text)} 字节")
    except Exception as e:
        print(f"{name}: 异常 {type(e).__name__}")
