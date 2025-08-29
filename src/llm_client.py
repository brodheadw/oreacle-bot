# src/llm_client.py
import json
import os
from typing import Dict, Any
from openai import OpenAI
try:
    from .models import Extraction
except ImportError:
    from models import Extraction

CLIENT = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OREACLE_MODEL", "gpt-4o-mini")  # or "gpt-4.1"

EXTRACTION_SYSTEM = """You are a compliance-grade, extractive information extractor for Chinese regulatory documents about mining licenses.
Rules:
- Output ONLY valid JSON that matches the provided schema.
- Be EXTRACTIVE: include exact Chinese quotes for every claim.
- Do NOT infer 'production resumption' unless an explicit phrase appears.
- If exploration-only or unrelated mine/entity, label accordingly.
- Focus on the Jianxiawo/Yichun lithium mine specifically.
"""

EXTRACTION_USER_TMPL = """
SCHEMA: {schema}

ALLOWED YES PHRASES (ZH): {yes_zh}
ALLOWED YES PHRASES (EN): {yes_en}
ALLOWED NO PHRASES (ZH): {no_zh}
MINE CANONICAL NAMES: {mine_aliases}

DOC_URL: {url}

TEXT (Chinese or mixed):


{source_text}


Return JSON only.
"""

EXTRACTION_JSON_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "doc_url": {"type": "string"},
        "doc_title": {"type": ["string", "null"]},
        "mine_match": {"type": "string", "enum": ["JIANXIAWO_MATCH","POSSIBLE_MATCH","NO_MATCH"]},
        "authority": {"type": ["string","null"]},
        "key_terms_found_zh": {"type": "array", "items": {"type": "string"}},
        "key_terms_found_en": {"type": "array", "items": {"type": "string"}},
        "proposed_label": {"type": "string", "enum": ["YES_CONDITION","NO_CONDITION","AMBIGUOUS","IRRELEVANT"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "evidence": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "exact_zh_quote": {"type": "string"},
                    "en_literal": {"type": "string"},
                    "where_in_doc": {"type": "string"}
                },
                "required": ["exact_zh_quote","en_literal","where_in_doc"]
            }
        },
        "hazards": {"type":"array","items":{"type":"string"}}
    },
    "required": ["doc_url","mine_match","proposed_label","confidence","evidence",
                 "key_terms_found_zh","key_terms_found_en","hazards"]
}

def extract_from_text(source_text: str, url: str, phrasebook: Dict[str, Any]) -> Extraction:
    user = EXTRACTION_USER_TMPL.format(
        schema=json.dumps(EXTRACTION_JSON_SCHEMA, ensure_ascii=False),
        yes_zh=phrasebook["yes_zh"],
        yes_en=phrasebook["yes_en"],
        no_zh=phrasebook["no_zh"],
        mine_aliases=phrasebook["mine_aliases"],
        url=url,
        source_text=source_text
    )

    # Using Chat Completions with structured outputs
    resp = CLIENT.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "Extraction",
                "strict": True,
                "schema": EXTRACTION_JSON_SCHEMA
            }
        },
        messages=[
            {"role": "system", "content": EXTRACTION_SYSTEM},
            {"role": "user", "content": user},
        ],
    )

    content = resp.choices[0].message.content
    data = json.loads(content)  # guaranteed to obey the schema when strict JSON schema is used
    return Extraction.model_validate(data)