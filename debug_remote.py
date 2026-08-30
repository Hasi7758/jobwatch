#!/usr/bin/env python3
import re, requests, concurrent.futures as cf
S = requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0","Accept-Language":"de-DE,de;q=0.9"})

print("###### A. rodenstock.de 招聘列表页 ######")
for u in ["https://www.rodenstock.de/karriere/stellenanzeigen",
          "https://www.rodenstock.de/karriere-jobs",
          "https://www.rodenstock.de/de/de/wir-als-arbeitgeber.html"]:
    try:
        r = S.get(u, timeout=25, allow_redirects=True)
        print(f"{u[:58]:<60} HTTP {r.status_code} {len(r.text)}字节 -> {r.url[:60]}")
        if r.status_code == 200:
            ids = set(re.findall(r'hr4you[^"\']*id=(\d+)', r.text)) | set(re.findall(r'generator\.php\?id=(\d+)', r.text))
            print("   hr4you id:", sorted(ids)[:20], f"(共{len(ids)})")
            print("   iframe:", re.findall(r'<iframe[^>]*src="([^"]+)"', r.text)[:3])
            print("   (m/w/d):", re.findall(r'>([^<>]{6,90}\(m/w/d\))', r.text)[:6])
    except Exception as e:
        print(u[:58], type(e).__name__)

print("\n###### B. 扫 ID 段(generator.php?id=1900..2100) ######")
def probe(i):
    try:
        r = S.get(f"https://rodenstock.hr4you.org/generator.php?id={i}&changelanguage=de", timeout=12)
        if r.status_code != 200 or len(r.text) < 3000:
            return None
        r.encoding = "iso-8859-1"
        m = re.search(r"<title>(.*?)</title>", r.text, re.S)
        title = re.sub(r"\s+", " ", m.group(1)).strip() if m else ""
        if not title or "fehler" in title.lower() or len(title) < 6:
            return None
        loc = ""
        ml = re.search(r'CONTENT="[^"]*?,\s*([A-ZÄÖÜ][^",]{2,30}?)\s*,\s*[^"]*?"', r.text)
        mk = re.search(r'Keywords"\s*CONTENT="[^"]*?,\s*([^,"]{3,40}?)\s*,', r.text)
        return (i, title, (mk.group(1).strip() if mk else ""))
    except Exception:
        return None

hits = []
with cf.ThreadPoolExecutor(max_workers=12) as ex:
    for res in ex.map(probe, range(1900, 2101)):
        if res: hits.append(res)
print(f"命中 {len(hits)} 个有效职位:")
for i, t, loc in sorted(hits):
    print(f"   id={i}  {t[:70]}")
