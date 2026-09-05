#!/usr/bin/env python3
import requests, re
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0"})
H="https://jobs.tuvsud.com"
print("### TÜV SÜD 路径探测 ###")
for path,pp in [("/search/",{"q":"","locationsearch":"Singapore"}),
                ("/search/",{}),("/","" ),("/go/Singapore/",{}),
                ("/search/",{"q":"manager"}),("/searchjobs",{}),
                ("/ListJobs/All/",{}),("/search/?q=&sortColumn=referencedate&sortDirection=desc",{})]:
    try:
        r=S.get(H+path,params=pp or None,timeout=20)
        jl=list(dict.fromkeys(re.findall(r'href="(/job/[^"]{8,160})"', r.text))) if r.status_code==200 else []
        print(f"  {path:<52} HTTP {r.status_code} {len(r.text):>7}字节 /job/链接={len(jl)}")
        if jl:
            print("     样例:", jl[:3])
            tot=re.search(r'([\d,]+)\s*(?:Jobs|jobs)', r.text)
            print("     总数:", tot.group(1) if tot else "?")
            break
    except Exception as e: print(f"  {path:<52} {type(e).__name__}")

print("\n### 验证已探通德企的新加坡岗位量 ###")
for name,host in [("Bayer","https://jobs.bayer.com"),("Festo","https://jobs.festo.com"),
                  ("SAP","https://jobs.sap.com"),("Schaeffler","https://jobs.schaeffler.com"),
                  ("ZF","https://jobs.zf.com"),("Körber","https://jobs.koerber.com")]:
    try:
        r=S.get(host+"/search/",params={"q":"","locationsearch":"Singapore"},timeout=20)
        jl=list(dict.fromkeys(re.findall(r'href="(/job/[^"]{8,160})"', r.text)))
        sg=sum(1 for x in jl if "singapore" in x.lower())
        tot=re.search(r'([\d,]+)\s*(?:Jobs|jobs)\s*(?:found|Found)?', r.text)
        print(f"  {name:<12} 链接{len(jl):>3} URL含Singapore={sg:>3} 页面总数标记={tot.group(1) if tot else '?'}")
        for x in jl[:2]:
            if "singapore" in x.lower(): print("      ·", x[:80])
    except Exception as e: print(f"  {name:<12} {type(e).__name__}")
