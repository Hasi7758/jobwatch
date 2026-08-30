#!/usr/bin/env python3
import re, requests
from urllib.parse import urljoin
S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0"})

URL = "https://arbeitgeberliste.netlify.app/interaktive-karte/unternehmen-mit-ig-metall-flaechentarif-oder-haustarif-sowie-ig-bce"
r = S.get(URL, timeout=30)
h = r.text
print(f"地图页 HTTP {r.status_code}, {len(h)} 字节")
print("script src:", re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', h))
print("内联script数:", len(re.findall(r'<script(?![^>]*src)', h)))
print("geojson/json 引用:", list(set(re.findall(r'["\'\(]([^"\'\)\s]{2,150}\.(?:geo)?json)["\'\)]', h)))[:15])
print("fetch调用:", list(set(re.findall(r'fetch\(\s*["\'`]([^"\'`]{3,150})["\'`]', h)))[:15])
print("umap特征:", "umap" in h.lower(), "| leaflet:", "leaflet" in h.lower(), "| L.marker数:", h.count("L.marker"), "| circleMarker:", h.count("circleMarker"))
# 数据若内嵌:找大数组
for pat in ['[{"', "[{'", 'var data', 'const data', 'addLayer', 'L.geoJSON', 'L.geoJson']:
    i = h.find(pat)
    if i >= 0:
        print(f"\n--- 首个 {pat!r} @ {i},上下600字符 ---")
        print(h[max(0,i-100):i+500].replace("\n", " "))
# 内联 script 逐个报尺寸
for m in re.finditer(r'<script(?![^>]*src)[^>]*>(.*?)</script>', h, re.S):
    body = m.group(1)
    if len(body) > 500:
        print(f"\n=== 内联script {len(body)} 字节, 开头400: ===")
        print(body[:400].replace("\n"," "))
        js_refs = list(set(re.findall(r'["\'`]([^"\'`\s]{2,150}\.(?:geo)?json)["\'`]', body)))
        if js_refs: print("  其中json引用:", js_refs[:15])
