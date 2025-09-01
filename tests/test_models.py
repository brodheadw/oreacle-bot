"""
Tests for Pydantic models.
"""

import pytest
from oreaclebot.models import Extraction, Evidence


class TestEvidence:
    """Test cases for Evidence model."""
    
    def test_evidence_creation(self):
        """Test evidence creation with required fields."""
        evidence = Evidence(
            exact_zh_quote="采矿许可证延续",
            en_literal="mining license renewal",
            where_in_doc="main announcement"
        )
        
        assert evidence.exact_zh_quote == "采矿许可证延续"
        assert evidence.en_literal == "mining license renewal"
        assert evidence.where_in_doc == "main announcement"
    
    def test_evidence_validation_missing_fields(self):
        """Test evidence validation with missing required fields."""
        with pytest.raises(ValueError):
            Evidence(
                exact_zh_quote="采矿许可证延续",
                # Missing en_literal and where_in_doc
            )


class TestExtraction:
    """Test cases for Extraction model."""
    
    def test_extraction_creation_minimal(self):
        """Test extraction creation with minimal required fields."""
        extraction = Extraction(
            doc_url="https://example.com/doc",
            mine_match="JIANXIAWO_MATCH",
            proposed_label="YES_CONDITION",
            confidence=0.8,
            evidence=[],
            key_terms_found_zh=[],
            key_terms_found_en=[],
            hazards=[]
        )
        
        assert extraction.doc_url == "https://example.com/doc"
        assert extraction.mine_match == "JIANXIAWO_MATCH"
        assert extraction.proposed_label == "YES_CONDITION"
        assert extraction.confidence == 0.8
        assert extraction.evidence == []
        assert extraction.doc_title is None
        assert extraction.authority is None
    
    def test_extraction_creation_full(self):
        """Test extraction creation with all fields."""
        evidence = Evidence(
            exact_zh_quote="采矿许可证延续",
            en_literal="mining license renewal",
            where_in_doc="main announcement"
        )
        
        extraction = Extraction(
            doc_url="https://example.com/doc",
            doc_title="Test Document",
            mine_match="JIANXIAWO_MATCH",
            authority="Jiangxi Natural Resources",
            key_terms_found_zh=["采矿许可证延续", "恢复生产"],
            key_terms_found_en=["mining license renewal", "resume production"],
            proposed_label="YES_CONDITION",
            confidence=0.85,
            evidence=[evidence],
            hazards=["potential typo"]
        )
        
        assert extraction.doc_title == "Test Document"
        assert extraction.authority == "Jiangxi Natural Resources"
        assert len(extraction.key_terms_found_zh) == 2
        assert len(extraction.key_terms_found_en) == 2
        assert len(extraction.evidence) == 1
        assert len(extraction.hazards) == 1
    
    def test_extraction_confidence_validation(self):
        """Test extraction confidence validation."""
        # Valid confidence values
        for conf in [0.0, 0.5, 1.0]:
            extraction = Extraction(
                doc_url="https://example.com/doc",
                mine_match="JIANXIAWO_MATCH",
                proposed_label="YES_CONDITION",
                confidence=conf,
                evidence=[],
                key_terms_found_zh=[],
                key_terms_found_en=[],
                hazards=[]
            )
            assert extraction.confidence == conf
        
        # Invalid confidence values
        for conf in [-0.1, 1.1]:
            with pytest.raises(ValueError):
                Extraction(
                    doc_url="https://example.com/doc",
                    mine_match="JIANXIAWO_MATCH",
                    proposed_label="YES_CONDITION",
                    confidence=conf,
                    evidence=[],
                    key_terms_found_zh=[],
                    key_terms_found_en=[],
                    hazards=[]
                )
    
    def test_extraction_enum_validation(self):
        """Test extraction enum field validation."""
        # Valid mine_match values
        for match in ["JIANXIAWO_MATCH", "POSSIBLE_MATCH", "NO_MATCH"]:
            extraction = Extraction(
                doc_url="https://example.com/doc",
                mine_match=match,
                proposed_label="YES_CONDITION",
                confidence=0.8,
                evidence=[],
                key_terms_found_zh=[],
                key_terms_found_en=[],
                hazards=[]
            )
            assert extraction.mine_match == match
        
        # Valid proposed_label values
        for label in ["YES_CONDITION", "NO_CONDITION", "AMBIGUOUS", "IRRELEVANT"]:
            extraction = Extraction(
                doc_url="https://example.com/doc",
                mine_match="JIANXIAWO_MATCH",
                proposed_label=label,
                confidence=0.8,
                evidence=[],
                key_terms_found_zh=[],
                key_terms_found_en=[],
                hazards=[]
            )
            assert extraction.proposed_label == label
