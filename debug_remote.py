#!/usr/bin/env python3
"""验证 Workday / SuccessFactors 接口能否直接取到职位列表。"""
import json, re, requests
S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 Chrome/124.0", "Content-Type": "application/json",
                  "Accept": "application/json"})

print("########## Workday CXS 接口 ##########")
WD = [
    ("Airbus",  "https://ag.wd3.myworkdayjobs.com/wday/cxs/ag/Airbus/jobs"),
    ("KION/Linde", "https://kiongroup.wd3.myworkdayjobs.com/wday/cxs/kiongroup/de-DE/jobs"),
    ("KION alt", "https://kiongroup.wd3.myworkdayjobs.com/wday/cxs/kiongroup/KIONGroup/jobs"),
]
for name, url in WD:
    try:
        r = S.post(url, json={"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "München"}, timeout=25)
        print(f"[{name}] HTTP {r.status_code}")
        if r.status_code == 200:
            d = r.json()
            posts = d.get("jobPostings", [])
            print(f"   总数={d.get('total')} 本页={len(posts)}")
            for p in posts[:4]:
                print(f"     · {p.get('title','')[:55]} | {p.get('locationsText','')[:30]} | {p.get('postedOn','')}")
        else:
            print("   ", r.text[:150])
    except Exception as e:
        print(f"[{name}] 异常 {type(e).__name__} {e}")

print()
print("########## Knorr-Bremse SuccessFactors ##########")
for url in ["https://careers.knorr-bremse.com/search/?q=&locationsearch=M%C3%BCnchen",
            "https://performancemanager5.successfactors.eu/xi/ats/jobrequisition/jobrequisitionsearch"]:
    try:
        r = S.get(url, timeout=25)
        print(f"{url[:60]} -> HTTP {r.status_code}, {len(r.text)} 字节")
        if r.status_code == 200:
            jobs = re.findall(r'jobTitle-link[^>]*>([^<]{4,80})<', r.text)
            print("   职位样例:", jobs[:5])
            print("   含 RSS:", "rss" in r.text.lower(), "| 含 /job/:", r.text.count("/job/"))
    except Exception as e:
        print("   异常", type(e).__name__)
