# src/cninfo.py
import requests, time
from typing import List, Dict

HEADERS = {
"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0 Safari/537.36",
"Origin": "http://www.cninfo.com.cn",
"Referer": "http://www.cninfo.com.cn/",
}

CNINFO_URL = "http://www.cninfo.com.cn/new/hisAnnouncement/query"

# CATL stock code: 300750 (SZ), search by searchkey w Chinese terms

def fetch_cninfo(keywords: List[str], days_back: int = 90) -> List[Dict]:
    import datetime as dt
    start = (dt.datetime.utcnow() - dt.timedelta(days=days_back)).strftime("%Y-%m-%d")
    end = dt.datetime.utcnow().strftime("%Y-%m-%d")

    items = []
    for kw in keywords:
        payload = {
            "pageNum": 1,
            "pageSize": 30,
            "column": "szse", # deep-SZ column
            "tabName": "fulltext",
            "plate": "",
            "stock": "300750", # CATL
            "searchkey": kw,
            "secid": "",
            "category": "",
            "trade": "",
            "seDate": f"{start}~{end}",
            "sortName": "time",
            "sortType": "desc",
            "isHLtitle": "true",
        }

        r = requests.post(CNINFO_URL, headers=HEADERS, data=payload, timeout=20)
        r.raise_for_status()
        data = r.json()
        ann = data.get("announcements", []) or []
        for a in ann:
            url = a.get("adjunctUrl")
            if url and not url.startswith("http"):
                url = f"http://static.cninfo.com.cn/{url.lstrip('/')}"
            items.append({
                "source": "cninfo",
                "id": a.get("announcementId") or a.get("id") or a.get("adjunctUrl"),
                "title": a.get("announcementTitle"),
                "time": a.get("announcementTime"),
                "url": url,
                "raw": a,
                "keyword": kw,
            })
        time.sleep(0.8)
    return items