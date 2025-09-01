"""
Oreacle Bot - A monitoring bot that tracks Chinese regulatory sources for CATL lithium mine license updates.

This package provides tools for monitoring Chinese regulatory sources and automatically posting
analysis to Manifold Markets.
"""

__version__ = "1.0.0"
__author__ = "Oreacle Bot Team"

# Core data models
from .models import Extraction, Evidence

# Manifold client and types
from .client import ManifoldClient, LimitOrder, Comment, Outcome

# LLM integration
from .llm_client import extract_from_text

# Decision pipeline
from .decision import final_verdict, passes_yes_gate, passes_no_gate

# Prefiltering
from .prefilter import passes_boolean_filter, fuzzy_mine_match, enhanced_relevance_check

# New modules
from .ladder import LadderMonotonicity, LadderViolation
from .sheets_sink import SpreadsheetSink, SpreadsheetRow, log_analysis

# Import monitor functions
from .monitor import main as monitor_main, run_once as monitor_run_once

# Make submodules available
from . import sentinels
from . import sources

__all__ = [
    # Version info
    "__version__",
    "__author__",
    
    # Core models
    "Extraction",
    "Evidence",
    
    # Manifold integration
    "ManifoldClient",
    "LimitOrder", 
    "Comment",
    "Outcome",
    
    # LLM integration
    "extract_from_text",
    
    # Decision pipeline
    "final_verdict",
    "passes_yes_gate",
    "passes_no_gate",
    
    # Prefiltering
    "passes_boolean_filter",
    "fuzzy_mine_match",
    "enhanced_relevance_check",
    
    # Ladder monotonicity
    "LadderMonotonicity",
    "LadderViolation",
    
    # Spreadsheet logging
    "SpreadsheetSink",
    "SpreadsheetRow", 
    "log_analysis",
    
    # Monitor functions
    "monitor_main",
    "monitor_run_once",
    
    # Submodules
    "sentinels",
    "sources",
]
