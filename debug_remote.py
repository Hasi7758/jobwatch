#!/usr/bin/env python3
import requests, re
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0"})

print("### SuccessFactors 列表页格式验证 ###")
HOSTS=[("ST Engineering","https://careers.stengg.com"),
       ("SIA Engineering","https://careers.siaec.com.sg"),
       ("Abbott","https://www.jobs.abbott"),
       ("Seagate","https://seagatecareers.com"),
       ("Stryker","https://careers.stryker.com"),
       ("BD","https://jobs.bd.com"),
       ("Honeywell","https://careers.honeywell.com"),
       ("Micron","https://careers.micron.com"),
       ("TUV SUD","https://careers.tuvsud.com"),
       ("Alcon","https://careers.alcon.com")]
for name,h in HOSTS:
    got=False
    for path,pp in [("/search/",{"q":"","locationsearch":"Singapore"}),
                    ("/search/",{"q":"","location":"Singapore"}),
                    ("/go/Singapore/",{}),
                    ("/searchjobs",{"q":"","locationsearch":"Singapore"})]:
        try:
            r=S.get(h+path,params=pp,timeout=25)
            if r.status_code!=200: continue
            jl=list(dict.fromkeys(re.findall(r'href="(/job/[^"]{8,150})"', r.text)))
            if jl:
                titles=re.findall(r'jobTitle-link[^>]*>\s*([^<]{5,90})', r.text)
                tot=re.search(r'(\d[\d,]*)\s*(?:jobs|Jobs|results|Results)', r.text)
                print(f"  ✓ {name:<18} {path:<12} 职位链接 {len(jl)} 条 | 总数标记={tot.group(1) if tot else '?'}")
                for x in jl[:3]: print("        ", x[:95])
                if titles: print("      标题:", titles[:3])
                got=True; break
        except Exception: pass
    if not got: print(f"  · {name}")
