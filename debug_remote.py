#!/usr/bin/env python3
import re, requests
S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0",
                  "Accept-Language": "de-DE,de;q=0.9"})

print("###### A. HR4YOU 职位列表探测 ######")
cands = [
    "https://rodenstock.hr4you.org/generator.php?id=2030&changelanguage=de",
    "https://rodenstock.hr4you.org/joblist.php?changelanguage=de",
    "https://rodenstock.hr4you.org/index.php?changelanguage=de",
    "https://rodenstock.hr4you.org/",
    "https://rodenstock.hr4you.org/joboffers.php",
    "https://rodenstock.hr4you.org/rss.php",
    "https://rodenstock.hr4you.org/feed.php",
]
for u in cands:
    try:
        r = S.get(u, timeout=20, allow_redirects=True)
        n_job = len(re.findall(r'job(?:id|_id|ID)=(\d+)', r.text, re.I))
        print(f"{u[:64]:<66} HTTP {r.status_code} {len(r.text):>7}字节 jobid数={n_job} 最终={r.url[:60]}")
    except Exception as e:
        print(f"{u[:64]:<66} {type(e).__name__}")

print("\n###### B. 主列表页结构 ######")
r = S.get("https://rodenstock.hr4you.org/generator.php?id=2030&changelanguage=de", timeout=25)
h = r.text
print("HTTP", r.status_code, len(h), "字节")
print("\n--- 所有 href(去重前20) ---")
print(list(dict.fromkeys(re.findall(r'href="([^"]+)"', h)))[:20])
print("\n--- 含 (m/w/d) 的文本 ---")
print(re.findall(r'>([^<>]{6,110}\((?:m/w/d|w/m/d|d/m/w|m/f/d)[^)]*\))\s*<', h)[:12])
print("\n--- class 统计 ---")
import collections
print(collections.Counter(re.findall(r'class="([^"]{2,50})"', h)).most_common(18))
print("\n--- 前 2200 字符 ---")
print(h[:2200])
