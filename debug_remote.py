#!/usr/bin/env python3
import re, requests
S = requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0","Accept-Language":"de-DE,de;q=0.9"})

for u in ["https://rodenstock.hr4you.org/index_extern.php?sid=2030&changelanguage=de",
          "https://rodenstock.hr4you.org/index_extern.php?changelanguage=de",
          "https://rodenstock.hr4you.org/index.php?changelanguage=de"]:
    try:
        r = S.get(u, timeout=25)
    except Exception as e:
        print(u, type(e).__name__); continue
    r.encoding = r.apparent_encoding or "iso-8859-1"
    h = r.text
    ids = re.findall(r'generator\.php\?id=(\d+)', h)
    print(f"\n===== {u[:70]}")
    print(f"HTTP {r.status_code} {len(h)}字节 | generator.php?id 出现 {len(ids)} 次, 唯一 {len(set(ids))} 个")
    print("id样例:", sorted(set(ids))[:15])
    titles = re.findall(r'generator\.php\?id=(\d+)[^"]*"[^>]*>\s*([^<>]{5,120}?)\s*<', h)
    print("链接文字样例:")
    for i,tt in titles[:10]: print(f"   {i}: {tt}")
    if len(set(ids)) > 3:
        print("--- 一条记录的原文 ---")
        m = re.search(r'.{300}generator\.php\?id=\d+.{500}', h, re.S)
        if m: print(m.group(0).replace("\n"," ")[:900])
