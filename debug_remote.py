#!/usr/bin/env python3
import requests, re, itertools
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0"})
print("### Workday 穷举(航空MRO + 半导体 + 医疗)###")
TEN={"ST Engineering":["stengg","stengineering","st-engineering"],
     "Rolls-Royce":["rollsroyce","rr","royce"],
     "RTX/Collins":["rtx","raytheon","utc","collins"],
     "Honeywell":["honeywell"],
     "Safran":["safran"],
     "SIA Engineering":["siaec","siaengineering"],
     "Singapore Airlines":["singaporeairlines","sia"],
     "Abbott":["abbott"],
     "J&J":["jnj","johnsonandjohnson"],
     "Stryker":["stryker"],
     "Boston Scientific":["bostonscientific","bsci"],
     "AMD":["amd"],
     "Lam Research":["lamresearch","lam"],
     "Infineon":["infineon"],
     "Seagate":["seagate"],
     "Keysight":["keysight"],
     "Siemens Healthineers":["healthineers","siemenshealthineers"],
     "Dyson":["dyson"],
     "Shell":["shell"],
     "Schneider":["schneiderelectric","se"]}
SITES=["External","Careers","Search","ExternalCareers","External_Career_Site","Global",
       "CareerSite","careers","Professional","ExternalSite"]
WDS=["wd1","wd3","wd5"]
for name,tens in TEN.items():
    hit=None
    for ten,wd,site in itertools.product(tens,WDS,SITES):
        u=f"https://{ten}.{wd}.myworkdayjobs.com/wday/cxs/{ten}/{site}/jobs"
        try:
            r=S.post(u,json={"appliedFacets":{},"limit":1,"offset":0,"searchText":"Singapore"},
                     headers={"Content-Type":"application/json"},timeout=8)
            if r.status_code==200:
                d=r.json()
                if d.get("total") is not None:
                    hit=(u,d.get("total")); break
        except Exception: pass
    print((f"  ✓ {name:<22} SG={hit[1]}\n      {hit[0]}") if hit else f"  · {name}")

print("\n### slug 直连 ###")
API=[("greenhouse",lambda s:f"https://boards-api.greenhouse.io/v1/boards/{s}/jobs"),
     ("lever",lambda s:f"https://api.lever.co/v0/postings/{s}?mode=json"),
     ("ashby",lambda s:f"https://api.ashbyhq.com/posting-api/job-board/{s}"),
     ("smartrecruiters",lambda s:f"https://api.smartrecruiters.com/v1/companies/{s}/postings?limit=5")]
for slug in ["stengineering","stengg","rollsroyce","siaec","safran","honeywell","abbott",
             "stryker","bostonscientific","amd","lamresearch","seagate","keysight","dyson",
             "shell","schneiderelectric","sembcorp","keppel","seagroup","sea"]:
    for ats,mk in API:
        try:
            r=S.get(mk(slug),timeout=8)
            if r.status_code==200 and len(r.content)>80:
                n=len(re.findall(r'"id"\s*:',r.text)); sg=r.text.lower().count("singapore")
                if n: print(f"  ✓ {slug:<20} {ats:<16} ~{n} 条, SG {sg}")
        except Exception: pass
