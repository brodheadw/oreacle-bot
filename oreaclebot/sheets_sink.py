"""
Spreadsheet sink for comprehensive Oreacle Bot analysis logging.

Tracks all analysis results in a structured format for audit, debugging, and performance analysis.
Supports Google Sheets API integration with comprehensive data logging.
"""

import logging
import csv
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

from .models import Extraction, Evidence


class SpreadsheetRow:
    """Represents a single row of analysis data."""
    
    def __init__(self):
        self.timestamp = datetime.now(timezone.utc)
        self.doc_url = ""
        self.doc_title = ""
        self.source = ""  # CNINFO, SZSE, Jiangxi
        
        # Market probabilities
        self.prob_before = 0.0
        self.prob_after = 0.0
        self.prob_delta = 0.0
        
        # Ladder probabilities (for monotonicity check)
        self.ladder_probs = []  # List of related market probabilities
        self.hazard_rate = 0.0  # Instantaneous probability change
        
        # LLM analysis results
        self.zh_quote = ""
        self.en_literal = ""
        self.proposed_label = ""
        self.confidence = 0.0
        self.mine_match = ""
        self.authority = ""
        self.key_terms_zh = []
        self.key_terms_en = []
        self.hazards = []
        
        # Decision pipeline
        self.passes_prefilter = False
        self.passes_yes_gate = False
        self.passes_no_gate = False
        self.final_verdict = ""
        
        # Actions taken
        self.action_taken = "NONE"  # COMMENT, TRADE_YES, TRADE_NO, NONE
        self.comment_posted = False
        self.trade_amount = 0
        self.trade_outcome = ""
        
        # Performance tracking
        self.pnl_this_action = 0.0
        self.pnl_cumulative = 0.0
        self.execution_time_ms = 0
        self.llm_tokens_used = 0
        self.llm_cost_usd = 0.0
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert row to dictionary for CSV/JSON serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'doc_url': self.doc_url,
            'doc_title': self.doc_title,
            'source': self.source,
            'prob_before': self.prob_before,
            'prob_after': self.prob_after,
            'prob_delta': self.prob_delta,
            'ladder_probs': json.dumps(self.ladder_probs),
            'hazard_rate': self.hazard_rate,
            'zh_quote': self.zh_quote,
            'en_literal': self.en_literal,
            'proposed_label': self.proposed_label,
            'confidence': self.confidence,
            'mine_match': self.mine_match,
            'authority': self.authority,
            'key_terms_zh': json.dumps(self.key_terms_zh),
            'key_terms_en': json.dumps(self.key_terms_en),
            'hazards': json.dumps(self.hazards),
            'passes_prefilter': self.passes_prefilter,
            'passes_yes_gate': self.passes_yes_gate,
            'passes_no_gate': self.passes_no_gate,
            'final_verdict': self.final_verdict,
            'action_taken': self.action_taken,
            'comment_posted': self.comment_posted,
            'trade_amount': self.trade_amount,
            'trade_outcome': self.trade_outcome,
            'pnl_this_action': self.pnl_this_action,
            'pnl_cumulative': self.pnl_cumulative,
            'execution_time_ms': self.execution_time_ms,
            'llm_tokens_used': self.llm_tokens_used,
            'llm_cost_usd': self.llm_cost_usd,
        }
    
    @classmethod
    def from_extraction(cls, extraction: Extraction, doc_url: str, source: str) -> 'SpreadsheetRow':
        """Create SpreadsheetRow from LLM extraction results."""
        row = cls()
        row.doc_url = doc_url
        row.doc_title = extraction.doc_title or ""
        row.source = source
        row.proposed_label = extraction.proposed_label
        row.confidence = extraction.confidence
        row.mine_match = extraction.mine_match
        row.authority = extraction.authority or ""
        row.key_terms_zh = extraction.key_terms_found_zh
        row.key_terms_en = extraction.key_terms_found_en
        row.hazards = extraction.hazards
        
        # Combine evidence quotes
        if extraction.evidence:
            zh_quotes = [ev.exact_zh_quote for ev in extraction.evidence]
            en_quotes = [ev.en_literal for ev in extraction.evidence]
            row.zh_quote = " | ".join(zh_quotes[:3])  # First 3 quotes
            row.en_literal = " | ".join(en_quotes[:3])
        
        return row


