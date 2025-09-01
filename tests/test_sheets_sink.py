"""
Tests for spreadsheet sink functionality.
"""

import pytest
import tempfile
import csv
import json
from pathlib import Path
from unittest.mock import Mock

from oreaclebot.sheets_sink import SpreadsheetSink, SpreadsheetRow
from oreaclebot.models import Extraction, Evidence


@pytest.fixture
def temp_csv_path():
    """Temporary CSV file path for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as f:
        temp_path = f.name
    # Remove the file so SpreadsheetSink can create it properly
    Path(temp_path).unlink(missing_ok=True) 
    yield temp_path
    # Cleanup after test
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture 
def spreadsheet_sink(temp_csv_path):
    """SpreadsheetSink instance with temporary file."""
    return SpreadsheetSink(output_path=temp_csv_path)


@pytest.fixture
def sample_extraction():
    """Sample extraction for testing."""
    return Extraction(
        doc_url="http://example.com/test-doc",
        doc_title="Test Mining Document",
        mine_match="JIANXIAWO_MATCH",
        proposed_label="YES_CONDITION",
        confidence=0.85,
        key_terms_found_zh=["采矿许可证延续", "批准"],
        key_terms_found_en=["mining license renewal", "approved"],
        evidence=[
            Evidence(
                exact_zh_quote="采矿许可证延续获得批准",
                en_literal="mining license renewal approved",
                where_in_doc="section 1"
            ),
            Evidence(
                exact_zh_quote="恢复生产",
                en_literal="resume production", 
                where_in_doc="section 2"
            )
        ]
    )


class TestSpreadsheetRow:
    """Test cases for SpreadsheetRow class."""
    
    def test_row_creation(self):
        """Test basic row creation."""
        row = SpreadsheetRow()
        
        assert row.doc_url == ""
        assert row.prob_delta == 0.0
        assert row.confidence == 0.0
        assert row.action_taken == "NONE"
        assert not row.comment_posted
        assert row.pnl_cumulative == 0.0
    
    def test_row_to_dict(self):
        """Test row serialization to dictionary."""
        row = SpreadsheetRow()
        row.doc_url = "http://example.com"
        row.confidence = 0.8
        row.action_taken = "COMMENT"
        
        row_dict = row.to_dict()
        
        assert isinstance(row_dict, dict)
        assert row_dict['doc_url'] == "http://example.com"
        assert row_dict['confidence'] == 0.8
        assert row_dict['action_taken'] == "COMMENT"
        assert 'timestamp' in row_dict
    
    def test_row_from_extraction(self, sample_extraction):
        """Test row creation from extraction."""
        row = SpreadsheetRow.from_extraction(
            sample_extraction, 
            "http://source.com", 
            "CNINFO"
        )
        
        assert row.doc_url == "http://source.com"
        assert row.doc_title == "Test Mining Document"
        assert row.source == "CNINFO"
        assert row.proposed_label == "YES_CONDITION"
        assert row.confidence == 0.85
        assert row.mine_match == "JIANXIAWO_MATCH"
        assert "采矿许可证延续获得批准" in row.zh_quote
        assert "mining license renewal approved" in row.en_literal


class TestSpreadsheetSink:
    """Test cases for SpreadsheetSink class."""
    
    def test_sink_initialization(self, temp_csv_path):
        """Test sink initialization creates CSV with headers."""
        sink = SpreadsheetSink(output_path=temp_csv_path)
        
        # Check file exists
        assert Path(temp_csv_path).exists()
        
        # Check headers are present
        with open(temp_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            
        expected_headers = ['timestamp', 'doc_url', 'confidence', 'final_verdict']
        for header in expected_headers:
            assert header in headers
    
    def test_append_row(self, spreadsheet_sink, temp_csv_path):
        """Test appending a row to the spreadsheet."""
        row = SpreadsheetRow()
        row.doc_url = "http://test.com"
        row.confidence = 0.9
        row.final_verdict = "YES"
        
        spreadsheet_sink.append_row(row)
        
        # Verify row was written
        with open(temp_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
        assert len(rows) == 1
        assert rows[0]['doc_url'] == "http://test.com"
        assert rows[0]['confidence'] == "0.9"
        assert rows[0]['final_verdict'] == "YES"
    
    def test_get_cumulative_pnl(self, spreadsheet_sink, temp_csv_path):
        """Test getting cumulative P&L from spreadsheet."""
        # Add some rows with different P&L values
        rows = [
            SpreadsheetRow(),
            SpreadsheetRow(),
            SpreadsheetRow()
        ]
        rows[0].pnl_cumulative = 10.0
        rows[1].pnl_cumulative = 25.0
        rows[2].pnl_cumulative = 30.0  # Most recent
        
        for row in rows:
            spreadsheet_sink.append_row(row)
        
        pnl = spreadsheet_sink.get_cumulative_pnl()
        assert pnl == 30.0
    
    def test_get_analysis_stats(self, spreadsheet_sink):
        """Test getting analysis statistics."""
        # Add sample rows with different labels
        rows = []
        for i, label in enumerate(['YES_CONDITION', 'NO_CONDITION', 'AMBIGUOUS', 'YES_CONDITION']):
            row = SpreadsheetRow()
            row.proposed_label = label
            row.confidence = 0.8
            row.comment_posted = i % 2 == 0  # Every other row has comment
            row.action_taken = "COMMENT" if i % 2 == 0 else "NONE"
            rows.append(row)
        
        for row in rows:
            spreadsheet_sink.append_row(row)
        
        stats = spreadsheet_sink.get_analysis_stats(days=7)
        
        assert stats['total_documents'] == 4
        assert stats['yes_conditions'] == 2
        assert stats['no_conditions'] == 1
        assert stats['comments_posted'] == 2
        assert stats['avg_confidence'] == 0.8
    
    def test_export_json(self, spreadsheet_sink, temp_csv_path):
        """Test exporting spreadsheet data to JSON."""
        # Add a sample row
        row = SpreadsheetRow()
        row.doc_url = "http://test.com"
        row.confidence = 0.9
        spreadsheet_sink.append_row(row)
        
        # Export to JSON
        json_path = spreadsheet_sink.export_json()
        
        # Verify JSON file exists and contains data
        assert Path(json_path).exists()
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert len(data) == 1
        assert data[0]['doc_url'] == "http://test.com"
        assert data[0]['confidence'] == "0.9"
        
        # Cleanup
        Path(json_path).unlink(missing_ok=True)


class TestGlobalSink:
    """Test cases for global sink functionality."""
    
    def test_get_global_sink(self):
        """Test getting global sink instance."""
        from oreaclebot.sheets_sink import get_global_sink
        
        sink1 = get_global_sink()
        sink2 = get_global_sink()
        
        # Should return same instance
        assert sink1 is sink2
    
    def test_log_analysis(self, sample_extraction):
        """Test convenience function for logging analysis."""
        from oreaclebot.sheets_sink import log_analysis, _global_sink
        
        # Reset global sink to None for clean test
        import oreaclebot.sheets_sink
        oreaclebot.sheets_sink._global_sink = None
        
        # Log analysis
        log_analysis(
            sample_extraction,
            "http://source.com",
            "CNINFO",
            action_taken="COMMENT",
            comment_posted=True
        )
        
        # Verify global sink was created and used
        assert oreaclebot.sheets_sink._global_sink is not None