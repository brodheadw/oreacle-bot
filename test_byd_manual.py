#!/usr/bin/env python3
"""
Manual test to verify BYD announcement exists and can be found.
Based on the user's research showing today's announcement at 19:05 HKT.
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

def test_hkex_manual():
    """Test the exact HKEX URLs the user mentioned."""
    
    print("🧪 Manual BYD Announcement Test")
    print("===============================")
    
    # Test the URLs provided by user
    test_urls = [
        ("HKEX ZH Index", "https://www1.hkexnews.hk/listedco/listconews/index/lci.html?lang=zh"),
        ("HKEX EN Index", "https://www1.hkexnews.hk/listedco/listconews/index/lci.html?lang=en"),
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}
    
    for name, url in test_urls:
        print(f"\n📡 Testing {name}: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            print(f"✅ HTTP {response.status_code}")
            
            if response.status_code != 200:
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Check page structure
            print(f"📄 Content length: {len(response.text):,} chars")
            
            # Find all text content
            all_text = soup.get_text()
            
            # Search for BYD mentions
            byd_mentions = []
            if "比亞迪" in all_text:
                byd_mentions.append("比亞迪 (Traditional)")
            if "比亚迪" in all_text:
                byd_mentions.append("比亚迪 (Simplified)")
            if "BYD" in all_text.upper():
                byd_mentions.append("BYD (English)")
                
            print(f"🏢 BYD mentions found: {byd_mentions}")
            
            # Search for production/sales keywords
            keywords_found = []
            if re.search(r"產銷快報", all_text):
                keywords_found.append("產銷快報 (Traditional)")
            if re.search(r"产销快报", all_text):
                keywords_found.append("产销快报 (Simplified)")
            if "PRODUCTION AND SALES VOLUME" in all_text.upper():
                keywords_found.append("PRODUCTION AND SALES VOLUME")
            if "自願公告" in all_text:
                keywords_found.append("自願公告")
                
            print(f"🔑 Keywords found: {keywords_found}")
            
            # Look for today's announcement specifically
            if "2025年8月" in all_text:
                print("📅 Found August 2025 mentions!")
                # Extract context around August mentions
                lines = all_text.split('\n')
                for i, line in enumerate(lines):
                    if "2025年8月" in line and any(byd in line for byd in ["比亞迪", "比亚迪", "BYD"]):
                        print(f"🎯 POTENTIAL MATCH: {line.strip()[:150]}")
            
            # Check if this is the JS-heavy page issue
            script_tags = soup.find_all('script')
            print(f"🔧 JavaScript tags: {len(script_tags)} (may require JS rendering)")
            
            # Look for any table rows or list items with content
            content_elements = []
            for tag in ['tr', 'li', 'div']:
                elements = soup.find_all(tag)
                for elem in elements[:20]:  # Check first 20 of each
                    text = elem.get_text(strip=True)
                    if text and len(text) > 10 and any(byd in text for byd in ["比亞迪", "比亚迪", "BYD"]):
                        content_elements.append(f"{tag}: {text[:100]}")
            
            if content_elements:
                print("📋 BYD content elements found:")
                for elem in content_elements:
                    print(f"  {elem}")
            else:
                print("❌ No BYD content elements found in TR/LI/DIV tags")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n🏁 Test complete")
    print("\nNext steps:")
    print("1. If BYD mentions found but no structured data -> JS rendering needed")
    print("2. If no BYD mentions found -> wrong endpoint or blocking")
    print("3. If keywords found -> filter logic should work")

if __name__ == "__main__":
    test_hkex_manual()