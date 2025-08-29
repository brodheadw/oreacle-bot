# src/monitor.py
import os, time, logging, yaml
from typing import List
from client import ManifoldClient, Comment
from storage import Store, SeenItem
from translate import get_translator
from classify import classify_for_market
from sources.cninfo import fetch_cninfo
from sources.szse import fetch_szse
from sources.jiangxi import fetch_jiangxi

# LLM Integration
from llm_client import extract_from_text
from decision import final_verdict, passes_yes_gate
from comment_renderer import render_comment
from prefilter import enhanced_relevance_check

KEYWORDS_ZH = [
    "枧下窝", "宜春", "宜丰", "奉新", "采矿许可证", "采矿权", "探矿权", "延续", "续期", "换发", "恢复生产", "恢复开采"
]

LOG_LEVEL = os.environ.get("OREACLE_LOG", "INFO").upper()
logging.basicConfig(level=LOG_LEVEL, format="[%(asctime)s] %(levelname)s: %(message)s")

MANI_KEY = os.environ["MANIFOLD_API_KEY"]
MARKET_SLUG = os.environ["MARKET_SLUG"] # e.g., "MikhailTal/catl-receives-license-renewal-for-y"
COMMENT_ONLY = os.environ.get("OREACLE_COMMENT_ONLY", "1") == "1"
USE_LLM = os.environ.get("OPENAI_API_KEY") is not None

CHECK_INTERVAL_SEC = int(os.environ.get("OREACLE_INTERVAL", "900")) # 15 min default

# Load phrasebook once at startup
try:
    with open("phrasebook.yml", "r", encoding="utf-8") as f:
        PHRASEBOOK = yaml.safe_load(f)
    logging.info("Loaded phrasebook configuration")
except Exception as e:
    logging.warning(f"Failed to load phrasebook.yml: {e}")
    PHRASEBOOK = {"yes_zh": [], "yes_en": [], "no_zh": [], "mine_aliases": []}

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
        url = it.get("url") or ""
        
        logging.info(f"Processing {it['source']} item: {zh_text[:100]}...")
        
        try:
            if USE_LLM:
                # LLM Analysis Pipeline
                logging.info("Running LLM extraction...")
                extraction = extract_from_text(zh_text, url, PHRASEBOOK)
                verdict = final_verdict(extraction)
                
                logging.info(f"LLM Analysis - Proposed: {extraction.proposed_label}, Final: {verdict}, Confidence: {extraction.confidence:.2f}")
                
                # Generate comment using LLM analysis
                should_comment = verdict in {"YES_CONDITION", "NO_CONDITION"} or extraction.mine_match != "NO_MATCH"
                
                if should_comment:
                    md = render_comment(extraction, verdict)
                    try:
                        mani.post_comment(Comment(contractId=cid, markdown=md))
                        logging.info(f"Posted LLM comment for {it['source']} {it['id']}")
                    except Exception as e:
                        logging.error(f"Failed to post LLM comment: {e}")
                
                # Trading logic (only with strict LLM gate)
                if not COMMENT_ONLY:
                    if passes_yes_gate(extraction):
                        try:
                            mani.place_limit_yes(cid, amount=5, limit_prob=0.55)
                            logging.info(f"Placed YES order based on LLM analysis")
                        except Exception as e:
                            logging.error(f"Failed to place YES order: {e}")
                    elif verdict == "NO_CONDITION" and extraction.confidence >= 0.8:
                        try:
                            mani.place_limit_no(cid, amount=5, limit_prob=0.45)
                            logging.info(f"Placed NO order based on LLM analysis")
                        except Exception as e:
                            logging.error(f"Failed to place NO order: {e}")
            
            else:
                # Fallback to old classification system
                logging.info("Using fallback regex classification (no LLM)")
                en_text = translator.translate(zh_text)
                verdict_old = classify_for_market(en_text, zh_text)
                
                should_comment = verdict_old.label in {"YES_CONDITION", "NO_CONDITION"} or it["source"] != "jiangxi"
                
                if should_comment:
                    md = format_comment(it, en_text, zh_text, verdict_old)
                    try:
                        mani.post_comment(Comment(contractId=cid, markdown=md))
                        logging.info(f"Posted fallback comment for {it['source']} {it['id']}")
                    except Exception as e:
                        logging.error(f"Failed to post fallback comment: {e}")
        
        except Exception as e:
            logging.error(f"Failed to process item {it['source']} {it['id']}: {e}")
        
        # Mark as seen regardless to avoid spam
        store.add(SeenItem(it["source"], it["id"], it.get("url") or "", it.get("title") or "", int(time.time())))

def main():
    logging.info(f"Oreacle Bot starting up - monitoring every {CHECK_INTERVAL_SEC} seconds")
    logging.info(f"Target market: {MARKET_SLUG}")
    logging.info(f"Comment only mode: {COMMENT_ONLY}")
    logging.info(f"LLM integration: {'ENABLED' if USE_LLM else 'DISABLED (no OpenAI API key)'}")
    if USE_LLM:
        model = os.getenv("OREACLE_MODEL", "gpt-4o-mini")
        min_conf = os.getenv("OREACLE_MIN_CONFIDENCE", "0.75")
        logging.info(f"LLM model: {model}, min confidence: {min_conf}")
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
