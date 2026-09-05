#!/usr/bin/env python3
import requests, json
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0","Content-Type":"application/json"})
print("### MCF 是否返回描述 ###")
r=S.post("https://api.mycareersfuture.gov.sg/v2/search?limit=3&page=0",
         json={"search":"engineering manager","sessionId":"","categories":[]},timeout=25)
d=r.json(); res=d.get("results") or []
if res:
    j=res[0]
    print("  字段:", list(j.keys()))
    for k in ["description","jobDescription","skills","categories"]:
        if k in j:
            v=json.dumps(j[k],ensure_ascii=False)
            print(f"  {k}: {v[:220]}")
print("\n### Workday 是否返回描述 (Micron) ###")
r=S.post("https://micron.wd1.myworkdayjobs.com/wday/cxs/micron/External/jobs",
         json={"appliedFacets":{},"limit":3,"offset":0,"searchText":"Singapore manager"},timeout=25)
d=r.json()
for j in (d.get("jobPostings") or [])[:1]:
    print("  字段:", list(j.keys()))
print("\n### Greenhouse content=true ###")
r=S.get("https://boards-api.greenhouse.io/v1/boards/govtech/jobs?content=true",timeout=25)
jj=(r.json().get("jobs") or [])
if jj:
    print("  字段:", list(jj[0].keys()))
    print("  content 长度:", len(str(jj[0].get("content",""))))
