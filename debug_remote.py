#!/usr/bin/env python3
import re, requests
S = requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0"})
r = S.get("https://rodenstock.hr4you.org/index_extern.php?sid=2030&changelanguage=de", timeout=25)
r.encoding = "iso-8859-1"
h = r.text
print("字节", len(h))
print("\n=== 全部 href(去重) ===")
for a in list(dict.fromkeys(re.findall(r'href="([^"]+)"', h)))[:30]: print("  ", a[:110])
print("\n=== 含 (m/w/d) 文本 ===")
print(re.findall(r'([^<>]{6,110}\((?:m/w/d|w/m/d|d/m/w)[^)]*\))', h)[:15])
print("\n=== class 统计 ===")
import collections; print(collections.Counter(re.findall(r'class="([^"]{2,50})"', h)).most_common(20))
print("\n=== 是否 iframe/JS 加载 ===")
print("iframe:", re.findall(r'<iframe[^>]*src="([^"]+)"', h)[:5])
print("script src:", re.findall(r'<script[^>]+src="([^"]+)"', h)[:8])
print("ajax/fetch:", re.findall(r'(?:url|ajax)\s*:\s*["\']([^"\']{4,120})["\']', h)[:8])
print("\n=== 中段 1500 字符(跳过头部) ===")
body = h[h.find("<body"):] if "<body" in h else h
print(body[:1800])
