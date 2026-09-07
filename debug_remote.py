#!/usr/bin/env python3
import requests, json, re, collections
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0"})
print("### arbeitnow 里慕尼黑 PO/PM 岗位是否含薪资 ###")
hits=[]
for page in range(1,7):
    try:
        d=S.get("https://www.arbeitnow.com/api/job-board-api",params={"page":page},timeout=25).json()
    except Exception: break
    for j in d.get("data",[]):
        loc=(j.get("location") or "").lower()
        ti=(j.get("title") or "").lower()
        if "münchen" in loc or "munich" in loc:
            if any(k in ti for k in ["product owner","product manager","projektmanager","projektleit","program manager"]):
                hits.append(j)
print("命中慕尼黑 PO/PM 岗位:", len(hits))
if hits:
    print("字段:", list(hits[0].keys()))
sal=0
for j in hits:
    txt=json.dumps(j,ensure_ascii=False)
    m=re.findall(r'(\d{2,3})[\.\s]?(\d{3})\s*(?:€|EUR)|€\s*(\d{2,3})[\.\s]?(\d{3})', txt)
    if m or j.get("salary"):
        sal+=1
        print(f"  · {j.get('title')[:52]:<54} salary={j.get('salary')} 文中数字={m[:3]}")
print(f"\n含薪资信息: {sal}/{len(hits)}")
for j in hits[:12]:
    print(f"  {j.get('title')[:56]:<58} {j.get('company_name','')[:26]}")
