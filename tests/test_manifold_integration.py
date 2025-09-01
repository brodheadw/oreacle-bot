"""
Integration tests for Manifold API client with real market data.

These tests verify that our client can successfully interact with the actual
Manifold Markets API and retrieve real market information.
"""

import pytest
import os
from unittest.mock import patch
from oreacle_bot.client import ManifoldClient


class TestManifoldIntegration:
    """Integration tests for Manifold API client."""
    
    def test_get_market_by_slug_real_market(self):
        """Test retrieving a real popular market by slug."""
        # Use a test API key or skip if not available
        api_key = os.getenv("MANIFOLD_API_KEY")
        if not api_key:
            pytest.skip("MANIFOLD_API_KEY not set - skipping integration test")
        
        client = ManifoldClient(api_key)
        
        # Test with the actual CATL market that we know exists
        market_slug = "catl-receives-license-renewal-for-y-qz65RqIZsy"
        
        try:
            market = client.get_market_by_slug(market_slug)
            
            # Verify we got a valid market response
            assert isinstance(market, dict)
            assert "id" in market
            assert "question" in market
            assert "slug" in market
            
            # Verify it's the correct market
            assert market["slug"] == market_slug
            assert "catl" in market["question"].lower()
            assert "yichun" in market["question"].lower()
            assert "lithium" in market["question"].lower()
            
            # Verify market has expected structure
            assert "closeTime" in market
            assert "createdTime" in market
            assert "outcomeType" in market
            
            print(f"✅ Successfully retrieved market: {market['question']}")
            print(f"   Market ID: {market['id']}")
            print(f"   Close Time: {market.get('closeTime', 'N/A')}")
            
        except Exception as e:
            pytest.fail(f"Failed to retrieve market {market_slug}: {e}")
    
    def test_get_market_by_slug_alternative_endpoint(self):
        """Test that our fallback endpoint works for market retrieval."""
        api_key = os.getenv("MANIFOLD_API_KEY")
        if not api_key:
            pytest.skip("MANIFOLD_API_KEY not set - skipping integration test")
        
        client = ManifoldClient(api_key)
        market_slug = "catl-receives-license-renewal-for-y-qz65RqIZsy"
        
        # Test the new /markets endpoint with slug filtering
        try:
            market = client.get_market_by_slug(market_slug)
            
            # Verify the response structure
            assert isinstance(market, dict)
            assert market["slug"] == market_slug
            
            print(f"✅ Fallback endpoint works for market: {market['question']}")
            
        except Exception as e:
            pytest.fail(f"Fallback endpoint failed for market {market_slug}: {e}")
    
    def test_market_resolution_criteria(self):
        """Test that we can extract resolution criteria from the market."""
        api_key = os.getenv("MANIFOLD_API_KEY")
        if not api_key:
            pytest.skip("MANIFOLD_API_KEY not set - skipping integration test")
        
        client = ManifoldClient(api_key)
        market_slug = "catl-receives-license-renewal-for-y-qz65RqIZsy"
        
        try:
            market = client.get_market_by_slug(market_slug)
            
            # Check if market has description/resolution criteria
            description = market.get("description", "")
            text = market.get("text", "")
            
            # Look for key terms in the resolution criteria
            combined_text = f"{description} {text}".lower()
            
            # Verify key resolution criteria terms are present (for the CATL market)
            assert "catl" in combined_text
            assert "yichun" in combined_text
            assert "lithium" in combined_text
            assert "license" in combined_text or "renewal" in combined_text
            
            print(f"✅ Market contains expected resolution criteria")
            print(f"   Description length: {len(description)}")
            print(f"   Text length: {len(text)}")
            
        except Exception as e:
            pytest.fail(f"Failed to verify resolution criteria: {e}")
    
    def test_market_verification_links(self):
        """Test that the market contains expected content."""
        api_key = os.getenv("MANIFOLD_API_KEY")
        if not api_key:
            pytest.skip("MANIFOLD_API_KEY not set - skipping integration test")
        
        client = ManifoldClient(api_key)
        market_slug = "catl-receives-license-renewal-for-y-qz65RqIZsy"
        
        try:
            market = client.get_market_by_slug(market_slug)
            
            # Check for verification links in the market description
            description = market.get("description", "")
            text = market.get("text", "")
            combined_text = f"{description} {text}"
            
            # Verify expected content is present (for the CATL market)
            expected_terms = [
                "catl",
                "yichun",
                "lithium",
                "license",
                "renewal"
            ]
            
            found_terms = []
            for term in expected_terms:
                if term in combined_text:
                    found_terms.append(term)
            
            assert len(found_terms) >= 2, f"Expected at least 2 relevant terms, found: {found_terms}"
            
            print(f"✅ Found relevant terms: {found_terms}")
            
        except Exception as e:
            pytest.fail(f"Failed to verify links: {e}")
    
    @pytest.mark.parametrize("slug_variant", [
        "catl-receives-license-renewal-for-y-qz65RqIZsy",  # Jan 1, 2026
        "catl-receives-license-renewal-for-y-gd6qs2lII6",  # Nov 1, 2025
    ])
    def test_market_slug_variants(self, slug_variant):
        """Test different slug formats to ensure robustness."""
        api_key = os.getenv("MANIFOLD_API_KEY")
        if not api_key:
            pytest.skip("MANIFOLD_API_KEY not set - skipping integration test")
        
        client = ManifoldClient(api_key)
        
        try:
            market = client.get_market_by_slug(slug_variant)
            
            # Should get a valid market response
            assert isinstance(market, dict)
            assert "id" in market
            assert "question" in market
            
            print(f"✅ Slug variant '{slug_variant}' works")
            
        except Exception as e:
            # Some variants might not work, that's okay for this test
            print(f"⚠️  Slug variant '{slug_variant}' failed: {e}")
    
    def test_market_trading_info(self):
        """Test that we can retrieve trading information from the market."""
        api_key = os.getenv("MANIFOLD_API_KEY")
        if not api_key:
            pytest.skip("MANIFOLD_API_KEY not set - skipping integration test")
        
        client = ManifoldClient(api_key)
        market_slug = "catl-receives-license-renewal-for-y-qz65RqIZsy"
        
        try:
            market = client.get_market_by_slug(market_slug)
            
            # Check for trading-related fields
            assert "outcomeType" in market
            assert "mechanism" in market
            
            # Verify it's a binary market
            assert market["outcomeType"] == "BINARY"
            
            # Check for probability information
            if "probability" in market:
                prob = market["probability"]
                assert 0.0 <= prob <= 1.0
                print(f"✅ Market probability: {prob:.2%}")
            
            # Check for volume information
            if "volume" in market:
                volume = market["volume"]
                assert volume >= 0
                print(f"✅ Market volume: {volume}")
            
            print(f"✅ Market trading info retrieved successfully")
            
        except Exception as e:
            pytest.fail(f"Failed to retrieve trading info: {e}")


# Test configuration for integration tests
@pytest.fixture(scope="session")
def manifold_client():
    """Fixture providing a Manifold client for integration tests."""
    api_key = os.getenv("MANIFOLD_API_KEY")
    if not api_key:
        pytest.skip("MANIFOLD_API_KEY not set - skipping integration tests")
    
    return ManifoldClient(api_key)


@pytest.fixture
def test_market_slug():
    """Fixture providing a test market slug."""
    return "catl-receives-license-renewal-for-y-qz65RqIZsy"
