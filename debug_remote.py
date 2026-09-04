#!/usr/bin/env python3
import requests, re, concurrent.futures as cf
from urllib.parse import urljoin
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0"})
BASE="https://jobs.infineon.com/careers?start=0&location=Singapore"
h=S.get(BASE,timeout=30).text
scripts=[urljoin(BASE,s) for s in re.findall(r'<script[^>]+src=["\']([^"\']+)["\']',h)]
scripts=[s for s in scripts if "/gen/" in s or "vscdn" in s]
print(f"扫描 {len(scripts)} 个 JS …")

KEY=re.compile(r'(/(?:[a-z0-9_-]+/){0,3}(?:api|widgets|search)[a-z0-9/_-]*)', re.I)
def scan(u):
    try: js=S.get(u,timeout=45).text
    except Exception: return None
    out=[]
    for m in set(KEY.findall(js)):
        if len(m)>4: out.append(("PATH",m))
    for kw in ["/api/jobs","ph-search","x-widget","refineSearch","totalHits","careerSiteApi",
               "jobDetail","recommended-jobs","phenom","ddoKey","jobs?"]:
        i=js.find(kw)
        if i>=0: out.append(("CTX", kw+" :: "+js[max(0,i-90):i+160].replace("\n"," ")[:250]))
    return (u,len(js),out) if out else None

with cf.ThreadPoolExecutor(max_workers=8) as ex:
    for res in ex.map(scan, scripts):
        if not res: continue
        u,n,out=res
        paths=sorted({v for k,v in out if k=="PATH"})
        ctx=[v for k,v in out if k=="CTX"]
        if paths or ctx:
            print(f"\n### {u.split('/')[-1][:50]} ({n}字节)")
            for p in paths[:12]: print("   PATH:", p)
            for c in ctx[:4]: print("   CTX :", c)
