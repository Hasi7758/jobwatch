#!/usr/bin/env python3
import re, requests
S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0",
                  "Referer": "https://www.bmwgroup.jobs/de/de/jobfinder.html",
                  "X-Requested-With": "XMLHttpRequest"})
B = ("https://www.bmwgroup.jobs/de/de/_jcr_content/main/layoutcontainer/"
     "jobfinder30_copy.jobfinder_table.content.html")

for params in [
    {"filterSearch": "location_DE", "rowIndex": 0, "blockCount": 5},
    {"filterSearch": "location_DE", "rowIndex": 0, "blockCount": 50},
    {"filterSearch": "location_DE", "rowIndex": 0, "blockCount": 100},
]:
    try:
        r = S.get(B, params=params, timeout=30)
        print(f"blockCount={params['blockCount']}: HTTP {r.status_code}, {len(r.text)} 字节, "
              f"<tr>数={r.text.count('<tr')}, <a href数={r.text.count('<a ')}")
    except Exception as e:
        print("异常", e); continue

r = S.get(B, params={"filterSearch": "location_DE", "rowIndex": 0, "blockCount": 5}, timeout=30)
h = r.text
print("\n=== 原始片段前 3000 字符 ===")
print(h[:3000])
print("\n=== 所有 href ===")
print(list(set(re.findall(r'href="([^"]+)"', h)))[:12])
print("\n=== class 名统计 ===")
import collections
print(collections.Counter(re.findall(r'class="([^"]{2,60})"', h)).most_common(20))
