#!/usr/bin/env python3
import re, requests
S = requests.Session(); S.headers.update({"User-Agent": "Mozilla/5.0 Chrome/124.0"})
h = S.get("https://arbeitgeberliste.netlify.app/interaktive-karte/unternehmen-mit-ig-metall-flaechentarif-oder-haustarif-sowie-ig-bce", timeout=90).text
js = max(re.finditer(r'<script(?![^>]*src)[^>]*>(.*?)</script>', h, re.S), key=lambda x: len(x.group(1))).group(1)
print("大脚本", len(js), "字节")
print("addFeatures 次数:", js.count("addFeatures"))
print("反引号 ` 次数:", js.count("`"))
print("var feature 次数:", js.count("var feature"))
print("features.push 次数:", js.count("features.push"))
i = js.find("Geometry.Point")
print("\n--- 第一个点位块(Point 起 1400 字符) ---")
print(js[i:i+1400])
print("\n--- addFeatures 首次出现前后 400 ---")
j = js.find("addFeatures")
print(js[max(0,j-300):j+150])
