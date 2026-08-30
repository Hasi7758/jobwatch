#!/usr/bin/env python3
import re, requests
S = requests.Session(); S.headers.update({"User-Agent": "Mozilla/5.0 Chrome/124.0"})
h = S.get("https://arbeitgeberliste.netlify.app/interaktive-karte/unternehmen-mit-ig-metall-flaechentarif-oder-haustarif-sowie-ig-bce", timeout=60).text
m = max(re.finditer(r'<script(?![^>]*src)[^>]*>(.*?)</script>', h, re.S), key=lambda x: len(x.group(1)))
js = m.group(1)
print("大脚本:", len(js), "字节")
for pat in ["LonLat", "Geometry.Point", "Feature.Vector", "OpenLayers.Marker", "Popup", "Layer.Vector", "Layer.Markers", "addMarker", "createMarker", "attributes"]:
    print(f"  {pat}: {js.count(pat)} 次")
print("\nLayer.Vector/Markers 定义(前8个):")
for x in re.findall(r'new OpenLayers\.Layer\.(?:Vector|Markers)\(\s*["\']([^"\']+)["\']', js)[:8]:
    print("  层名:", x)
for pat in ["Geometry.Point", "createMarker", "addMarker", "OpenLayers.Marker"]:
    i = js.find(pat)
    if i >= 0:
        print(f"\n--- {pat} 首次出现,前后900字符 ---")
        print(js[max(0,i-450):i+450].replace("\n", " "))
        break
i = js.find("Popup")
if i >= 0:
    print("\n--- Popup 首次出现,前后800 ---")
    print(js[max(0,i-200):i+600].replace("\n"," "))
