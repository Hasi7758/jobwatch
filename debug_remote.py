#!/usr/bin/env python3
"""从公司官网招聘页反推它用的招聘系统(ATS)。"""
import re, requests
S = requests.Session()
S.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0"})

SIG = [
    ("workday",        r"([a-z0-9-]+)\.(wd\d)\.myworkdayjobs\.com/([^/\"'?]+)"),
    ("successfactors", r"([a-z0-9-]+)\.(?:jobs\.)?(?:successfactors|sapsf)\.(?:com|eu)"),
    ("softgarden",     r"([a-z0-9-]+)\.softgarden\.io"),
    ("personio",       r"([a-z0-9-]+)\.jobs\.personio\.(?:de|com)"),
    ("greenhouse",     r"boards\.greenhouse\.io/([a-z0-9]+)"),
    ("smartrecruiters", r"jobs\.smartrecruiters\.com/([A-Za-z0-9]+)"),
    ("lever",          r"jobs\.lever\.co/([a-z0-9-]+)"),
    ("ashby",          r"jobs\.ashbyhq\.com/([a-z0-9-]+)"),
    ("recruitee",      r"([a-z0-9-]+)\.recruitee\.com"),
    ("workable",       r"apply\.workable\.com/([a-z0-9-]+)"),
    ("join",           r"join\.com/companies/([a-z0-9-]+)"),
    ("teamtailor",     r"([a-z0-9-]+)\.teamtailor\.com"),
    ("dvinci",         r"([a-z0-9-]+)\.dvinci(?:hr)?\.(?:com|de)"),
    ("rexx",           r"([a-z0-9-]+)\.rexx-systems\.com"),
    ("concludis",      r"([a-z0-9-]+)\.concludis\.de"),
    ("umantis",        r"([a-z0-9-]+)\.umantis\.com"),
    ("avature",        r"([a-z0-9-]+)\.avature\.net"),
    ("taleo",          r"([a-z0-9-]+)\.taleo\.net"),
    ("jobvite",        r"jobs\.jobvite\.com/([a-z0-9-]+)"),
]

TARGETS = [
    ("BMW Group", "bmwgroup.jobs", ["/de/", "/"]),
    ("MAN Truck & Bus", "man.eu", ["/de/de/karriere/", "/karriere/"]),
    ("MTU Aero Engines", "mtu.de", ["/karriere/", "/de/karriere/"]),
    ("KraussMaffei", "kraussmaffei.com", ["/de/karriere", "/karriere", "/de-de/karriere"]),
    ("KUKA", "kuka.com", ["/de-de/karriere", "/karriere"]),
    ("Airbus", "airbus.com", ["/en/careers", "/careers"]),
    ("Siemens", "siemens.com", ["/global/en/company/jobs.html", "/de/de/unternehmen/jobs.html"]),
    ("Rohde & Schwarz", "rohde-schwarz.com", ["/karriere/", "/de/karriere/karriere_231.html"]),
    ("Knorr-Bremse", "knorr-bremse.com", ["/de/karriere/", "/karriere/"]),
    ("Linde Material Handling", "linde-mh.de", ["/karriere/", "/de/karriere/"]),
    ("RENK", "renk.com", ["/de/karriere", "/karriere"]),
    ("Wacker Chemie", "wacker.com", ["/cms/de-de/karriere/karriere.html", "/karriere"]),
    ("Siltronic", "siltronic.com", ["/de/karriere.html", "/karriere"]),
    ("ARRI", "arri.com", ["/de/karriere", "/en/careers"]),
]

for name, dom, paths in TARGETS:
    found = None
    for path in paths + ["/karriere", "/jobs", "/careers"]:
        for base in (f"https://www.{dom}", f"https://{dom}"):
            url = base + path
            try:
                r = S.get(url, timeout=18, allow_redirects=True)
            except Exception:
                continue
            if r.status_code != 200:
                continue
            blob = r.text + " " + r.url
            for ats, pat in SIG:
                m = re.search(pat, blob, re.I)
                if m:
                    found = (ats, m.groups(), r.url[:70])
                    break
            if found:
                break
        if found:
            break
    if found:
        ats, groups, src = found
        print(f"✓ {name:<26} {ats:<16} {groups}")
        print(f"    发现于 {src}")
    else:
        print(f"· {name:<26} 未识别")
