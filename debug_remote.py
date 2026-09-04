#!/usr/bin/env python3
"""AMD 的 /api/jobs 能用,验证同款路径在其它 Phenom 站点的变体。"""
import requests
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0","Accept":"application/json",
                                        "Referer":"https://careers.amd.com/"})
HOSTS=["https://jobs.infineon.com","https://careers.lamresearch.com","https://seagatecareers.com",
       "https://careers.stengg.com","https://www.jobs.abbott","https://careers.stryker.com",
       "https://careers.honeywell.com","https://jobs.siemens.com","https://careers.micron.com",
       "https://jobs.bd.com","https://careers.tuvsud.com","https://jobs.siemens-healthineers.com",
       "https://careers.alcon.com","https://careers.jnj.com","https://www.safran-group.com"]
PARAMS=[{"location":"Singapore","limit":5,"page":1},
        {"location":"Singapore","num":5,"start":0},
        {"limit":5,"page":1}]
for h in HOSTS:
    hit=False
    for pp in PARAMS:
        try:
            r=S.get(h+"/api/jobs", params=pp, timeout=15)
            if r.status_code==200 and "json" in r.headers.get("content-type",""):
                d=r.json(); jobs=d.get("jobs") or []
                if jobs:
                    x=jobs[0].get("data") or jobs[0]
                    print(f"  ✓ {h:<46} params={list(pp)} count={d.get('totalCount') or d.get('count')}")
                    print(f"      · {str(x.get('title'))[:50]} | {x.get('city') or x.get('location_name')}")
                    hit=True; break
        except Exception: pass
    if not hit:
        try:
            r=S.get(h+"/api/jobs", params={"limit":1}, timeout=12)
            print(f"  · {h:<46} HTTP {r.status_code} {r.headers.get('content-type','')[:20]}")
        except Exception as e:
            print(f"  · {h:<46} {type(e).__name__}")
