"""
Tests for the Manifold API client.
"""

import pytest
import requests
from unittest.mock import Mock, patch
from oreaclebot.client import ManifoldClient, LimitOrder, Comment, Outcome


class TestManifoldClient:
    """Test cases for ManifoldClient."""
    
    def test_client_initialization(self):
        """Test client initialization with API key."""
        client = ManifoldClient("test_api_key")
        assert client.api_key == "test_api_key"
        assert client.base_url == "https://api.manifold.markets/v0"
        assert client.max_retries == 3
    
    def test_client_initialization_custom_params(self):
        """Test client initialization with custom parameters."""
        client = ManifoldClient("test_api_key", "https://test.api", 5)
        assert client.api_key == "test_api_key"
        assert client.base_url == "https://test.api"
        assert client.max_retries == 5
    
    def test_client_headers(self):
        """Test that client creates proper headers."""
        client = ManifoldClient("test_api_key")
        expected_headers = {
            "Authorization": "Key test_api_key",
            "Content-Type": "application/json"
        }
        assert client._headers == expected_headers


class TestLimitOrder:
    """Test cases for LimitOrder dataclass."""
    
    def test_limit_order_creation(self):
        """Test limit order creation and validation."""
        order = LimitOrder(
            contractId="test_contract",
            outcome=Outcome.YES,
            amount=100,
            limitProb=0.6
        )
        
        assert order.contractId == "test_contract"
        assert order.outcome == Outcome.YES
        assert order.amount == 100
        assert order.limitProb == 0.6
        assert order.expiresMillisAfter == 6 * 60 * 60 * 1000  # default
    
    def test_limit_order_validation_valid(self):
        """Test limit order validation with valid data."""
        order = LimitOrder(
            contractId="test_contract",
            outcome=Outcome.YES,
            amount=100,
            limitProb=0.6
        )
        
        # Should not raise any exception
        order.validate()
    
    def test_limit_order_validation_invalid_amount(self):
        """Test limit order validation with invalid amount."""
        order = LimitOrder(
            contractId="test_contract",
            outcome=Outcome.YES,
            amount=0,  # Invalid amount
            limitProb=0.6
        )
        
        with pytest.raises(ValueError, match="Order amount must be positive"):
            order.validate()
    
    def test_limit_order_validation_invalid_prob(self):
        """Test limit order validation with invalid probability."""
        order = LimitOrder(
            contractId="test_contract",
            outcome=Outcome.YES,
            amount=100,
            limitProb=1.5  # Invalid probability
        )
        
        with pytest.raises(ValueError, match="Limit probability must be between 0.0 and 1.0"):
            order.validate()
    
    def test_limit_order_payload(self):
        """Test limit order payload generation."""
        order = LimitOrder(
            contractId="test_contract",
            outcome=Outcome.YES,
            amount=100,
            limitProb=0.6
        )
        
        payload = order.payload()
        
        expected = {
            "contractId": "test_contract",
            "outcome": "YES",  # Enum value converted to string
            "amount": 100,
            "limitProb": 0.6,
            "expiresMillisAfter": 6 * 60 * 60 * 1000
        }
        
        assert payload == expected


class TestComment:
    """Test cases for Comment dataclass."""
    
    def test_comment_creation(self):
        """Test comment creation."""
        comment = Comment(
            contractId="test_contract",
            markdown="# Test comment"
        )
        
        assert comment.contractId == "test_contract"
        assert comment.markdown == "# Test comment"
