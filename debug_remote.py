#!/usr/bin/env python3
import requests, json, collections
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0","Content-Type":"application/json"})

print("### MCF 薪资字段 ###")
allj=[]
for term in ["engineering manager","technical program manager","project manager"]:
    r=S.post("https://api.mycareersfuture.gov.sg/v2/search?limit=100&page=0",
             json={"search":term,"sessionId":"","categories":[]},timeout=30)
    allj += r.json().get("results") or []
print("样本:", len(allj))
has=[j for j in allj if j.get("salary")]
print(f"带薪资字段: {len(has)}/{len(allj)}")
if has:
    print("salary 结构:", json.dumps(has[0]["salary"], ensure_ascii=False))
hide=sum(1 for j in allj if (j.get("metadata") or {}).get("isHideSalary"))
print("隐藏薪资:", hide)
print("\n薪资分布(月薪中位):")
buckets=collections.Counter()
for j in has:
    s=j["salary"]; mn=s.get("minimum") or 0; mx=s.get("maximum") or 0
    typ=(s.get("type") or {}).get("salaryType","?")
    mid=(mn+mx)/2
    if typ.lower().startswith("month") or mid<50000:
        b=int(mid//2000*2000); buckets[b]+=1
for b,n in sorted(buckets.items()):
    if b>=2000: print(f"  S${b:>6,}-{b+2000:<7,} {'█'*min(n,40)} {n}")
print("\n月薪 >= 9000 的样例:")
c=0
for j in has:
    s=j["salary"]; mx=s.get("maximum") or 0; mn=s.get("minimum") or 0
    if mn>=9000 and mn<60000:
        print(f"  S${mn:,}-{mx:,}  {str(j.get('title'))[:44]:<46} {(j.get('postedCompany') or {}).get('name','')[:26]}")
        c+=1
        if c>=8: break

print("\n### 其它源有没有薪资 ###")
r=S.post("https://micron.wd1.myworkdayjobs.com/wday/cxs/micron/External/jobs",
         json={"appliedFacets":{},"limit":3,"offset":0,"searchText":"Singapore"},timeout=25)
p0=(r.json().get("jobPostings") or [{}])[0]
print("Workday 字段:", list(p0.keys()))
r=S.get("https://boards-api.greenhouse.io/v1/boards/govtech/jobs?content=true",timeout=25)
g0=(r.json().get("jobs") or [{}])[0]
print("Greenhouse 字段:", [k for k in g0.keys()])
