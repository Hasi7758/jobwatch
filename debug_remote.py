#!/usr/bin/env python3
import requests, re, concurrent.futures as cf
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0"})

GERMAN=[("TÜV SÜD","tuvsud"),("TÜV Rheinland","tuv"),("Siemens","siemens"),
 ("Siemens Energy","siemens-energy"),("Siemens Healthineers","siemens-healthineers"),
 ("Bosch","bosch"),("BASF","basf"),("Bayer","bayer"),("Evonik","evonik"),
 ("Merck","merckgroup"),("Lanxess","lanxess"),("Wacker","wacker"),("Linde","linde"),
 ("Infineon","infineon"),("Siltronic","siltronic"),("Rohde & Schwarz","rohde-schwarz"),
 ("Trumpf","trumpf"),("Festo","festo"),("SICK","sick"),("Pepperl+Fuchs","pepperl-fuchs"),
 ("Endress+Hauser","endress"),("Dräger","draeger"),("Freudenberg","freudenberg"),
 ("Heraeus","heraeus"),("Körber","koerber"),("DHL","dhl"),("Lufthansa Technik","lufthansa-technik"),
 ("SAP","sap"),("Continental","continental"),("Schaeffler","schaeffler"),
 ("ZF","zf"),("thyssenkrupp","thyssenkrupp"),("Jebsen & Jessen","jjsea"),
 ("Deutsche Bank","db"),("Allianz","allianz"),("Munich Re","munichre"),("Osram","ams-osram")]

def probe(item):
    name,slug=item
    for host in [f"https://jobs.{slug}.com", f"https://careers.{slug}.com",
                 f"https://jobs.{slug}.de", f"https://{slug}.jobs"]:
        for path,pp in [("/search/",{"q":"","locationsearch":"Singapore"}),
                        ("/search/",{"q":"","location":"Singapore"})]:
            try:
                r=S.get(host+path,params=pp,timeout=12)
            except Exception: continue
            if r.status_code!=200: continue
            jl=list(dict.fromkeys(re.findall(r'href="(/job/[^"]{8,160})"', r.text)))
            if not jl: continue
            tot=re.search(r'([\d,]+)\s*(?:Jobs|jobs|results|Results)', r.text)
            titles=re.findall(r'jobTitle-link[^>]*>\s*([^<]{5,80})', r.text)
            return (name,host,len(jl),tot.group(1) if tot else "?",titles[:3])
    return (name,None,0,"","")

with cf.ThreadPoolExecutor(max_workers=8) as ex:
    for name,host,n,tot,titles in ex.map(probe,GERMAN):
        if host:
            print(f"  ✓ {name:<22} {host:<38} 本页{n:>3}条 总数={tot}")
            for x in titles: print(f"        · {x[:62]}")
        else:
            print(f"  · {name}")
