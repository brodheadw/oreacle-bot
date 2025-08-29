# src/monitor.py
import os, time, logging
from typing import List
from client import ManifoldClient, Comment
from storage import Store, SeenItem
from translate import get_translator
from classify import classify_for_market
from sources.cninfo import fetch_cninfo
from sources.szse import fetch_szse
from sources.jiangxi import fetch_jiangxi

KEYWORDS_ZH = [
    "枧下窝", "宜春", "宜丰", "奉新", "采矿许可证", "采矿权", "探矿权", "延续", "续期", "换发", "恢复生产", "恢复开采"
]

LOG_LEVEL = os.environ.get("OREACLE_LOG", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="[%(asctime)s] %(levelname)s: %(message)s")

MANI_KEY = os.environ["MANIFOLD_API_KEY"]
MARKET_SLUG = os.environ["MARKET_SLUG"] # e.g., "MikhailTal/catl-receives-license-renewal-for-y"
COMMENT_ONLY = os.environ.get("OREACLE_COMMENT_ONLY", "1") == "1"

CHECK_INTERVAL_SEC = int(os.environ.get("OREACLE_INTERVAL", "900")) # 15 min default

def format_comment(item, en, zh, verdict):
    src = item["source"].upper()
    link = item.get("url") or ""
    title = (item.get("title") or "").strip()
    key = item.get("keyword")
    head = f"**{src} hit**: {title}\n\n"
    body = f"Chinese excerpt → English (auto):\n\n> {en[:500]}\n\nClassifier verdict: **{verdict.label}** — {verdict.reason}."
    foot = f"\n\n[Source link]({link}) | keyword: `{key}` | bot: Oreacle"
    return head + body + foot

def run_once():
    logging.info("Starting monitoring cycle...")
    store = Store()
    translator = get_translator()
    
    logging.info("Connecting to Manifold Markets...")
    mani = ManifoldClient(MANI_KEY)
    market = mani.get_market_by_slug(MARKET_SLUG)
    cid = market["id"]
    logging.info(f"Connected to market: {market.get('question', 'Unknown')}")

    items = []
    logging.info("Fetching from CNINFO...")
    try:
        cninfo_items = fetch_cninfo(KEYWORDS_ZH)
        items += cninfo_items
        logging.info(f"CNINFO: Found {len(cninfo_items)} items")
    except Exception as e:
        logging.error(f"CNINFO fetch failed: {e}")
    
    logging.info("Fetching from SZSE...")
    try:
        szse_items = fetch_szse(KEYWORDS_ZH)
        items += szse_items
        logging.info(f"SZSE: Found {len(szse_items)} items")
    except Exception as e:
        logging.error(f"SZSE fetch failed: {e}")
    
    logging.info("Fetching from Jiangxi...")
    try:
        jiangxi_items = fetch_jiangxi()
        items += jiangxi_items
        logging.info(f"Jiangxi: Found {len(jiangxi_items)} items")
    except Exception as e:
        logging.error(f"Jiangxi fetch failed: {e}")

    # Dedup & process
    new_items = [i for i in items if not store.has(i["source"], i["id"])]
    logging.info(f"Total: {len(items)} items, new: {len(new_items)}")
    
    if new_items:
        logging.info("New items found:")
        for item in new_items:
            logging.info(f"  {item['source']}: {item.get('title', 'No title')[:100]}")
    else:
        logging.info("No new items to process")

    for it in new_items:
        zh_text = (it.get("title") or "")
        en_text = translator.translate(zh_text)
        verdict = classify_for_market(en_text, zh_text)

        # Always post a comment when we see a strong YES/NO; otherwise, only note if highly relevant
        should_comment = verdict.label in {"YES_CONDITION", "NO_CONDITION"} or it["source"] != "jiangxi"

        if should_comment:
            md = format_comment(it, en_text, zh_text, verdict)
        try:
            mani.post_comment(Comment(contractId=cid, markdown=md))
            logging.info(f"Commented on {it['source']} {it['id']}")
        except Exception as e:
            logging.error(f"Failed to post comment: {e}")

        # Optional: trade logic (disabled by default)
        if not COMMENT_ONLY and verdict.label in {"YES_CONDITION", "NO_CONDITION"}:
            try:
                if verdict.label == "YES_CONDITION":
                    mani.place_limit_yes(cid, amount=5, limit_prob=0.55)
                else:
                    mani.place_limit_no(cid, amount=5, limit_prob=0.55)
            except Exception as e:
                logging.error(f"Failed to place order: {e}")

        # Mark as seen regardless to avoid spam
        store.add(SeenItem(it["source"], it["id"], it.get("url") or "", it.get("title") or "", int(time.time())))

def main():
    logging.info(f"Oreacle Bot starting up - monitoring every {CHECK_INTERVAL_SEC} seconds")
    logging.info(f"Target market: {MARKET_SLUG}")
    logging.info(f"Comment only mode: {COMMENT_ONLY}")
    logging.info(f"Keywords: {KEYWORDS_ZH}")
    
    while True:
        try:
            run_once()
        except Exception as e:
            logging.exception(f"run_once error: {e}")
        
        logging.info(f"Sleeping for {CHECK_INTERVAL_SEC} seconds until next cycle...")
        time.sleep(CHECK_INTERVAL_SEC)

if __name__ == "__main__":
    main()
