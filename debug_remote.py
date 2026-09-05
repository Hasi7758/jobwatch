#!/usr/bin/env python3
import requests, re
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0"})
print("### 验证 Workday 链接拼法 ###")
API="https://micron.wd1.myworkdayjobs.com/wday/cxs/micron/External/jobs"
r=S.post(API,json={"appliedFacets":{},"limit":5,"offset":0,"searchText":"Singapore"},
         headers={"Content-Type":"application/json"},timeout=25)
posts=r.json().get("jobPostings",[])
base=API.split("/wday/")[0]; site=re.search(r"/wday/cxs/[^/]+/([^/]+)/jobs",API).group(1)
for p_ in posts[:4]:
    path=p_.get("externalPath",""); loc=p_.get("locationsText","")
    for label,u in [("旧(错)",base+path),("新(修)",base+"/"+site+path)]:
        try:
            rr=S.get(u,timeout=15,allow_redirects=True)
            print(f"  {label} HTTP {rr.status_code} | {p_.get('title','')[:34]:<36} loc={loc[:26]}")
        except Exception as e: print(f"  {label} {type(e).__name__}")
    print()
