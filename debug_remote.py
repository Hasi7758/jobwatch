#!/usr/bin/env python3
import requests, re
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0","Content-Type":"application/json"})
WD=[("Micron","https://micron.wd1.myworkdayjobs.com/wday/cxs/micron/External/jobs"),
    ("GlobalFoundries","https://globalfoundries.wd1.myworkdayjobs.com/wday/cxs/globalfoundries/External/jobs"),
    ("Applied Materials","https://amat.wd1.myworkdayjobs.com/wday/cxs/amat/External/jobs"),
    ("KLA","https://kla.wd1.myworkdayjobs.com/wday/cxs/kla/Search/jobs"),
    ("Medtronic","https://medtronic.wd1.myworkdayjobs.com/wday/cxs/medtronic/MedtronicCareers/jobs")]
print(f"{'公司':<20} {'全球总数':>8} {'含Singapore':>12} {'其中管理岗':>10}")
for n,u in WD:
    try:
        a=S.post(u,json={"appliedFacets":{},"limit":1,"offset":0,"searchText":""},timeout=25).json()
        b=S.post(u,json={"appliedFacets":{},"limit":20,"offset":0,"searchText":"Singapore"},timeout=25).json()
        c=S.post(u,json={"appliedFacets":{},"limit":20,"offset":0,"searchText":"Singapore manager"},timeout=25).json()
        print(f"{n:<20} {str(a.get('total')):>8} {str(b.get('total')):>12} {str(c.get('total')):>10}")
        for p in (b.get("jobPostings") or [])[:3]:
            print(f"     · {p.get('title','')[:52]:<54} {p.get('postedOn','')}")
    except Exception as e:
        print(f"{n:<20} 失败 {type(e).__name__}")

print("\n### SmartRecruiters / Greenhouse 新加坡岗位数 ###")
for n,u,typ in [("Grab","https://api.smartrecruiters.com/v1/companies/grab/postings?limit=100","sr"),
                ("Western Digital","https://api.smartrecruiters.com/v1/companies/westerndigital/postings?limit=100","sr"),
                ("EssilorLuxottica","https://api.smartrecruiters.com/v1/companies/essilorluxottica/postings?limit=100","sr"),
                ("Continental","https://api.smartrecruiters.com/v1/companies/continental/postings?limit=100","sr"),
                ("ByteDance","https://api.smartrecruiters.com/v1/companies/bytedance/postings?limit=100","sr"),
                ("SHEIN","https://boards-api.greenhouse.io/v1/boards/shein/jobs","gh"),
                ("GovTech","https://boards-api.greenhouse.io/v1/boards/govtech/jobs","gh")]:
    try:
        d=S.get(u,timeout=25).json()
        items=d.get("content") if typ=="sr" else d.get("jobs")
        items=items or []
        sg=[j for j in items if "singapore" in str(j).lower()]
        print(f"  {n:<18} 取回 {len(items):>4} 条, 其中新加坡 {len(sg):>3}")
        for j in sg[:2]:
            print(f"       · {(j.get('name') or j.get('title',''))[:56]}")
    except Exception as e:
        print(f"  {n:<18} 失败 {type(e).__name__}")
