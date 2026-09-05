#!/usr/bin/env python3
import requests, json
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 Chrome/124.0","Accept":"application/json"})
API="https://fa-esta-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
def go(label, finder, extra=None):
    p={"onlyData":"true","finder":finder}
    if extra: p.update(extra)
    try:
        r=S.get(API,params=p,timeout=30)
        if r.status_code!=200:
            print(f"  ✗ {label:<44} HTTP {r.status_code} {r.text[:110]}"); return None
        blk=(r.json().get("items") or [{}])[0]
        it=blk.get("requisitionList") or []
        sg=[j for j in it if "singapore" in str(j.get("PrimaryLocation","")).lower()]
        print(f"  ✓ {label:<44} 返回{len(it):>3} 总数={blk.get('TotalJobsCount')} 新加坡={len(sg)}")
        for j in sg[:4]: print(f"        · {str(j.get('Title'))[:50]:<52} {j.get('PostedDate')}")
        return it
    except Exception as e:
        print(f"  ✗ {label:<44} {type(e).__name__}"); return None

print("### 找对的地点过滤写法 ###")
go("无过滤", "findReqs;siteNumber=CX_1001,limit=50,sortBy=POSTING_DATES_DESC")
go("offset独立", "findReqs;siteNumber=CX_1001,limit=50,sortBy=POSTING_DATES_DESC", {"offset":50})
go("locationId", "findReqs;siteNumber=CX_1001,limit=50,locationId=300000000440956,locationLevel=country,sortBy=POSTING_DATES_DESC")
go("selectedLocationsFacet", "findReqs;siteNumber=CX_1001,limit=50,selectedLocationsFacet=300000000440956,sortBy=POSTING_DATES_DESC")
go("keyword Singapore", "findReqs;siteNumber=CX_1001,limit=50,keyword=Singapore,sortBy=POSTING_DATES_DESC")
go("limit200 无过滤", "findReqs;siteNumber=CX_1001,limit=200,sortBy=POSTING_DATES_DESC")
