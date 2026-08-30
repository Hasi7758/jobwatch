#!/usr/bin/env python3
"""远程诊断:在 GitHub runner 上探明两处故障的真实原因。输出到 stdout。"""
import re, requests, json
from urllib.parse import urljoin

S = requests.Session()
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
S.headers.update({"User-Agent": UA})

print("########## A. Arbeitsagentur ##########")
base_params = {"wo": "München", "umkreis": 25, "size": 2, "page": 1}
variants = [
    ("v4 + X-API-Key",      "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs", {"X-API-Key": "jobboerse-jobsuche"}),
    ("v4 无key",             "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs", {}),
    ("v4 app-UA",           "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs", {"X-API-Key": "jobboerse-jobsuche", "User-Agent": "Jobsuche/1130 CFNetwork/1494 Darwin/23.4.0"}),
    ("v5 + X-API-Key",      "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v5/jobs", {"X-API-Key": "jobboerse-jobsuche"}),
    ("v4 clientId header",  "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v4/jobs", {"OAuthAccessToken": "", "X-API-Key": "c003a37f-024f-462a-b36d-b001be4cd24a"}),
]
for name, url, hdr in variants:
    try:
        r = S.get(url, params=base_params, headers=hdr, timeout=20)
        body = r.text[:280].replace("\n", " ")
        print(f"[{name}] HTTP {r.status_code} | server={r.headers.get('server','')} | body: {body}")
        if r.status_code == 200:
            d = r.json()
            print(f"    -> OK! keys={list(d)[:6]}, 总数={d.get('maxErgebnisse')}")
    except Exception as e:
        print(f"[{name}] 异常: {type(e).__name__} {e}")

print()
print("########## B. arbeitgeberliste.netlify.app ##########")
SITE = "https://arbeitgeberliste.netlify.app/"
r = S.get(SITE, timeout=20)
html = r.text
print(f"首页 HTTP {r.status_code}, {len(html)} 字节")
scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html)
links = re.findall(r'(?:href|src)=["\']([^"\']+\.(?:json|js|mjs))["\']', html)
print("script 标签:", scripts)
print("js/json 引用:", links)
print("首页前600字符:", html[:600].replace("\n"," "))

for s in (scripts + [l for l in links if l not in scripts])[:6]:
    u = urljoin(SITE, s)
    try:
        js = S.get(u, timeout=30).text
    except Exception as e:
        print(f"  {u}: 抓取失败 {e}"); continue
    print(f"\n--- {u} | {len(js)} 字节 ---")
    print("  .json 引用:", list(set(re.findall(r'["\'`]([^"\'`\s]{2,120}\.json)["\'`]', js)))[:10])
    print("  fetch/axios 调用:", list(set(re.findall(r'(?:fetch|axios(?:\.get)?)\(\s*["\'`]([^"\'`]{4,150})["\'`]', js)))[:10])
    for kw in ['"name"', '"firma"', '"Firma"', '"ort"', '"unternehmen"', 'JSON.parse']:
        n = js.count(kw)
        if n: print(f"  含 {kw}: {n} 次")
    i = js.find('[{"')
    if i >= 0:
        print(f"  首个 [{{\" 位置 {i}, 附近500字符:")
        print("   ", js[i:i+500].replace("\n", " "))
