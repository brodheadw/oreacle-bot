# src/decision.py
import os
try:
    from .models import Extraction
except ImportError:
    from models import Extraction

MIN_CONF = float(os.getenv("OREACLE_MIN_CONFIDENCE", "0.75"))

YES_ZH = {"采矿许可证恢复","恢复生产","恢复开采","核发采矿许可证","延续","续期","换发"}
YES_EN = {"mining license renewed","resume production","resumption of mining","license renewal","permit renewal"}
NO_ZH = {"仅限勘探","探矿权","暂停生产","停止生产","责令停产"}
NO_EN = {"exploration only","exploration permit","suspend production","halt production"}

def passes_yes_gate(x: Extraction) -> bool:
    """Strict gate for YES decisions - requires high confidence and clear evidence"""
    if x.proposed_label != "YES_CONDITION": 
        return False
    if x.mine_match != "JIANXIAWO_MATCH": 
        return False
    if x.confidence < MIN_CONF:
        return False
    
    # Check for positive terms
    terms_en = {t.lower() for t in x.key_terms_found_en}
    terms_zh = set(x.key_terms_found_zh)
    has_yes = bool(YES_EN & terms_en) or bool(YES_ZH & terms_zh)
    
    # Must have actual evidence quote
    has_quote = any(e.exact_zh_quote.strip() for e in x.evidence)
    
    # Red flags that should block YES
    exploration_flag = any("exploration" in t.lower() for t in terms_en) or any("勘探" in t for t in terms_zh)
    no_flag = bool(NO_EN & terms_en) or bool(NO_ZH & terms_zh)
    
    return has_yes and has_quote and not exploration_flag and not no_flag

def passes_no_gate(x: Extraction) -> bool:
    """Gate for NO decisions"""
    if x.proposed_label != "NO_CONDITION":
        return False
    if x.mine_match == "NO_MATCH":
        return False
    
    terms_en = {t.lower() for t in x.key_terms_found_en}
    terms_zh = set(x.key_terms_found_zh)
    has_no = bool(NO_EN & terms_en) or bool(NO_ZH & terms_zh)
    
    return has_no and x.confidence >= MIN_CONF

def final_verdict(x: Extraction) -> str:
    """Conservative final decision with strict gates"""
    if passes_yes_gate(x): 
        return "YES_CONDITION"
    if passes_no_gate(x): 
        return "NO_CONDITION"
    return "AMBIGUOUS"