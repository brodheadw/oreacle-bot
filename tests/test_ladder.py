"""
Tests for ladder monotonicity checking.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock

from oreaclebot.ladder import LadderMonotonicity, LadderViolation


@pytest.fixture
def mock_client():
    """Mock ManifoldClient for testing."""
    return Mock()


@pytest.fixture
def ladder_checker(mock_client):
    """LadderMonotonicity instance with mock client."""
    return LadderMonotonicity(mock_client, min_violation_size=0.05)


@pytest.fixture
def sample_markets():
    """Sample market data for testing."""
    return [
        {
            'id': 'market1',
            'slug': 'event-by-2024-12-31',
            'question': 'Will event happen by 2024-12-31?',
            'probability': 0.7
        },
        {
            'id': 'market2', 
            'slug': 'event-by-2024-06-30',
            'question': 'Will event happen by 2024-06-30?',
            'probability': 0.8  # Violation: earlier date has higher probability
        },
        {
            'id': 'market3',
            'slug': 'different-event',
            'question': 'Will different event happen by 2024-12-31?',
            'probability': 0.5
        }
    ]


class TestLadderMonotonicity:
    """Test cases for LadderMonotonicity class."""
    
    def test_extract_deadline_iso_format(self, ladder_checker):
        """Test deadline extraction from ISO format."""
        question = "Will CATL resume production by 2024-12-31?"
        deadline = ladder_checker.extract_deadline_from_question(question)
        assert deadline == datetime(2024, 12, 31)
    
    def test_extract_deadline_month_name(self, ladder_checker):
        """Test deadline extraction from month name format."""
        question = "Will event happen by December 31, 2024?"
        deadline = ladder_checker.extract_deadline_from_question(question)
        assert deadline == datetime(2024, 12, 31)
    
    def test_extract_deadline_before_pattern(self, ladder_checker):
        """Test deadline extraction from 'before' pattern."""
        question = "Will event happen before January 1, 2025?"
        deadline = ladder_checker.extract_deadline_from_question(question)
        assert deadline == datetime(2024, 12, 31)  # One day before
    
    def test_extract_deadline_no_match(self, ladder_checker):
        """Test deadline extraction with no matching pattern."""
        question = "Will event happen soon?"
        deadline = ladder_checker.extract_deadline_from_question(question)
        assert deadline is None
    
    def test_group_markets_by_base_question(self, ladder_checker, sample_markets):
        """Test grouping markets by base question."""
        groups = ladder_checker.group_markets_by_base_question(sample_markets)
        
        # Should group first two markets together (same base question)
        assert len(groups) == 1
        assert 'Will event happen' in list(groups.keys())[0]
        assert len(list(groups.values())[0]) == 2
    
    def test_check_group_monotonicity_violation(self, ladder_checker, sample_markets):
        """Test detection of monotonicity violation."""
        # Use only the first two markets that have the same base question
        group_markets = sample_markets[:2]
        violations = ladder_checker.check_group_monotonicity(group_markets)
        
        assert len(violations) == 1
        violation = violations[0]
        assert violation.earlier_prob == 0.8  # Earlier market (June 30)
        assert violation.later_prob == 0.7    # Later market (December 31)
        assert abs(violation.violation_size - 0.1) < 0.0001
    
    def test_check_group_monotonicity_no_violation(self, ladder_checker):
        """Test no violation when probabilities are correctly ordered."""
        markets = [
            {
                'question': 'Will event happen by 2024-06-30?',
                'probability': 0.6  # Lower probability for earlier date
            },
            {
                'question': 'Will event happen by 2024-12-31?', 
                'probability': 0.8  # Higher probability for later date
            }
        ]
        violations = ladder_checker.check_group_monotonicity(markets)
        assert len(violations) == 0
    
    def test_create_violation_comment(self, ladder_checker):
        """Test violation comment generation."""
        earlier_market = {
            'question': 'Will event happen by 2024-06-30?',
            'slug': 'event-june'
        }
        later_market = {
            'question': 'Will event happen by 2024-12-31?',
            'slug': 'event-december'
        }
        violation = LadderViolation(earlier_market, later_market, 0.8, 0.7)
        
        comment = ladder_checker.create_violation_comment(violation)
        
        assert "Monotonicity Violation Detected" in comment
        assert "80.0%" in comment  # Earlier probability
        assert "70.0%" in comment  # Later probability
        assert "10.0%" in comment  # Violation size


class TestLadderViolation:
    """Test cases for LadderViolation class."""
    
    def test_violation_creation(self):
        """Test violation object creation."""
        earlier_market = {'question': 'Earlier market?'}
        later_market = {'question': 'Later market?'}
        
        violation = LadderViolation(earlier_market, later_market, 0.8, 0.6)
        
        assert violation.earlier_prob == 0.8
        assert violation.later_prob == 0.6
        assert abs(violation.violation_size - 0.2) < 0.0001
    
    def test_violation_string_representation(self):
        """Test violation string representation."""
        earlier_market = {'question': 'Will X happen by June?'}
        later_market = {'question': 'Will X happen by December?'}
        
        violation = LadderViolation(earlier_market, later_market, 0.75, 0.65)
        
        violation_str = str(violation)
        assert "Monotonicity violation" in violation_str
        assert "75.0%" in violation_str
        assert "65.0%" in violation_str
        assert "10.0%" in violation_str


@pytest.fixture
def yes_condition_extraction():
    """Sample extraction with YES_CONDITION label."""
    from oreaclebot.models import Extraction, Evidence
    
    return Extraction(
        doc_url="http://example.com/doc1",
        mine_match="JIANXIAWO_MATCH",
        proposed_label="YES_CONDITION",
        confidence=0.85,
        evidence=[
            Evidence(
                exact_zh_quote="采矿许可证延续获得批准",
                en_literal="mining license renewal approved",
                where_in_doc="paragraph 2"
            )
        ]
    )


@pytest.fixture  
def no_condition_extraction():
    """Sample extraction with NO_CONDITION label."""
    from oreaclebot.models import Extraction, Evidence
    
    return Extraction(
        doc_url="http://example.com/doc2", 
        mine_match="NO_MATCH",
        proposed_label="NO_CONDITION",
        confidence=0.90,
        evidence=[
            Evidence(
                exact_zh_quote="仅限勘探活动",
                en_literal="exploration activities only", 
                where_in_doc="main text"
            )
        ]
    )


@pytest.fixture
def ambiguous_extraction():
    """Sample extraction with AMBIGUOUS label."""
    from oreaclebot.models import Extraction
    
    return Extraction(
        doc_url="http://example.com/doc3",
        mine_match="POSSIBLE_MATCH", 
        proposed_label="AMBIGUOUS",
        confidence=0.45,
        evidence=[]
    )


@pytest.fixture
def irrelevant_extraction():
    """Sample extraction with IRRELEVANT label."""
    from oreaclebot.models import Extraction
    
    return Extraction(
        doc_url="http://example.com/doc4",
        mine_match="NO_MATCH",
        proposed_label="IRRELEVANT", 
        confidence=0.95,
        evidence=[]
    )