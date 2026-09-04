#!/usr/bin/env python3
import requests, re, json
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0",
    "Referer":"https://jobs.infineon.com/careers","X-Requested-With":"XMLHttpRequest"})
H="https://jobs.infineon.com"
print("### /search 各种调用 ###")
for name,path,params,hdr in [
  ("search html","/search",{"q":"","location":"Singapore"},{}),
  ("search json","/search",{"q":"","location":"Singapore"},{"Accept":"application/json"}),
  ("search start","/search",{"start":0,"num":10,"location":"Singapore"},{"Accept":"application/json"}),
  ("careers json","/careers",{"start":0,"location":"Singapore","pid":""},{"Accept":"application/json"}),
  ("careers ajax","/careers",{"start":0,"location":"Singapore"},{"Accept":"application/json","X-Requested-With":"XMLHttpRequest"}),
  ("api suggest","/api/suggest",{"q":"manager"},{"Accept":"application/json"}),
]:
    try:
        r=S.get(H+path,params=params,headers=hdr,timeout=25)
        ct=r.headers.get("content-type","")[:26]
        print(f"  {name:<14} HTTP {r.status_code} {len(r.text):>7}字节 {ct}")
        if r.status_code==200:
            if "json" in ct:
                s=r.text[:500]; print("     JSON:", s)
            else:
                t=re.findall(r'\((?:m/w/d|f/m/d|m/f/d)\)|Singapore', r.text)
                titles=re.findall(r'data-ph-at-job-title-text="([^"]{4,80})"', r.text)
                titles+=re.findall(r'"jobTitle"\s*:\s*"([^"]{4,80})"', r.text)
                print(f"     标记数={len(t)} 抓到标题={titles[:4]}")
                m=re.search(r'(\{[^{}]*"jobs"\s*:\s*\[.{0,300})', r.text, re.S)
                if m: print("     内嵌jobs:", m.group(1)[:260].replace("\n"," "))
    except Exception as e: print(f"  {name:<14} {type(e).__name__}")

print("\n### 直接看 /search 页面里有没有职位 ###")
r=S.get(H+"/search",params={"location":"Singapore"},timeout=30)
h=r.text
print("字节:",len(h))
for pat in [r'data-ph-at-job-title-text="([^"]+)"', r'job-title[^>]*>([^<]{6,70})<',
            r'"title"\s*:\s*"([^"]{6,70})"', r'/job/(\d+)', r'positionId["\s:=]+(\d+)']:
    f=re.findall(pat,h)
    if f: print(f"  {pat[:40]:<42} -> {f[:5]} (共{len(f)})")
