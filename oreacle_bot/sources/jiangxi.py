# src/jiangxi.py
import requests, re
from typing import List, Dict
from html import unescape

# Natural Resources Dept. (Jiangxi) top site and mining-rights announcement sections
INDEXES = [
    "https://bnr.jiangxi.gov.cn/jxszrzyt/kyqjygggs/kyqjygsg/", # 探矿权交易公告/公示
    "https://bnr.jiangxi.gov.cn/jxszrzyt/ckqcrgggs/ckqcrgsg/", # 采矿权出让公告/公示
    "https://www.yichun.gov.cn/ycsrmzf/gytdsyqhkyqcr/" # 宜春市出让专栏
]

PATTERNS = [r"宜春|宜丰|奉新|袁州", r"锂|云母|陶瓷土", r"采矿权|探矿权|挂牌|出让|续期|延续|换发|复产|恢复生产"]

A_RE = re.compile(r"<a[^>]+href=\"(?P<href>[^\"]+)\"[^>]*>(?P<title>.*?)</a>", re.I|re.S)

def fetch_jiangxi(max_pages: int = 1) -> List[Dict]:
    out = []
    for base in INDEXES:
        try:
            r = requests.get(base, timeout=20)
            r.raise_for_status()
            html = r.text
            for m in A_RE.finditer(html):
                href, title = unescape(m.group("href")), unescape(m.group("title"))
                title_plain = re.sub(r"<[^>]+>", "", title)
                if not all(re.search(p, title_plain) for p in PATTERNS[:1]): # requires region hint
                    continue
                url = href if href.startswith("http") else requests.compat.urljoin(base, href)
                out.append({
                    "source": "jiangxi",
                    "id": url, # pages usually unique
                    "title": title_plain.strip(),
                    "time": None,
                    "url": url,
                    "raw": {"base": base},
                    "keyword": None,
                })
        except Exception:
            continue
    return out
