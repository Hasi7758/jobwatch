#!/usr/bin/env python3
import requests, json, re
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0","Accept":"application/json"})

print("###### A. Oracle HCM REST 接口 ######")
HOST="https://fa-esta-saasfaprod1.fa.ocs.oraclecloud.com"
API=HOST+"/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
for name,params in [
 ("标准 finder", {"onlyData":"true","expand":"requisitionList.secondaryLocations,flexFieldsFacet.values",
   "finder":"findReqs;siteNumber=CX_1001,limit=50,sortBy=POSTING_DATES_DESC"}),
 ("带地点", {"onlyData":"true",
   "finder":"findReqs;siteNumber=CX_1001,limit=50,locationId=300000000440956,locationLevel=country,sortBy=POSTING_DATES_DESC"}),
 ("最简", {"onlyData":"true","finder":"findReqs;siteNumber=CX_1001,limit=10"}),
]:
    try:
        r=S.get(API,params=params,timeout=30)
        print(f"  [{name}] HTTP {r.status_code} {len(r.content)}字节")
        if r.status_code==200:
            d=r.json()
            items=(d.get("items") or [{}])[0].get("requisitionList") or []
            print(f"     职位数={len(items)} | 总数={(d.get('items') or [{}])[0].get('TotalJobsCount')}")
            for j in items[:4]:
                print(f"       · {str(j.get('Title'))[:52]:<54} {str(j.get('PrimaryLocation'))[:22]:<24} {j.get('PostedDate')}")
            if items: print("     字段:", list(items[0].keys())[:16])
            break
    except Exception as e: print(f"  [{name}] {type(e).__name__} {str(e)[:70]}")

print("\n###### B. 这是哪家公司? ######")
try:
    r=S.get(HOST+"/hcmUI/CandidateExperience/en/sites/CX_1001/jobs",timeout=25,
            headers={"Accept":"text/html"})
    t=r.text
    print("  HTTP",r.status_code,len(t),"字节")
    for pat in [r'<title>([^<]{3,80})</title>', r'"companyName"\s*:\s*"([^"]+)"',
                r'alt="([^"]{3,40})\s*logo', r'og:site_name"\s*content="([^"]+)"']:
        m=re.search(pat,t,re.I)
        if m: print("  ", pat[:26], "->", m.group(1))
except Exception as e: print("  ", type(e).__name__)

print("\n###### C. Siemens Healthineers ######")
for u,p in [("https://jobs.siemens-healthineers.com/de_DE/searchjobs/results",{"searchTerm":"","location":"Singapore"}),
            ("https://jobs.siemens-healthineers.com/en_US/searchjobs/results",{"location":"Singapore"}),
            ("https://jobs.siemens-healthineers.com/de_DE/searchjobs",{"location":"Singapore"}),
            ("https://jobs.siemens-healthineers.com/api/jobs",{"location":"Singapore"})]:
    try:
        r=S.get(u,params=p,timeout=25,headers={"Accept":"application/json, text/html"})
        ct=r.headers.get("content-type","")[:24]
        print(f"  {u.split('.com')[1][:38]:<40} HTTP {r.status_code} {len(r.text):>7}字节 {ct}")
        if r.status_code==200:
            ids=set(re.findall(r'JobDetail/(\d{4,8})', r.text))
            tt=re.findall(r'JobDetail/\d+[^>]*>\s*([^<]{5,80})', r.text)
            if ids: print(f"      JobDetail id: {sorted(ids)[:6]} (共{len(ids)}) 标题:{tt[:3]}")
    except Exception as e: print(f"  {u[:44]} {type(e).__name__}")
