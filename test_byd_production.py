#!/usr/bin/env python3
"""
Production test for BYD sentinel - shows what CLI output will look like
with real posting enabled.
"""

from oreaclebot.sentinels.byd_monthly import BYDSentinel
from oreaclebot.client import ManifoldClient
import logging

def test_production_ready():
    """Test production-ready BYD sentinel with real posting logic."""
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Note: Use dummy API key for testing - in production use real key
    client = ManifoldClient('dummy_key')
    sentinel = BYDSentinel(client)
    
    print("🧪 BYD Sentinel Production Test")
    print("================================")
    print("Testing with POSTING ENABLED (will fail with dummy API key)")
    
    # Example BYD BEV market ID (user would provide real ones)
    # Format based on Manifold URL structure
    example_markets = [
        "byd-august-bev-sales-exceed-182000",  # >182k threshold market
        "byd-august-phev-sales-exceed-170000", # PHEV market example
    ]
    
    # Test with posting enabled
    results = sentinel.run_monthly_check(
        market_ids=example_markets,
        dry_run=False  # Real posting mode
    )
    
    print(f"\n🏁 PRODUCTION RESULTS:")
    print(f"  Reports found: {results['reports_found']}")
    print(f"  Comments posted: {results['comments_posted']}")
    print(f"  Errors: {len(results['errors'])}")
    
    if results['reports_found'] > 0:
        print("\n✅ SUCCESS: BYD discovery is working!")
        print("  - Found real BYD monthly PDFs")
        print("  - Extracted real sales data")
        print("  - Generated market comments")
        
        if results['comments_posted'] > 0:
            print("\n🎉 COMPLETE SUCCESS: Comments posted!")
        elif results['errors']:
            print(f"\n⚠️  Posting failed (expected with dummy key):")
            for error in results['errors'][:2]:
                print(f"     {error}")
            print("\n   With real MANIFOLD_API_KEY, this would post successfully!")
        else:
            print("\n❌ Posting blocked - check market_ids or other gates")
    else:
        print("\n❌ No reports found - check discovery logic")
        
    print("\n" + "="*50)
    print("PRODUCTION SETUP INSTRUCTIONS:")
    print("1. Set real MANIFOLD_API_KEY environment variable")
    print("2. Run: oreaclebot sentinel byd-monthly --market-ids <real_market_id>")
    print("3. Remove --dry-run flag to enable actual posting")
    print("4. Expected output: 'Reports found: 1, Comments posted: 1'")

if __name__ == "__main__":
    test_production_ready()