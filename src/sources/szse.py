# src/szse.py
import requests, random, time
from typing import List, Dict

SZSE_URL = "http://www.szse.cn/api/disc/announcement/annList"
SZSE_HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/json",
    "Origin": "http://www.szse.cn",
    "Referer": "http://www.szse.cn/disclosure/listed/notice/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}

def fetch_szse(keywords: List[str], days_back: int = 90) -> List[Dict]:
    import datetime as dt
    start = (dt.datetime.utcnow() - dt.timedelta(days=days_back)).strftime("%Y-%m-%d")
    end = dt.datetime.utcnow().strftime("%Y-%m-%d")

    results = []
    for kw in keywords:
        body = {
            "seDate": f"{start}~{end}",
            "channelCode": ["listedNotice_disc"],
            "pageSize": 30,
            "pageNum": 1,
            "keyword": kw,
            "plateCode": ["szse"],
            "secCode": ["300750"],
        }
    r = requests.post(f"{SZSE_URL}?random={random.random()}", headers=SZSE_HEADERS, json=body, timeout=20)
    r.raise_for_status(); data = r.json()
    for a in data.get("data", {}).get("announcements", []):
        url = a.get("attachPath")
    if url and not url.startswith("http"):
        url = f"http://disc.static.szse.cn/download/{url.lstrip('/')}"
    results.append({
        "source": "szse",
        "id": a.get("id") or a.get("seqId") or a.get("attachPath"),
        "title": a.get("title"),
        "time": a.get("publishTime"),
        "url": url,
        "raw": a,
        "keyword": kw,
    })
    time.sleep(0.8)
    return results