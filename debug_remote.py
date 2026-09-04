#!/usr/bin/env python3
import requests, json
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0","Accept":"application/json"})

TARGETS=[("Infineon","https://jobs.infineon.com","infineon.com"),
         ("Lam Research","https://careers.lamresearch.com","lamresearch.com"),
         ("Seagate","https://seagatecareers.com","seagate.com"),
         ("ST Engineering","https://careers.stengg.com","stengg.com"),
         ("Abbott","https://www.jobs.abbott","abbott.com"),
         ("Stryker","https://careers.stryker.com","stryker.com"),
         ("Honeywell","https://careers.honeywell.com","honeywell.com"),
         ("Siemens","https://jobs.siemens.com","siemens.com"),
         ("Siemens Healthineers","https://jobs.siemens-healthineers.com","siemens-healthineers.com"),
         ("TUV SUD","https://careers.tuvsud.com","tuvsud.com"),
         ("Micron","https://careers.micron.com","micron.com"),
         ("ASML","https://www.asml.com","asml.com"),
         ("Trumpf","https://careers.trumpf.com","trumpf.com"),
         ("BD","https://jobs.bd.com","bd.com")]

for name, host, dom in TARGETS:
    found=False
    for path, extra in [("/api/jobs", {"domain":dom,"start":0,"num":10,"location":"Singapore"}),
                        ("/api/jobs", {"domain":dom,"start":0,"num":10}),
                        ("/widgets/api/jobs", {"domain":dom,"start":0,"num":10,"location":"Singapore"}),
                        ("/api/jobs", {"start":0,"num":10,"location":"Singapore"})]:
        try:
            r=S.get(host+path, params=extra, timeout=20)
            if r.status_code==200 and "json" in r.headers.get("content-type",""):
                d=r.json(); jobs=d.get("jobs") or []
                if jobs:
                    dd=jobs[0].get("data") or jobs[0]
                    print(f"  ✓ {name:<22} {path}?domain={extra.get('domain','-')}")
                    print(f"      count={d.get('count') or d.get('totalCount')} 本页={len(jobs)}")
                    for j in jobs[:3]:
                        x=j.get("data") or j
                        print(f"        · {str(x.get('title'))[:46]:<48} {str(x.get('city') or x.get('location_name'))[:18]:<20} {str(x.get('posted_date'))[:10]}")
                    found=True; break
        except Exception: pass
    if not found: print(f"  · {name}")
