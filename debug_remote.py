#!/usr/bin/env python3
import requests, json, collections
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0","Content-Type":"application/json"})
allj=[]
for term in ["project manager","engineering manager","product owner","technical program manager"]:
    r=S.post("https://api.mycareersfuture.gov.sg/v2/search?limit=100&page=0",
             json={"search":term,"sessionId":"","categories":[]},timeout=30)
    allj += r.json().get("results") or []
print("样本:", len(allj))

sch=collections.Counter()
for j in allj:
    for s in (j.get("schemes") or []):
        sch[json.dumps(s,ensure_ascii=False)[:130]]+=1
print("\n=== schemes 分布 ===")
for k,v in sch.most_common(8): print(f"  {v:>3}  {k}")

ob=[j for j in allj if (j.get("metadata") or {}).get("isPostedOnBehalf")]
print(f"\n=== isPostedOnBehalf: {len(ob)}/{len(allj)} ===")
for j in ob[:5]:
    print(f"   · {str(j.get('title'))[:36]:<38} posted={(j.get('postedCompany') or {}).get('name','')[:28]:<30} hiring={(j.get('hiringCompany') or {}).get('name','')[:26]}")

print("\n=== 发帖公司 Top 25 ===")
for k,v in collections.Counter((j.get("postedCompany") or {}).get("name","?") for j in allj).most_common(25):
    print(f"  {v:>3}  {k[:58]}")
