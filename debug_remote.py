#!/usr/bin/env python3
import re, requests
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0"})
API=[("greenhouse",lambda s:f"https://boards-api.greenhouse.io/v1/boards/{s}/jobs"),
     ("lever",lambda s:f"https://api.lever.co/v0/postings/{s}?mode=json"),
     ("ashby",lambda s:f"https://api.ashbyhq.com/posting-api/job-board/{s}"),
     ("smartrecruiters",lambda s:f"https://api.smartrecruiters.com/v1/companies/{s}/postings?limit=5"),
     ("workday",None)]
WD=[("Micron","https://micron.wd1.myworkdayjobs.com/wday/cxs/micron/External/jobs"),
    ("GlobalFoundries","https://globalfoundries.wd1.myworkdayjobs.com/wday/cxs/globalfoundries/External/jobs"),
    ("Infineon","https://infineon.wd3.myworkdayjobs.com/wday/cxs/infineon/Infineon/jobs"),
    ("Applied Materials","https://amat.wd1.myworkdayjobs.com/wday/cxs/amat/External/jobs"),
    ("Medtronic","https://medtronic.wd1.myworkdayjobs.com/wday/cxs/medtronic/MedtronicCareers/jobs"),
    ("Becton Dickinson","https://bd.wd1.myworkdayjobs.com/wday/cxs/bd/EXTERNAL_CAREER_SITE_USA/jobs"),
    ("Siemens","https://siemens.wd3.myworkdayjobs.com/wday/cxs/siemens/SiemensCareers/jobs"),
    ("ASML","https://asml.wd3.myworkdayjobs.com/wday/cxs/asml/ASML_Careers/jobs"),
    ("Carl Zeiss","https://zeiss.wd3.myworkdayjobs.com/wday/cxs/zeiss/ZEISS_Career/jobs"),
    ("ST Engineering","https://stengg.wd3.myworkdayjobs.com/wday/cxs/stengg/ST_Engineering_Careers/jobs")]
print("### Workday ###")
for n,u in WD:
    try:
        r=S.post(u,json={"appliedFacets":{},"limit":20,"offset":0,"searchText":"Singapore"},
                 headers={"Content-Type":"application/json"},timeout=25)
        if r.status_code==200:
            d=r.json(); print(f"  ✓ {n:<20} total={d.get('total')} 本页={len(d.get('jobPostings',[]))}")
        else: print(f"  · {n:<20} HTTP {r.status_code}")
    except Exception as e: print(f"  · {n:<20} {type(e).__name__}")
print("\n### slug 直连 ###")
for slug in ["amd","kla","lamresearch","ultracleanholdings","alcon","hoya","essilorluxottica",
             "tuvsud","festo","sick","bosch","continental","werideai","shein","bytedance",
             "seagroup","shopee","dyson","razer","zendesk","gitlab","cisco","salesforce"]:
    for ats,mk in API[:4]:
        try:
            r=S.get(mk(slug),timeout=8)
            if r.status_code==200 and len(r.content)>80:
                n=len(re.findall(r'"id"\s*:',r.text)); sg=r.text.lower().count("singapore")
                if n: print(f"  ✓ {slug:<20} {ats:<16} ~{n} 职位, SG提及 {sg}")
        except Exception: pass
