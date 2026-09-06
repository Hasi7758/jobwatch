#!/usr/bin/env python3
import requests, json, collections
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0","Content-Type":"application/json"})
allj=[]
for term in ["project manager","engineering manager","product owner"]:
    r=S.post("https://api.mycareersfuture.gov.sg/v2/search?limit=100&page=0",
             json={"search":term,"sessionId":"","categories":[]},timeout=30)
    allj += r.json().get("results") or []
print("样本:", len(allj))
sch=collections.Counter()
for j in allj:
    for s in (j.get("schemes") or []):
        sch[json.dumps(s,ensure_ascii=False)[:120]]+=1
print("\n=== schemes 取值分布 ===")
for k,v in sch.most_common(10): print(f"  {v:>3}  {k}")
print("\n=== 发帖公司 Top20(看中介占比) ===")
for k,v in collections.Counter((j.get("postedCompany") or {}).get("name","?") for j in allj).most_common(20):
    print(f"  {v:>3}  {k[:56]}")
print("\n=== isPostedOnBehalf(代招标志) ===")
ob=sum(1 for j in allj if (j.get("metadata") or {}).get("isPostedOnBehalf"))
print(f"  代招 {ob} / {len(allj)}")
j0=[j for j in allj if (j.get("metadata") or {}).get("isPostedOnBehalf")]
for j in j0[:3]:
    print(f"    · {j.get('title')[:40]:<42} posted={(j.get('postedCompany') or {}).get('name','')[:26]} hiring={(j.get('hiringCompany') or {}).get('name','')[:26]}")
