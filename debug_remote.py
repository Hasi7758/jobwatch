#!/usr/bin/env python3
import requests, json
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0","Content-Type":"application/json"})
r=S.post("https://api.mycareersfuture.gov.sg/v2/search?limit=3&page=0",
         json={"search":"project manager","sessionId":"","categories":[]},timeout=25)
res=r.json().get("results") or []
print("字段:", list(res[0].keys()))
j=res[0]
meta=j.get("metadata") or {}
print("metadata 字段:", list(meta.keys()))
print()
for k in ["uuid","jobPostId","jobDetailsUrl","originalPostingDate"]:
    v = j.get(k) or meta.get(k)
    print(f"  {k} = {v}")
print()
print("完整 metadata:", json.dumps(meta, ensure_ascii=False)[:400])
print()
print("### 测试各种链接格式 ###")
uuid=j.get("uuid"); jpid=meta.get("jobPostId")
title=(j.get("title") or "").lower().replace(" ","-").replace("/","-")
comp=((j.get("postedCompany") or {}).get("name") or "").lower().replace(" ","-")
cands=[f"https://www.mycareersfuture.gov.sg/job/{jpid}",
       f"https://www.mycareersfuture.gov.sg/job/{uuid}",
       f"https://www.mycareersfuture.gov.sg/job/{title}-{uuid}",
       f"https://www.mycareersfuture.gov.sg/job/engineering/{title}-{comp}-{uuid}",
       j.get("jobDetailsUrl") or ""]
for u in cands:
    if not u: continue
    try:
        rr=S.get(u,timeout=20,allow_redirects=True,headers={"Accept":"text/html"})
        print(f"  HTTP {rr.status_code} {len(rr.text):>7}字节  {u[:88]}")
        if rr.status_code==200 and "not found" not in rr.text[:3000].lower():
            print("       -> 最终URL:", rr.url[:100])
    except Exception as e: print(f"  {type(e).__name__} {u[:70]}")
