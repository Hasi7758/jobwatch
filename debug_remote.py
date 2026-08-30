#!/usr/bin/env python3
import requests, re
from urllib.parse import quote
UA="Mozilla/5.0 Chrome/124.0"
def via(u, to=45):
    return requests.get("https://api.allorigins.win/raw?url="+quote(u,safe=""),
                        headers={"User-Agent":UA}, timeout=to)

B = ("https://www.bmwgroup.jobs/de/de/_jcr_content/main/layoutcontainer/"
     "jobfinder30_copy.jobfinder_table.content.html?filterSearch=location_DE&rowIndex=0&blockCount=40")
r = via(B)
h = r.text
print("HTTP", r.status_code, len(h), "字节")
print("\n=== 前 2500 字符 ===")
print(h[:2500])
print("\n=== href 样例 ===")
print(list(set(re.findall(r'href="([^"]+)"', h)))[:8])
import collections
print("\n=== class 统计 ===")
print(collections.Counter(re.findall(r'class="([^"]{2,70})"', h)).most_common(15))
