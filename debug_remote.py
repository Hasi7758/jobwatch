#!/usr/bin/env python3
import re, requests
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0"})

# Workday: tenant x wdN x site 组合猜测
WD_GUESS=[("AMD","amd",["wd1","wd5"],["External","AMD_External"]),
 ("KLA","kla",["wd1","wd5"],["Search","External"]),
 ("Lam Research","lamresearch",["wd1"],["External"]),
 ("Alcon","alcon",["wd5","wd1"],["Careers","External"]),
 ("Siemens Healthineers","siemens",["wd3"],["SiemensHealthineers","Healthineers"]),
 ("TUV SUD","tuvsud",["wd3","wd1"],["Careers","External"]),
 ("Carl Zeiss","zeiss",["wd3"],["ZEISS_Careers","External","Careers"]),
 ("ST Engineering","stengg",["wd3"],["Careers","External","ST_Engineering"]),
 ("Becton Dickinson","bd",["wd1"],["Careers","External"]),
 ("Infineon","infineon",["wd3"],["Careers","External","IFX"]),
 ("Bosch","bosch",["wd3"],["Careers","External"]),
 ("Rolls-Royce","rollsroyce",["wd3"],["Careers","External"]),
 ("Keysight","keysight",["wd1"],["External"]),
 ("Seagate","seagate",["wd1"],["External","Seagate"]),
 ("Dyson","dyson",["wd3"],["Careers","External"]),
 ("Hoya","hoya",["wd3"],["Careers"]),
]
print("### Workday 组合探测 ###")
for name,ten,wds,sites in WD_GUESS:
    ok=False
    for wd in wds:
        for site in sites:
            u=f"https://{ten}.{wd}.myworkdayjobs.com/wday/cxs/{ten}/{site}/jobs"
            try:
                r=S.post(u,json={"appliedFacets":{},"limit":20,"offset":0,"searchText":"Singapore"},
                         headers={"Content-Type":"application/json"},timeout=20)
                if r.status_code==200:
                    d=r.json(); tot=d.get("total")
                    if tot is not None:
                        print(f"  ✓ {name:<22} {wd}/{site:<22} total={tot}")
                        print(f"      {u}")
                        ok=True; break
            except Exception: pass
        if ok: break
    if not ok: print(f"  · {name}")

print("\n### slug 直连 ###")
API=[("greenhouse",lambda s:f"https://boards-api.greenhouse.io/v1/boards/{s}/jobs"),
     ("lever",lambda s:f"https://api.lever.co/v0/postings/{s}?mode=json"),
     ("ashby",lambda s:f"https://api.ashbyhq.com/posting-api/job-board/{s}"),
     ("smartrecruiters",lambda s:f"https://api.smartrecruiters.com/v1/companies/{s}/postings?limit=5")]
for slug in ["alcon","hoya","tuvsud","zeiss","carlzeiss","stengineering","dyson","amd",
             "keysight","seagate","western-digital","westerndigital","rollsroyce","siemens",
             "siemenshealthineers","bd","beckman","abbott","jnj","philips","bayer"]:
    for ats,mk in API:
        try:
            r=S.get(mk(slug),timeout=8)
            if r.status_code==200 and len(r.content)>80:
                n=len(re.findall(r'"id"\s*:',r.text))
                if n: print(f"  ✓ {slug:<20} {ats:<16} ~{n}")
        except Exception: pass
