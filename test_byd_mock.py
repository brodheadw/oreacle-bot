#!/usr/bin/env python3
"""
Mock BYD test with simulated today's announcement to verify the filter logic works.
This simulates the announcement that definitely exists today.
"""

from oreaclebot.sentinels.byd_monthly import BYDSentinel
from oreaclebot.client import ManifoldClient
import logging

def test_with_mock_announcement():
    """Test BYD sentinel with a mock version of today's announcement."""
    
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("🧪 BYD Sentinel Mock Test")
    print("=========================")
    
    # Create client (dummy key for testing)
    client = ManifoldClient('dummy_key')
    sentinel = BYDSentinel(client)
    
    # Mock today's announcement based on user's research
    mock_announcement = {
        'announcementTitle': '自願公告 — 2025年8月產銷快報',  # Exact title from user's research
        'adjunctUrl': 'https://www1.hkexnews.hk/listedco/listconews/sehk/2025/0901/01211_byd_aug2025.pdf',
        'content': '''
        BYD COMPANY LIMITED (01211.HK)
        自願公告 — 2025年8月產銷快報
        VOLUNTARY ANNOUNCEMENT – PRODUCTION AND SALES VOLUME FOR AUGUST 2025
        
        比亞迪股份有限公司（「本公司」及其附屬公司，統稱「本集團」）公佈2025年8月產銷數據：
        
        汽車銷售：總銷量約為370,854台，其中新能源汽車銷量約為370,854台
        - 純電動汽車銷量：約為148,470台
        - 插電式混合動力汽車銷量：約為222,384台
        
        本公司汽車累計銷量約為2,417,804台，同比增長約28.8%
        ''',
        'publishDate': '2025-09-01',
        'lang': 'zh'
    }
    
    print("📄 Mock announcement:")
    print(f"  Title: {mock_announcement['announcementTitle']}")
    print(f"  Date: {mock_announcement['publishDate']}")
    
    # Test the parsing logic
    print("\n🔍 Testing parse_monthly_sales_report...")
    monthly_data = sentinel.parse_monthly_sales_report(mock_announcement)
    
    if monthly_data:
        print("✅ Successfully parsed as monthly report!")
        print(f"  Period: {monthly_data.period}")
        print(f"  Total sales: {monthly_data.total_sales:,}")
        print(f"  NEV sales: {monthly_data.nev_sales:,}")
        print(f"  BEV sales: {monthly_data.bev_sales:,}")
        print(f"  PHEV sales: {monthly_data.phev_sales:,}")
        print(f"  Source: {monthly_data.source_title}")
        
        # Test comment creation
        print("\n💬 Testing comment creation...")
        try:
            comment = sentinel.create_monthly_comment(monthly_data)
            print("✅ Successfully created comment!")
            print("📝 Comment preview:")
            print(comment[:500] + "...")
            
        except Exception as e:
            print(f"❌ Error creating comment: {e}")
        
    else:
        print("❌ Failed to parse as monthly report")
        print("🔍 Debug: Check filter logic...")
        
        # Debug the filter
        title = mock_announcement.get('announcementTitle', '')
        print(f"  Title: '{title}'")
        print(f"  Title lower: '{title.lower()}'")
        
        # Test individual keyword matches
        keywords = ['产销快报', '產銷快報', 'production and sales volume']
        for keyword in keywords:
            if keyword.lower() in title.lower() or keyword in title:
                print(f"  ✅ Keyword match: {keyword}")
            else:
                print(f"  ❌ Keyword miss: {keyword}")
                
    return monthly_data is not None

if __name__ == "__main__":
    success = test_with_mock_announcement()
    print(f"\n🏁 Result: {'✅ PASS' if success else '❌ FAIL'}")
    if success:
        print("Filter logic works! Issue is in fetch layer.")
    else:
        print("Filter logic needs fixes.")