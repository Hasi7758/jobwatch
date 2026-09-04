#!/usr/bin/env python3
import requests, re
from urllib.parse import urljoin
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0"})
BASE="https://jobs.infineon.com/careers?start=0&location=Singapore"
h=S.get(BASE,timeout=30).text
print("页面", len(h), "字节")
scripts=re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', h)
print(f"共 {len(scripts)} 个 JS:")
for s in scripts: print("  ", s[:100])

PAT=re.compile(r'(?:"|\'|`)(/(?:[a-z0-9_-]+/)*(?:api|search|jobs|widgets)[a-z0-9/_-]*)(?:"|\'|`)', re.I)
for s in scripts[:12]:
    u=urljoin(BASE,s)
    try: js=S.get(u,timeout=40).text
    except Exception as e: print(f"\n{s[:60]} 抓取失败"); continue
    hits=set(PAT.findall(js))
    urls=set(x for x in re.findall(r'https?://[a-zA-Z0-9./_?=&%:-]{12,140}', js) if re.search(r'api|job|search|phenom',x,re.I))
    if hits or urls:
        print(f"\n### {s[:70]} ({len(js)}字节)")
        for x in sorted(hits)[:15]: print("   路径:", x)
        for x in sorted(urls)[:10]: print("   URL :", x[:120])
    # ph 特征
    for kw in ["ph-search","phenompeople","x-widget","refineSearch","jobsSearch","/api/jobs"]:
        if kw in js:
            i=js.find(kw)
            print(f"   [{kw}] …{js[max(0,i-100):i+150]}…".replace("\n"," ")[:280])
