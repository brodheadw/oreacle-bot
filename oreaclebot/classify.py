# src/classify.py
import re
from dataclasses import dataclass

@dataclass
class Verdict:
    label: str # "YES_CONDITION", "NO_CONDITION", "IRRELEVANT", "AMBIGUOUS"
    reason: str

YES_PATTERNS = [
    r"许可(证)?(延续|续期|换发)",
    r"恢复(生产|开采|采矿)",
    r"准予(生产|开采)",
]
NO_PATTERNS = [
    r"(仅|只|限)勘(探|查)",
    r"责令停产|暂停开采|停止生产",
    r"行政处罚|吊销采矿许可证",
]

JIANXIAWO_HINTS = [r"枧下窝", r"Jianxiawo", r"宜丰", r"奉新", r"宜春", r"江西"]

def classify_for_market(en_text: str, zh_text: str) -> Verdict:
    """Very simple first pass: regex on Chinese + English snippets.
    Return conservative labels so we don't trade on weak signals.
    """
    text = f"{en_text}\n{zh_text}".lower()
    if not any(re.search(h, text, re.I) for h in JIANXIAWO_HINTS):
        return Verdict("IRRELEVANT", "No Yichun/Jianxiawo/region hints found")

    for p in YES_PATTERNS:
        if re.search(p, zh_text):
            return Verdict("YES_CONDITION", f"Matched YES pattern: /{p}/")

    for p in NO_PATTERNS:
        if re.search(p, zh_text):
            return Verdict("NO_CONDITION", f"Matched NO pattern: /{p}/")

    return Verdict("AMBIGUOUS", "Mentions region but not license/production status keywords")
