# src/prefilter.py
import re
from typing import Dict, Any, List

def passes_boolean_filter(text: str, phrasebook: Dict[str, Any]) -> bool:
    """
    Tighter boolean filter: requires (entity OR geo) AND (license-action OR resumption verb)
    Reduces noise by ensuring relevance before expensive LLM analysis.
    """
    text_lower = text.lower()
    
    # Check for entity match (company, mine, or geo)
    entity_match = False
    for category in ['company_aliases', 'mine_aliases', 'geo_aliases']:
        if category in phrasebook:
            for alias in phrasebook[category]:
                if alias.lower() in text_lower:
                    entity_match = True
                    break
        if entity_match:
            break
    
    # Check for action match (license actions or resumption verbs)
    action_match = False
    for category in ['yes_zh', 'yes_en', 'no_zh', 'traditional_zh']:
        if category in phrasebook:
            for term in phrasebook[category]:
                if term.lower() in text_lower:
                    action_match = True
                    break
        if action_match:
            break
    
    return entity_match and action_match

def fuzzy_mine_match(text: str) -> bool:
    """
    Check for fuzzy variants of Jianxiawo (typos, transliterations)
    Returns True if likely mining-related Jianxiawo variant detected
    """
    text_lower = text.lower()
    
    # Direct Latin variants
    latin_variants = ['jianxiawo', 'jianxia wo', 'jian xia wo']
    if any(variant in text_lower for variant in latin_variants):
        return True
    
    # Check for mining context with potential typos
    mining_terms = ['mining', '采矿', '矿', 'lithium', '锂', 'mine']
    has_mining = any(term in text_lower for term in mining_terms)
    
    if has_mining:
        # 2-char edit distance variants (simplified check)
        typo_variants = ['建夏沃', '建夏窝', '涧下窝']
        if any(variant in text for variant in typo_variants):
            return True
    
    return False

def enhanced_relevance_check(item: Dict[str, Any], phrasebook: Dict[str, Any]) -> bool:
    """
    Enhanced relevance check combining boolean filter and fuzzy matching
    """
    title = item.get('title', '')
    
    # Primary filter
    if passes_boolean_filter(title, phrasebook):
        return True
    
    # Fuzzy mine matching as backup
    if fuzzy_mine_match(title):
        return True
    
    return False