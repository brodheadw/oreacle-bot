# src/szse.py
import requests, random, time
from typing import List, Dict

SZSE_URL = "https://www.szse.cn/api/disc/announcement/annList"
SZSE_HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Content-Type": "application/json",
    "Origin": "https://www.szse.cn",
    "Referer": "https://www.szse.cn/disclosure/listed/notice/",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}

def fetch_szse(keywords: List[str], days_back: int = 90) -> List[Dict]:
    import datetime as dt, logging
    start = (dt.datetime.utcnow() - dt.timedelta(days=days_back)).strftime("%Y-%m-%d")
    end = dt.datetime.utcnow().strftime("%Y-%m-%d")

    results = []
    for kw in keywords:
        try:
            body = {
                "seDate": f"{start}~{end}",
                "channelCode": ["listedNotice_disc"],
                "pageSize": 30,
                "pageNum": 1,
                "keyword": kw,
                "plateCode": ["szse"],
                "secCode": ["300750"],
            }
            
            url = f"{SZSE_URL}?random={random.random()}"
            logging.debug(f"SZSE request URL: {url}")
            logging.debug(f"SZSE request body: {body}")
            
            r = requests.post(url, headers=SZSE_HEADERS, json=body, timeout=20)
            logging.debug(f"SZSE response status: {r.status_code}")
            logging.debug(f"SZSE response headers: {dict(r.headers)}")
            
            r.raise_for_status()
            
            # Check if response has content before parsing JSON
            if not r.text.strip():
                logging.warning(f"SZSE returned empty response for keyword: {kw}")
                continue
                
            try:
                data = r.json()
                logging.debug(f"SZSE JSON response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            except ValueError as e:
                # Check if it's HTML (maintenance page or server error)
                if r.text.strip().startswith('<!DOCTYPE html>') or r.text.strip().startswith('<html'):
                    if '50x' in r.text or 'maintain' in r.text.lower():
                        logging.warning(f"SZSE API appears to be down (50x error or maintenance) for keyword '{kw}'")
                    else:
                        logging.warning(f"SZSE returned HTML page for keyword '{kw}' - possibly blocked")
                    logging.debug(f"First 200 chars: {r.text[:200]}")
                else:
                    logging.warning(f"SZSE returned invalid JSON for keyword '{kw}': {r.text[:100]}...")
                continue
            
            announcements = data.get("data", {}).get("announcements", []) if isinstance(data, dict) else []
            
            for a in announcements:
                url = a.get("attachPath", "")
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
            
        except Exception as e:
            logging.error(f"SZSE fetch failed for keyword '{kw}': {e}")
            continue
            
    return results