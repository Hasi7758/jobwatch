#!/usr/bin/env python3
import requests, re
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
B = ("https://www.bmwgroup.jobs/de/de/_jcr_content/main/layoutcontainer/"
     "jobfinder30_copy.jobfinder_table.content.html?filterSearch=location_DE&rowIndex=0&blockCount=5")

tests = [
    ("裸GET 15s", B, {"User-Agent": UA}, 15),
    ("全套浏览器头", B, {"User-Agent": UA, "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
                    "Accept-Language": "de-DE,de;q=0.9", "Referer": "https://www.bmwgroup.jobs/de/de/jobfinder.html",
                    "X-Requested-With": "XMLHttpRequest", "Connection": "keep-alive"}, 25),
    ("主站首页", "https://www.bmwgroup.jobs/de/de.html", {"User-Agent": UA}, 20),
    ("裸域名", "https://bmwgroup.jobs/", {"User-Agent": UA}, 20),
]
for name, url, hdr, to in tests:
    try:
        r = requests.get(url, headers=hdr, timeout=to)
        print(f"[{name}] HTTP {r.status_code}, {len(r.text)} 字节, server={r.headers.get('server','')}")
        if r.status_code == 200 and "jobfinder_table" in url:
            print("   <tr>数:", r.text.count("<tr"), "| 前300:", r.text[:300].replace("\n"," "))
    except Exception as e:
        print(f"[{name}] {type(e).__name__}")

# 公共 CORS 代理能否中转
print("\n--- 公共代理中转 ---")
for name, purl in [
    ("r.jina.ai", "https://r.jina.ai/" + B),
    ("allorigins", "https://api.allorigins.win/raw?url=" + requests.utils.quote(B, safe="")),
    ("codetabs", "https://api.codetabs.com/v1/proxy?quest=" + requests.utils.quote(B, safe="")),
]:
    try:
        r = requests.get(purl, headers={"User-Agent": UA}, timeout=40)
        body = r.text
        print(f"[{name}] HTTP {r.status_code}, {len(body)} 字节")
        if r.status_code == 200 and len(body) > 200:
            titles = re.findall(r'>([^<>]{8,90}\((?:m/w/d|w/m/d|d/m/w)[^)]*\))<', body)
            print("   识别到职位:", titles[:4] if titles else "无(前200字符: " + body[:200].replace("\n"," ") + ")")
    except Exception as e:
        print(f"[{name}] {type(e).__name__}")
