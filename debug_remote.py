#!/usr/bin/env python3
import requests, re, collections
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0"})
U="https://jobs.infineon.com/gen/js/ef-536eaa00.b460e4d8416cb3353937.js"
r=S.get(U,timeout=40); js=r.text
print(f"HTTP {r.status_code} {len(js)} 字节")

print("\n=== 含 api 的路径字符串 ===")
paths=set(re.findall(r'["\'`](/[a-zA-Z0-9/_.-]{2,80})["\'`]', js))
api=[p for p in paths if re.search(r'api|job|search|widget|graphql', p, re.I)]
for p in sorted(api)[:40]: print("  ", p)

print("\n=== 完整 URL ===")
for u in sorted(set(re.findall(r'https?://[a-zA-Z0-9./_?=&%-]{10,120}', js)))[:30]:
    if re.search(r'api|job|search|phenom|widget', u, re.I): print("  ", u)

print("\n=== 关键词上下文 ===")
for kw in ["/api/", "phApp", "ddo", "jobSearch", "searchJob", "totalHits", "eagerLoad", "domain:"]:
    idx=[m.start() for m in re.finditer(re.escape(kw), js)][:3]
    if idx:
        print(f"\n--- {kw} ({len(idx)}处) ---")
        for i in idx[:2]:
            print("   ", js[max(0,i-140):i+180].replace("\n"," ")[:320])
