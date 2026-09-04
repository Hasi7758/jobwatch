#!/usr/bin/env python3
import requests, json
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0","Accept":"application/json"})

print("### Phenom /api/jobs 全面探测 ###")
HOSTS=[("AMD","https://careers.amd.com"),("Keysight","https://careers.keysight.com"),
       ("Infineon","https://jobs.infineon.com"),("Lam Research","https://careers.lamresearch.com"),
       ("Seagate","https://seagatecareers.com"),("ST Engineering","https://careers.stengg.com"),
       ("Micron","https://careers.micron.com"),("Abbott","https://www.jobs.abbott"),
       ("Stryker","https://careers.stryker.com"),("Honeywell","https://careers.honeywell.com")]
for name, host in HOSTS:
    for path in ["/api/jobs", "/widgets/api/jobs"]:
        try:
            r=S.get(host+path, params={"location":"Singapore","limit":10,"page":1}, timeout=20)
            if r.status_code==200 and "json" in r.headers.get("content-type",""):
                d=r.json(); jobs=d.get("jobs") or []
                print(f"  ✓ {name:<16} {path:<18} 返回 {len(jobs)} 条 | totalCount={d.get('totalCount') or d.get('count')}")
                for j in jobs[:2]:
                    dd=j.get("data") or j
                    print(f"      · {str(dd.get('title'))[:48]:<50} loc={str(dd.get('city') or dd.get('location'))[:22]} date={dd.get('posted_date') or dd.get('create_date')}")
                if jobs:
                    print("      字段:", list((jobs[0].get('data') or jobs[0]).keys())[:18])
                break
        except Exception as e:
            pass
    else:
        print(f"  · {name}")

print("\n### 参数验证:Singapore 过滤是否生效 (AMD) ###")
for loc in ["Singapore", ""]:
    r=S.get("https://careers.amd.com/api/jobs", params={"location":loc,"limit":100,"page":1}, timeout=25)
    d=r.json(); jobs=d.get("jobs") or []
    sg=sum(1 for j in jobs if "singapore" in json.dumps(j).lower())
    print(f"  location={loc!r:<12} 返回{len(jobs)} 其中含Singapore {sg} | total={d.get('totalCount')}")
