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
    import datetime as dt, logging
    start = (dt.datetime.utcnow() - dt.timedelta(days=days_back)).strftime("%Y-%m-%d")
    end = dt.datetime.utcnow().strftime("%Y-%m-%d")

    items = []
    
    # Method 1: Keyword-based search
    for kw in keywords:
        try:
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
        except Exception as e:
            logging.error(f"CNINFO keyword search failed for '{kw}': {e}")
    
    # Method 2: Stock code 300750 recent announcements (backup)
    try:
        payload = {
            "pageNum": 1,
            "pageSize": 50,  # Get more recent items
            "column": "szse",
            "tabName": "fulltext", 
            "plate": "",
            "stock": "300750",
            "searchkey": "",  # No keyword filter
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
        
        # Filter locally for relevance
        for a in ann:
            title = a.get("announcementTitle", "")
            # Quick relevance check for mining/lithium/Yichun terms
            relevant_terms = ["采矿", "锂", "宜春", "矿", "许可", "延续", "恢复", "生产"]
            if any(term in title for term in relevant_terms):
                url = a.get("adjunctUrl")
                if url and not url.startswith("http"):
                    url = f"http://static.cninfo.com.cn/{url.lstrip('/')}"
                
                # Avoid duplicates from keyword search
                item_id = a.get("announcementId") or a.get("id") or a.get("adjunctUrl")
                if not any(item["id"] == item_id for item in items):
                    items.append({
                        "source": "cninfo",
                        "id": item_id,
                        "title": title,
                        "time": a.get("announcementTime"),
                        "url": url,
                        "raw": a,
                        "keyword": "stock_sweep",
                    })
        
        logging.debug(f"CNINFO stock sweep found {len([i for i in items if i.get('keyword') == 'stock_sweep'])} additional items")
        
    except Exception as e:
        logging.error(f"CNINFO stock sweep failed: {e}")
    
    return items
