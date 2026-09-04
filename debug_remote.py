#!/usr/bin/env python3
import requests, json, re
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0",
                                        "Accept":"application/json, text/html, */*"})

print("###### A. Phenom People (Infineon / Lam / Keysight) ######")
# Phenom 的搜索接口通常是 /widgets 或 /api/jobs
for name, host in [("Infineon","https://jobs.infineon.com"),
                   ("Lam Research","https://careers.lamresearch.com"),
                   ("Keysight","https://careers.keysight.com")]:
    for path, params in [
        ("/widgets", {"location":"Singapore","limit":10,"type":"jobs"}),
        ("/api/jobs", {"location":"Singapore","limit":10}),
        ("/search-jobs/results", {"ActiveFacetID":"0","CurrentPage":"1","SearchTerm":"Singapore"}),
        ("/careers/jobs", {"location":"Singapore"}),
    ]:
        try:
            r=S.get(host+path, params=params, timeout=20)
            ct=r.headers.get("content-type","")[:30]
            ok = r.status_code==200
            n = 0
            if ok and "json" in ct:
                try:
                    d=r.json()
                    s=json.dumps(d)
                    n=s.count('"jobId"')+s.count('"title"')
                except Exception: pass
            print(f"  {name:<14} {path:<24} HTTP {r.status_code} {ct:<24} 迹象={n}")
            if ok and n>3:
                d=r.json(); s=json.dumps(d, ensure_ascii=False)
                print("     样例:", s[:400])
        except Exception as e:
            print(f"  {name:<14} {path:<24} {type(e).__name__}")

print("\n###### B. iCIMS (AMD) ######")
for u,p in [("https://careers-amd.icims.com/jobs/search", {"ss":"1","searchLocation":"Singapore","in_iframe":"1"}),
            ("https://careers.amd.com/api/jobs", {"location":"Singapore","limit":10}),
            ("https://careers.amd.com/careers-home/jobs", {"location":"Singapore"})]:
    try:
        r=S.get(u,params=p,timeout=20)
        print(f"  {u[:52]:<54} HTTP {r.status_code} {len(r.text)}字节 {r.headers.get('content-type','')[:24]}")
        if r.status_code==200:
            ids=set(re.findall(r'/jobs/(\d{4,7})/', r.text))
            print("     job id:", sorted(ids)[:8], f"(共{len(ids)})")
    except Exception as e: print(f"  {u[:52]} {type(e).__name__}")

print("\n###### C. SuccessFactors (Seagate) ######")
for u in ["https://career41.sapsf.com/careers?company=seagatetec",
          "https://career41.sapsf.com/search?company=seagatetec&location=Singapore",
          "https://seagatecareers.com/search/?q=&locationsearch=Singapore"]:
    try:
        r=S.get(u,timeout=25)
        print(f"  {u[:60]:<62} HTTP {r.status_code} {len(r.text)}字节")
        if r.status_code==200:
            jl=re.findall(r'href="(/job/[^"]{6,90})"', r.text)
            print("     /job/ 链接:", jl[:4], f"(共{len(set(jl))})")
            print("     含 jobTitle-link:", r.text.count("jobTitle-link"))
    except Exception as e: print(f"  {u[:60]} {type(e).__name__}")