class SpreadsheetSink:
    """
    Manages structured logging of Oreacle Bot analysis to spreadsheet formats.
    
    Supports both local CSV files and Google Sheets integration.
    """
    
    def __init__(self, output_path: str = "./tmp/oreacle_analysis.csv", 
                 sheets_config: Optional[Dict] = None):
        """
        Initialize spreadsheet sink.
        
        Args:
            output_path: Local CSV file path
            sheets_config: Google Sheets API configuration (optional)
        """
        self.output_path = Path(output_path)
        self.sheets_config = sheets_config
        self.logger = logging.getLogger(__name__)
        
        # Ensure output directory exists
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize CSV with headers if file doesn't exist
        if not self.output_path.exists():
            self._initialize_csv()
    
    def _initialize_csv(self):
        """Initialize CSV file with headers."""
        headers = [
            'timestamp', 'doc_url', 'doc_title', 'source',
            'prob_before', 'prob_after', 'prob_delta', 'ladder_probs', 'hazard_rate',
            'zh_quote', 'en_literal', 'proposed_label', 'confidence',
            'mine_match', 'authority', 'key_terms_zh', 'key_terms_en', 'hazards',
            'passes_prefilter', 'passes_yes_gate', 'passes_no_gate', 'final_verdict',
            'action_taken', 'comment_posted', 'trade_amount', 'trade_outcome',
            'pnl_this_action', 'pnl_cumulative', 'execution_time_ms',
            'llm_tokens_used', 'llm_cost_usd'
        ]
        
        try:
            with open(self.output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            self.logger.info(f"Initialized CSV file at {self.output_path}")
        except Exception as e:
            self.logger.error(f"Failed to initialize CSV file: {e}")
    
    def append_row(self, row: SpreadsheetRow):
        """
        Append a new analysis row to the spreadsheet.
        
        Args:
            row: SpreadsheetRow to append
        """
        try:
            # Append to local CSV
            self._append_to_csv(row)
            
            # Append to Google Sheets if configured
            if self.sheets_config:
                self._append_to_sheets(row)
                
        except Exception as e:
            self.logger.error(f"Failed to append row to spreadsheet: {e}")
    
    def _append_to_csv(self, row: SpreadsheetRow):
        """Append row to local CSV file."""
        row_dict = row.to_dict()
        
        with open(self.output_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=row_dict.keys())
            writer.writerow(row_dict)
    
    def _append_to_sheets(self, row: SpreadsheetRow):
        """Append row to Google Sheets (placeholder for future implementation)."""
        # TODO: Implement Google Sheets API integration
        self.logger.debug("Google Sheets integration not implemented yet")
    
    def get_cumulative_pnl(self) -> float:
        """Get cumulative P&L from the spreadsheet."""
        try:
            if not self.output_path.exists():
                return 0.0
                
            with open(self.output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            if not rows:
                return 0.0
                
            # Return the most recent cumulative P&L
            return float(rows[-1].get('pnl_cumulative', 0.0))
            
        except Exception as e:
            self.logger.error(f"Failed to get cumulative P&L: {e}")
            return 0.0
    
    def get_analysis_stats(self, days: int = 7) -> Dict[str, Any]:
        """
        Get analysis statistics for the past N days.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with analysis statistics
        """
        try:
            if not self.output_path.exists():
                return {}
                
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            with open(self.output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                recent_rows = []
                
                for row in reader:
                    try:
                        row_date = datetime.fromisoformat(row['timestamp'])
                        if row_date >= cutoff_date:
                            recent_rows.append(row)
                    except (ValueError, KeyError):
                        continue
            
            if not recent_rows:
                return {}
            
            # Calculate statistics
            total_docs = len(recent_rows)
            yes_conditions = len([r for r in recent_rows if r['proposed_label'] == 'YES_CONDITION'])
            no_conditions = len([r for r in recent_rows if r['proposed_label'] == 'NO_CONDITION'])
            comments_posted = len([r for r in recent_rows if r['comment_posted'] == 'True'])
            trades_made = len([r for r in recent_rows if r['action_taken'] in ['TRADE_YES', 'TRADE_NO']])
            
            avg_confidence = 0.0
            if recent_rows:
                confidences = [float(r.get('confidence', 0)) for r in recent_rows]
                avg_confidence = sum(confidences) / len(confidences)
            
            total_pnl = sum(float(r.get('pnl_this_action', 0)) for r in recent_rows)
            
            return {
                'days_analyzed': days,
                'total_documents': total_docs,
                'yes_conditions': yes_conditions,
                'no_conditions': no_conditions,
                'comments_posted': comments_posted,
                'trades_made': trades_made,
                'avg_confidence': avg_confidence,
                'total_pnl': total_pnl,
                'docs_per_day': total_docs / max(days, 1)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get analysis stats: {e}")
            return {}
    
    def export_json(self, output_path: Optional[str] = None) -> str:
        """
        Export spreadsheet data to JSON format.
        
        Args:
            output_path: Output JSON file path (optional)
            
        Returns:
            Path to exported JSON file
        """
        if output_path is None:
            output_path = str(self.output_path).replace('.csv', '.json')
            
        try:
            with open(self.output_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                data = list(reader)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Exported {len(data)} rows to {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to export JSON: {e}")
            raise


# Global instance for easy access
_global_sink: Optional[SpreadsheetSink] = None


def get_global_sink() -> SpreadsheetSink:
    """Get or create global spreadsheet sink instance."""
    global _global_sink
    if _global_sink is None:
        _global_sink = SpreadsheetSink()
    return _global_sink


def log_analysis(extraction: Extraction, doc_url: str, source: str, **kwargs) -> None:
    """
    Convenience function to log analysis results to global spreadsheet sink.
    
    Args:
        extraction: LLM extraction results
        doc_url: Source document URL
        source: Source name (CNINFO, SZSE, Jiangxi)
        **kwargs: Additional fields to set on SpreadsheetRow
    """
    sink = get_global_sink()
    row = SpreadsheetRow.from_extraction(extraction, doc_url, source)
    
    # Set additional fields from kwargs
    for key, value in kwargs.items():
        if hasattr(row, key):
            setattr(row, key, value)
    
    sink.append_row(row)