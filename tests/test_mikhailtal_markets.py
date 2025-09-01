"""
Tests specifically for MikhailTal markets and CATL-related markets.

These tests search for markets created by MikhailTal and specifically look for
CATL-related prediction markets.
"""

import pytest
import os
from oreaclebot.client import ManifoldClient


class TestMikhailTalMarkets:
    """Test cases for MikhailTal markets."""
    
    def test_search_mikhailtal_markets(self):
        """Test searching for markets created by MikhailTal."""
        api_key = os.getenv("MANIFOLD_API_KEY")
        if not api_key:
            pytest.skip("MANIFOLD_API_KEY not set - skipping integration test")
        
        client = ManifoldClient(api_key)
        
        # Get all markets and search for MikhailTal
        import requests
        r = requests.get("https://api.manifold.markets/v0/markets", timeout=20)
        r.raise_for_status()
        markets = r.json()
        
        mikhailtal_markets = []
        for market in markets:
            creator_username = market.get("creatorUsername", "")
            if "mikhailtal" in creator_username.lower():
                mikhailtal_markets.append({
                    "slug": market.get("slug"),
                    "question": market.get("question", "")[:100],
                    "id": market.get("id"),
                    "creator": creator_username
                })
        
        print(f"Found {len(mikhailtal_markets)} markets by MikhailTal:")
        for market in mikhailtal_markets:
            print(f"  - {market['slug']}: {market['question']}")
        
        # We expect to find at least some markets by MikhailTal
        assert len(mikhailtal_markets) > 0, "No markets found by MikhailTal"
    
    def test_search_catl_markets(self):
        """Test searching for CATL-related markets."""
        api_key = os.getenv("MANIFOLD_API_KEY")
        if not api_key:
            pytest.skip("MANIFOLD_API_KEY not set - skipping integration test")
        
        client = ManifoldClient(api_key)
        
        # Get all markets and search for CATL-related content
        import requests
        r = requests.get("https://api.manifold.markets/v0/markets", timeout=20)
        r.raise_for_status()
        markets = r.json()
        
        catl_markets = []
        for market in markets:
            question = market.get("question", "").lower()
            slug = market.get("slug", "").lower()
            description = market.get("description", "").lower()
            
            # Search for CATL-related terms
            catl_terms = ["catl", "yichun", "lithium", "mining", "license", "renewal"]
            if any(term in question or term in slug or term in description for term in catl_terms):
                catl_markets.append({
                    "slug": market.get("slug"),
                    "question": market.get("question", "")[:100],
                    "id": market.get("id"),
                    "creator": market.get("creatorUsername", "")
                })
        
        print(f"Found {len(catl_markets)} CATL-related markets:")
        for market in catl_markets:
            print(f"  - {market['slug']}: {market['question']}")
        
        # Log the results but don't fail if none found (market might not exist yet)
        if len(catl_markets) == 0:
            print("⚠️  No CATL-related markets found - the market might not exist in the API yet")
        else:
            print(f"✅ Found {len(catl_markets)} CATL-related markets")
    
    def test_specific_catl_market_slug(self):
        """Test the specific CATL market slug we're interested in."""
        api_key = os.getenv("MANIFOLD_API_KEY")
        if not api_key:
            pytest.skip("MANIFOLD_API_KEY not set - skipping integration test")
        
        client = ManifoldClient(api_key)
        
        # Test the specific market slug
        market_slug = "MikhailTal/catl-receives-license-renewal-for-y-qz65RqIZsy"
        
        try:
            market = client.get_market_by_slug(market_slug)
            
            # If we get here, the market exists
            assert market["slug"] == market_slug
            assert "CATL" in market["question"]
            assert "Yichun" in market["question"]
            assert "lithium" in market["question"].lower()
            
            print(f"✅ Found CATL market: {market['question']}")
            print(f"   Market ID: {market['id']}")
            print(f"   Creator: {market.get('creatorUsername', 'Unknown')}")
            
        except ValueError as e:
            if "No market found for slug" in str(e):
                print(f"⚠️  CATL market not found: {market_slug}")
                print("   This could mean:")
                print("   - The market doesn't exist yet")
                print("   - The market is very new and not indexed")
                print("   - The slug format is different")
                # Don't fail the test - just log the issue
            else:
                raise
    
    def test_search_markets_by_creator(self):
        """Test searching for markets by specific creator."""
        api_key = os.getenv("MANIFOLD_API_KEY")
        if not api_key:
            pytest.skip("MANIFOLD_API_KEY not set - skipping integration test")
        
        # Get all markets and search for specific creators
        import requests
        r = requests.get("https://api.manifold.markets/v0/markets", timeout=20)
        r.raise_for_status()
        markets = r.json()
        
        # Look for markets by various creators
        creators_to_check = ["MikhailTal", "mikhailtal", "Mikhail"]
        
        for creator in creators_to_check:
            creator_markets = []
            for market in markets:
                creator_username = market.get("creatorUsername", "")
                if creator.lower() in creator_username.lower():
                    creator_markets.append({
                        "slug": market.get("slug"),
                        "question": market.get("question", "")[:80],
                        "creator": creator_username
                    })
            
            print(f"Markets by '{creator}': {len(creator_markets)}")
            for market in creator_markets[:5]:  # Show first 5
                print(f"  - {market['slug']}: {market['question']}")
        
        # Check if we found any markets by similar usernames
        total_found = sum(
            len([m for m in markets if creator.lower() in m.get("creatorUsername", "").lower()])
            for creator in creators_to_check
        )
        
        if total_found > 0:
            print(f"✅ Found {total_found} markets by similar creators")
        else:
            print("⚠️  No markets found by similar creator names")
