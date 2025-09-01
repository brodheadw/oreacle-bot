# src/comment_renderer.py
try:
    from .models import Extraction
except ImportError:
    from models import Extraction

def render_comment(x: Extraction, final_verdict: str) -> str:
    """Render a comprehensive comment for Manifold Markets"""
    
    # Primary evidence
    ev = x.evidence[0] if x.evidence else None
    zh = ev.exact_zh_quote if ev else "—"
    en = ev.en_literal if ev else "—"
    
    # Source info
    source_title = x.doc_title or "Regulatory Document"
    authority = x.authority or "Unknown Authority"
    
    # Confidence indicator
    confidence_emoji = "🟢" if x.confidence >= 0.8 else "🟡" if x.confidence >= 0.6 else "🔴"
    
    comment = f"""**🤖 Oreacle LLM Analysis** — {confidence_emoji} Confidence: {x.confidence:.1%}

📄 **Source**: [{source_title}]({x.doc_url})
🏛️ **Authority**: {authority}
⛏️ **Mine Match**: {x.mine_match}

**Key Evidence** (ZH→EN):
> 中文: 「{zh}」
> English: {en}

**LLM Verdict**: {x.proposed_label} → **Final: {final_verdict}**

**Terms Found**: 
- 🇨🇳 {', '.join(x.key_terms_found_zh[:5]) if x.key_terms_found_zh else 'None'}
- 🇬🇧 {', '.join(x.key_terms_found_en[:5]) if x.key_terms_found_en else 'None'}"""

    if x.hazards:
        comment += f"\n\n⚠️ **Risk Flags**: {', '.join(x.hazards)}"
    
    if len(x.evidence) > 1:
        comment += f"\n\n📋 **Additional Evidence**: {len(x.evidence)-1} more quotes available"
    
    comment += "\n\n*Automated analysis by Oreacle Bot*"
    
    return comment