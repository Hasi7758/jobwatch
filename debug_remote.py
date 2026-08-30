#!/usr/bin/env python3
import re, requests, json
S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0"})

SIG = [("workday", r"([a-z0-9-]+)\.(wd\d)\.myworkdayjobs\.com/(?:[a-z-]+/)?([^/\"'?]+)"),
       ("successfactors", r"([a-z0-9-]+)\.(?:jobs\.)?(?:successfactors|sapsf)\.(?:com|eu)"),
       ("softgarden", r"([a-z0-9-]+)\.softgarden\.io"),
       ("personio", r"([a-z0-9-]+)\.jobs\.personio\.(?:de|com)"),
       ("greenhouse", r"boards\.greenhouse\.io/([a-z0-9]+)"),
       ("smartrecruiters", r"smartrecruiters\.com/([A-Za-z0-9]+)"),
       ("lever", r"jobs\.lever\.co/([a-z0-9-]+)"),
       ("ashby", r"jobs\.ashbyhq\.com/([a-z0-9-]+)"),
       ("recruitee", r"([a-z0-9-]+)\.recruitee\.com"),
       ("workable", r"apply\.workable\.com/([a-z0-9-]+)"),
       ("join", r"join\.com/companies/([a-z0-9-]+)"),
       ("dvinci", r"([a-z0-9-]+)\.dvinci(?:hr)?\.(?:com|de)"),
       ("rexx", r"([a-z0-9-]+)\.rexx-systems\.com"),
       ("concludis", r"([a-z0-9-]+)\.concludis\.de"),
       ("teamtailor", r"([a-z0-9-]+)\.teamtailor\.com"),
       ("umantis", r"([a-z0-9-]+)\.umantis\.com"),
       ("avature", r"([a-z0-9-]+)\.avature\.net")]

print("###### A. 官网招聘页识别 ######")
for path in ["/karriere", "/de/karriere", "/karriere/stellenangebote", "/jobs",
             "/de/karriere/offene-stellen", "/company/karriere", "/"]:
    for base in ["https://www.rodenstock.com", "https://rodenstock.com"]:
        try:
            r = S.get(base + path, timeout=18, allow_redirects=True)
        except Exception:
            continue
        if r.status_code != 200:
            continue
        blob = r.text + " " + r.url
        for ats, pat in SIG:
            m = re.search(pat, blob, re.I)
            if m:
                print(f"  ✓ {ats}: {m.groups()}  (发现于 {r.url[:70]})")
        if "karriere" in r.url.lower() or "career" in r.url.lower():
            print(f"  招聘页: {r.url[:90]} ({len(r.text)}字节)")
            for kw in ["stellenangebote", "jobboerse", "jobs.", "bewerb"]:
                for m in re.findall(r'href="([^"]*' + kw + r'[^"]*)"', r.text, re.I)[:3]:
                    print("     链接:", m[:100])

print("\n###### B. 直接试常见 slug ######")
for slug in ["rodenstock", "rodenstockgmbh", "rodenstock-gmbh"]:
    for name, url in [("personio", f"https://{slug}.jobs.personio.de/xml"),
                      ("greenhouse", f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"),
                      ("smartrecruiters", f"https://api.smartrecruiters.com/v1/companies/{slug}/postings?limit=5"),
                      ("softgarden", f"https://{slug}.softgarden.io/api/rest/frontend/v3/job-postings?limit=5"),
                      ("recruitee", f"https://{slug}.recruitee.com/api/offers/"),
                      ("ashby", f"https://api.ashbyhq.com/posting-api/job-board/{slug}"),
                      ("workable", f"https://apply.workable.com/api/v1/widget/accounts/{slug}?details=true")]:
        try:
            r = S.get(url, timeout=12)
            if r.status_code == 200 and len(r.content) > 60:
                n = len(re.findall(r'"id"\s*:|<position>', r.text))
                print(f"  ✓ {slug} / {name}: HTTP 200, ~{n} 职位")
                if n:
                    print("     样例:", re.findall(r'"(?:name|title|text)"\s*:\s*"([^"]{5,70})"', r.text)[:5]
                          or re.findall(r"<name>([^<]{5,70})</name>", r.text)[:5])
        except Exception:
            pass

print("\n###### C. arbeitnow 里现在有没有 Rodenstock ######")
found = []
for page in range(1, 7):
    try:
        d = S.get("https://www.arbeitnow.com/api/job-board-api", params={"page": page}, timeout=25).json()
    except Exception:
        break
    for j in d.get("data", []):
        if "rodenstock" in (j.get("company_name","") + j.get("title","")).lower():
            found.append(j)
print("  命中:", len(found))
for j in found[:10]:
    print(f"    · {j.get('title')[:60]} | {j.get('location')} | {j.get('created_at')}")
