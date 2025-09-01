"""
Oreacle Bot - A monitoring bot that tracks Chinese regulatory sources for CATL lithium mine license updates.

This package provides tools for monitoring Chinese regulatory sources and automatically posting
analysis to Manifold Markets.
"""

__version__ = "1.0.0"
__author__ = "Oreacle Bot Team"

# Import main components for easy access
from .client import ManifoldClient, LimitOrder, Comment, Outcome
from .models import Extraction, Evidence
from .llm_client import extract_from_text
from .decision import final_verdict, passes_yes_gate, passes_no_gate

__all__ = [
    "ManifoldClient",
    "LimitOrder", 
    "Comment",
    "Outcome",
    "Extraction",
    "Evidence",
    "extract_from_text",
    "final_verdict",
    "passes_yes_gate",
    "passes_no_gate",
]
