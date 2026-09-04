#!/usr/bin/env python3
import requests, re, json
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0"})

print("### 抓用户给的真实页面,找内嵌数据/接口 ###")
URLS=[("Infineon","https://jobs.infineon.com/careers?start=0&location=Singapore&sort_by=distance"),
      ("Lam","https://careers.lamresearch.com/careers?start=0&sort_by=timestamp"),
      ("AMD-ok","https://careers.amd.com/api/jobs?location=Singapore&limit=5&page=1")]
for name,u in URLS:
    try:
        r=S.get(u,timeout=30); h=r.text
    except Exception as e:
        print(f"{name}: {type(e).__name__}"); continue
    print(f"\n=== {name} HTTP {r.status_code} {len(h)} 字节 {r.headers.get('content-type','')[:28]}")
    if "json" in r.headers.get("content-type",""):
        print("  已是JSON,跳过"); continue
    # Phenom 常把首屏数据塞进 window.* 变量
    for var in ["phApp.ddo","window.phApp","__INITIAL_STATE__","eagerLoadRefineSearch","jobs\":\["]:
        i=h.find(var)
        print(f"  {var:<26} {'@'+str(i) if i>=0 else '未出现'}")
    m=re.search(r'"eagerLoadRefineSearch"\s*:\s*(\{.{0,600})', h, re.S)
    if m: print("  eagerLoad 片段:", m.group(1)[:400].replace("\n"," "))
    # 找 api 路径
    apis=set(re.findall(r'["\'](/[a-z0-9/_-]*api[a-z0-9/_-]*)["\']', h, re.I))
    print("  页面里的 api 路径:", sorted(apis)[:12])
    hosts=set(re.findall(r'https://([a-z0-9.-]*phenom[a-z0-9.-]*)', h, re.I))
    print("  phenom 域名:", sorted(hosts)[:6])
    m2=re.search(r'"totalHits?"\s*:\s*(\d+)', h)
    print("  totalHits:", m2.group(1) if m2 else "无")
