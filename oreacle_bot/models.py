# src/models.py
from pydantic import BaseModel, Field
from typing import List, Literal, Optional

AllowedLabel = Literal["YES_CONDITION", "NO_CONDITION", "AMBIGUOUS", "IRRELEVANT"]

class Evidence(BaseModel):
    exact_zh_quote: str = Field(..., description="Exact Chinese clause")
    en_literal: str = Field(..., description="Literal EN translation of the same line")
    where_in_doc: str = Field(..., description="URL/section/anchor")

class Extraction(BaseModel):
    doc_url: str
    doc_title: Optional[str] = None
    mine_match: Literal["JIANXIAWO_MATCH", "POSSIBLE_MATCH", "NO_MATCH"]
    authority: Optional[str] = None
    key_terms_found_zh: List[str] = []
    key_terms_found_en: List[str] = []
    proposed_label: AllowedLabel
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[Evidence] = []
    hazards: List[str] = []
    