#!/usr/bin/env python3
"""探测新加坡职位数据源。"""
import json, re, requests
S = requests.Session()
S.headers.update({"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0",
                  "Accept":"application/json"})

print("###### A. MyCareersFuture (新加坡政府官方门户) ######")
tests = [
    ("GET v2/jobs", "GET", "https://api.mycareersfuture.gov.sg/v2/jobs", {"limit":5,"page":0}, None),
    ("GET v2/search", "GET", "https://api.mycareersfuture.gov.sg/v2/search", {"limit":5,"page":0}, None),
    ("POST v2/search", "POST", "https://api.mycareersfuture.gov.sg/v2/search?limit=5&page=0", None,
       {"search":"manager","sessionId":"","categories":[]}),
    ("POST v2/jobs", "POST", "https://api.mycareersfuture.gov.sg/v2/jobs?limit=5&page=0", None,
       {"search":"manager"}),
    ("GET api.../jobs-api", "GET", "https://api.mycareersfuture.sg/v2/jobs", {"limit":5}, None),
    ("网页首页", "GET", "https://www.mycareersfuture.gov.sg/", None, None),
]
for name, meth, url, params, body in tests:
    try:
        r = S.post(url, json=body, timeout=25) if meth=="POST" else S.get(url, params=params, timeout=25)
        print(f"[{name}] HTTP {r.status_code}, {len(r.content)} 字节")
        if r.status_code == 200 and r.content[:1] in (b"{", b"["):
            d = r.json()
            keys = list(d)[:8] if isinstance(d, dict) else "list"
            print("   keys:", keys)
            res = d.get("results") or d.get("jobs") or d.get("data") or (d if isinstance(d,list) else [])
            print("   条数:", len(res) if hasattr(res,'__len__') else "?", "| 总数:", d.get("total") if isinstance(d,dict) else "")
            if res:
                j0 = res[0]
                print("   字段:", list(j0)[:14])
                print("   样例:", json.dumps(j0, ensure_ascii=False)[:400])
    except Exception as e:
        print(f"[{name}] {type(e).__name__} {str(e)[:60]}")

print()
print("###### B. 新加坡公司 ATS 直连 ######")
API = [("greenhouse", lambda s:f"https://boards-api.greenhouse.io/v1/boards/{s}/jobs"),
       ("lever", lambda s:f"https://api.lever.co/v0/postings/{s}?mode=json"),
       ("ashby", lambda s:f"https://api.ashbyhq.com/posting-api/job-board/{s}"),
       ("smartrecruiters", lambda s:f"https://api.smartrecruiters.com/v1/companies/{s}/postings?limit=5"),
       ("workable", lambda s:f"https://apply.workable.com/api/v1/widget/accounts/{s}?details=true"),
       ("recruitee", lambda s:f"https://{s}.recruitee.com/api/offers/")]
SLUGS = ["grab","sea","shopee","gojek","carousell","ninjavan","propertyguru","razer",
         "circles","govtech","zendesk","stripe","atlassian","glints","tiktok","bytedance",
         "coda","endowus","nium","thoughtworks","aspire","xendit","advance","sleek"]
for slug in SLUGS:
    for ats, mk in API:
        try:
            r = S.get(mk(slug), timeout=8)
            if r.status_code == 200 and len(r.content) > 80:
                n = len(re.findall(r'"id"\s*:', r.text))
                sg = r.text.lower().count("singapore")
                if n:
                    print(f"  ✓ {slug:<14} {ats:<16} ~{n} 职位, 提到 Singapore {sg} 次")
        except Exception:
            pass
