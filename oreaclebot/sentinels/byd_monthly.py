"""
BYD Monthly Sentinel - Monitors BYD's monthly sales and production reports.

Watches HKEXnews (01211) and CNINFO (002594) for BYD's monthly operational updates,
particularly focusing on NEV (New Energy Vehicle) sales and production data.
"""

import logging
import re
import requests
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json

from ..client import ManifoldClient, Comment
from ..sheets_sink import SpreadsheetRow, SpreadsheetSink


class BYDMonthlyData:
    """Represents BYD monthly operational data."""
    
    def __init__(self):
        self.report_date = None
        self.period = ""  # e.g., "2024-01"
        
        # Sales data (vehicles)
        self.total_sales = 0
        self.nev_sales = 0  # New Energy Vehicle sales
        self.bev_sales = 0  # Battery Electric Vehicle sales  
        self.phev_sales = 0  # Plug-in Hybrid sales
        self.ice_sales = 0  # Internal Combustion Engine sales
        
        # Production data
        self.total_production = 0
        self.nev_production = 0
        self.bev_production = 0
        self.phev_production = 0
        
        # Export data
        self.total_exports = 0
        self.nev_exports = 0
        
        # Year-over-year comparisons
        self.sales_yoy_growth = None
        self.nev_sales_yoy_growth = None
        
        # Source information
        self.source_url = ""
        self.source_title = ""
        self.raw_text = ""
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'report_date': self.report_date.isoformat() if self.report_date else None,
            'period': self.period,
            'total_sales': self.total_sales,
            'nev_sales': self.nev_sales,
            'bev_sales': self.bev_sales,
            'phev_sales': self.phev_sales,
            'ice_sales': self.ice_sales,
            'total_production': self.total_production,
            'nev_production': self.nev_production,
            'bev_production': self.bev_production,
            'phev_production': self.phev_production,
            'total_exports': self.total_exports,
            'nev_exports': self.nev_exports,
            'sales_yoy_growth': self.sales_yoy_growth,
            'nev_sales_yoy_growth': self.nev_sales_yoy_growth,
            'source_url': self.source_url,
            'source_title': self.source_title
        }


class BYDSentinel:
    """
    Monitors BYD monthly sales and production reports.
    
    Watches multiple sources:
    - HKEXnews for BYD Company Limited (01211.HK)
    - CNINFO for BYD Company Limited (002594.SZ)
    - BYD's investor relations announcements
    """
    
    def __init__(self, client: ManifoldClient, spreadsheet_sink: SpreadsheetSink = None):
        """
        Initialize BYD sentinel.
        
        Args:
            client: ManifoldClient for posting comments
            spreadsheet_sink: SpreadsheetSink for logging data
        """
        self.client = client
        self.spreadsheet_sink = spreadsheet_sink
        self.logger = logging.getLogger(__name__)
        
        # BYD identifiers
        self.hk_stock_code = "01211"  # HKEXnews
        self.sz_stock_code = "002594"  # CNINFO
        
    def fetch_hkex_announcements(self, days_back: int = 7) -> List[Dict]:
        """
        Fetch recent BYD announcements from HKEXnews.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of announcement dictionaries
        """
        announcements = []
        
        try:
            # HKEXnews announcement search URL
            # Note: This is a simplified implementation - actual API endpoints may vary
            url = "https://www1.hkexnews.hk/search/titlesearch.xhtml"
            params = {
                'lang': 'en',
                'sortby': 'datetime',
                'sortdir': 'desc',
                'stock': self.hk_stock_code,
                'from': (datetime.now() - timedelta(days=days_back)).strftime('%Y%m%d')
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse HTML response (simplified - would need proper HTML parsing)
            # This is a placeholder for actual implementation
            self.logger.info(f"Fetched HKEXnews data for BYD ({self.hk_stock_code})")
            
        except Exception as e:
            self.logger.error(f"Failed to fetch HKEXnews announcements: {e}")
            
        return announcements
    
    def fetch_cninfo_announcements(self, days_back: int = 7) -> List[Dict]:
        """
        Fetch recent BYD announcements from CNINFO.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of announcement dictionaries
        """
        announcements = []
        
        try:
            # CNINFO API for BYD (002594)
            url = "http://www.cninfo.com.cn/new/hisAnnouncement/query"
            
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            data = {
                'stock': self.sz_stock_code,
                'searchkey': '',
                'plate': '',
                'category': '',
                'trade': '',
                'column': 'szse',
                'columnTitle': '历史公告查询',
                'pageNum': 1,
                'pageSize': 30,
                'tabName': 'fulltext',
                'sortName': '',
                'sortType': '',
                'limit': '',
                'showTitle': '',
                'seDate': f"{start_date}~{end_date}"
            }
            
            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get('resultcode') == 200:
                announcements = result.get('announcements', [])
                self.logger.info(f"Fetched {len(announcements)} CNINFO announcements for BYD")
            
        except Exception as e:
            self.logger.error(f"Failed to fetch CNINFO announcements: {e}")
            
        return announcements
    
    def parse_monthly_sales_report(self, announcement: Dict) -> Optional[BYDMonthlyData]:
        """
        Parse a monthly sales/production announcement.
        
        Args:
            announcement: Announcement dictionary with title and content
            
        Returns:
            BYDMonthlyData if this is a monthly report, None otherwise
        """
        title = announcement.get('announcementTitle', '').lower()
        content = announcement.get('content', '')
        
        # Check if this is a monthly sales/production report
        monthly_keywords = [
            'monthly sales', 'monthly production', 'monthly delivery',
            '月度销量', '月度产量', '产销快报', '销量快报',
            'sales volume', 'production volume'
        ]
        
        is_monthly = any(keyword in title for keyword in monthly_keywords)
        if not is_monthly:
            return None
            
        self.logger.info(f"Parsing monthly report: {title[:100]}")
        
        data = BYDMonthlyData()
        data.source_url = announcement.get('adjunctUrl', '')
        data.source_title = announcement.get('announcementTitle', '')
        data.raw_text = content
        
        # Extract period (e.g., "2024-01")
        period_match = re.search(r'(\d{4})[年\-](\d{1,2})', title)
        if period_match:
            year, month = period_match.groups()
            data.period = f"{year}-{month.zfill(2)}"
            
        # Extract sales numbers using regex patterns
        # These patterns would need to be refined based on actual BYD report formats
        
        # Total sales (汽车销量、总销量)
        total_pattern = r'(?:总销量|汽车销量)(?:约为|为)?[:：\s]*?(\d+(?:,\d{3})*|\d+(?:\.\d+)?(?:万)?)(?:辆|台|units?)'
        total_match = re.search(total_pattern, content, re.IGNORECASE)
        if total_match:
            data.total_sales = self._parse_number(total_match.group(1))
            
        # NEV sales (新能源汽车销量)
        nev_pattern = r'新能源汽车销量(?:约为|为)?[:：\s]*?(\d+(?:,\d{3})*|\d+(?:\.\d+)?(?:万)?)(?:辆|台|units?)'
        nev_match = re.search(nev_pattern, content, re.IGNORECASE)
        if nev_match:
            data.nev_sales = self._parse_number(nev_match.group(1))
            
        # BEV sales (纯电动汽车)
        bev_pattern = r'纯电动汽车(?:销量)?(?:约为|为)?[:：\s]*?(\d+(?:,\d{3})*|\d+(?:\.\d+)?(?:万)?)(?:辆|台|units?)'
        bev_match = re.search(bev_pattern, content, re.IGNORECASE)
        if bev_match:
            data.bev_sales = self._parse_number(bev_match.group(1))
            
        # PHEV sales (混合动力汽车)
        phev_pattern = r'(?:插电式混合动力|混合动力)汽车(?:销量)?(?:约为|为)?[:：\s]*?(\d+(?:,\d{3})*|\d+(?:\.\d+)?(?:万)?)(?:辆|台|units?)'
        phev_match = re.search(phev_pattern, content, re.IGNORECASE)
        if phev_match:
            data.phev_sales = self._parse_number(phev_match.group(1))
            
        # Year-over-year growth
        yoy_pattern = r'同比(?:增长|上升|增加)(?:约)?(\d+(?:\.\d+)?)%'
        yoy_match = re.search(yoy_pattern, content)
        if yoy_match:
            data.sales_yoy_growth = float(yoy_match.group(1))
            
        # Only return if we extracted meaningful data
        if data.total_sales > 0 or data.nev_sales > 0:
            return data
            
        return None
    
    def _parse_number(self, num_str: str) -> int:
        """
        Parse Chinese/English number strings to integers.
        
        Handles formats like:
        - "123,456"
        - "12.34万" (万 = 10,000)
        - "123万"
        """
        if not num_str:
            return 0
            
        # Remove commas
        num_str = num_str.replace(',', '')
        
        # Handle 万 (10,000) multiplier
        if '万' in num_str:
            base_num = float(num_str.replace('万', ''))
            return int(base_num * 10000)
            
        try:
            return int(float(num_str))
        except ValueError:
            return 0
    
    def create_monthly_comment(self, data: BYDMonthlyData) -> str:
        """
        Create a structured comment for BYD monthly data.
        
        Args:
            data: BYDMonthlyData to summarize
            
        Returns:
            Formatted comment text
        """
        comment = f"""📊 **BYD Monthly Sales Report - {data.period}**

**🚗 Vehicle Sales:**"""
        
        if data.total_sales > 0:
            comment += f"\n- **Total Sales**: {data.total_sales:,} vehicles"
            
        if data.nev_sales > 0:
            comment += f"\n- **NEV Sales**: {data.nev_sales:,} vehicles"
            nev_percentage = (data.nev_sales / data.total_sales * 100) if data.total_sales > 0 else 0
            if nev_percentage > 0:
                comment += f" ({nev_percentage:.1f}% of total)"
                
        if data.bev_sales > 0:
            comment += f"\n- **BEV Sales**: {data.bev_sales:,} vehicles"
            
        if data.phev_sales > 0:
            comment += f"\n- **PHEV Sales**: {data.phev_sales:,} vehicles"
            
        if data.sales_yoy_growth is not None:
            growth_emoji = "📈" if data.sales_yoy_growth > 0 else "📉"
            comment += f"\n\n**📊 Growth:** {growth_emoji} {data.sales_yoy_growth:+.1f}% YoY"
            
        if data.total_exports > 0:
            comment += f"\n\n**🌍 Exports:** {data.total_exports:,} vehicles"
            
        comment += f"\n\n**📄 Source:** [{data.source_title[:80]}...]({data.source_url})"
        comment += f"\n\n*Data extracted by BYD Sentinel - Oreacle Bot*"
        
        return comment
    
    def log_to_spreadsheet(self, data: BYDMonthlyData):
        """Log BYD data to spreadsheet sink."""
        if not self.spreadsheet_sink:
            return
            
        try:
            row = SpreadsheetRow()
            row.doc_url = data.source_url
            row.doc_title = data.source_title
            row.source = "BYD_SENTINEL"
            row.proposed_label = "BYD_MONTHLY_DATA"
            row.confidence = 1.0  # High confidence in structured data
            
            # Store data in key_terms_zh as JSON
            row.key_terms_zh = [json.dumps(data.to_dict())]
            row.action_taken = "COMMENT"
            row.comment_posted = True
            
            self.spreadsheet_sink.append_row(row)
            self.logger.info("Logged BYD data to spreadsheet")
            
        except Exception as e:
            self.logger.error(f"Failed to log BYD data to spreadsheet: {e}")
    
    def run_monthly_check(self, market_ids: List[str] = None, 
                         dry_run: bool = True) -> Dict[str, Any]:
        """
        Run monthly BYD sales/production check.
        
        Args:
            market_ids: List of Manifold market IDs to post to
            dry_run: If True, only logs without posting comments
            
        Returns:
            Dict with check results
        """
        results = {
            'reports_found': 0,
            'comments_posted': 0,
            'errors': []
        }
        
        try:
            # Fetch announcements from both sources
            hkex_announcements = self.fetch_hkex_announcements(days_back=7)
            cninfo_announcements = self.fetch_cninfo_announcements(days_back=7)
            
            all_announcements = hkex_announcements + cninfo_announcements
            self.logger.info(f"Found {len(all_announcements)} total announcements")
            
            # Parse monthly reports
            monthly_reports = []
            for announcement in all_announcements:
                monthly_data = self.parse_monthly_sales_report(announcement)
                if monthly_data:
                    monthly_reports.append(monthly_data)
                    
            results['reports_found'] = len(monthly_reports)
            self.logger.info(f"Parsed {len(monthly_reports)} monthly reports")
            
            # Post comments for each report
            for data in monthly_reports:
                try:
                    comment_text = self.create_monthly_comment(data)
                    
                    if dry_run:
                        self.logger.info(f"DRY RUN - BYD monthly comment: {comment_text[:200]}...")
                    else:
                        # Post to specified markets
                        if market_ids:
                            for market_id in market_ids:
                                comment = Comment(contractId=market_id, content=comment_text)
                                response = self.client.post_comment(comment)
                                self.logger.info(f"Posted BYD monthly comment to market {market_id}")
                                results['comments_posted'] += 1
                                
                    # Log to spreadsheet
                    self.log_to_spreadsheet(data)
                    
                except Exception as e:
                    error_msg = f"Failed to post BYD comment: {e}"
                    self.logger.error(error_msg)
                    results['errors'].append(error_msg)
                    
        except Exception as e:
            error_msg = f"BYD sentinel check failed: {e}"
            self.logger.error(error_msg)
            results['errors'].append(error_msg)
            
        return results


def run_cli():
    """CLI entry point for BYD sentinel - only for direct execution."""
    import os
    import argparse
    
    parser = argparse.ArgumentParser(description="BYD Monthly Sales Sentinel")
    parser.add_argument("--dry-run", action="store_true", help="Only log reports, don't post comments")
    parser.add_argument("--market-ids", nargs="+", help="Manifold market IDs to post to")
    args = parser.parse_args()
    
    # Initialize client
    api_key = os.environ.get("MANIFOLD_API_KEY")
    if not api_key:
        print("Error: MANIFOLD_API_KEY environment variable required")
        return 1
        
    client = ManifoldClient(api_key)
    sentinel = BYDSentinel(client)
    
    results = sentinel.run_monthly_check(
        market_ids=args.market_ids or [],
        dry_run=args.dry_run
    )
    
    print(f"BYD Sentinel Results:")
    print(f"  Reports found: {results['reports_found']}")
    print(f"  Comments posted: {results['comments_posted']}")
    if results['errors']:
        print(f"  Errors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"    - {error}")
    
    return 0


def main():
    """Main function for CLI integration - no argument parsing."""
    import os
    
    # Initialize client
    api_key = os.environ.get("MANIFOLD_API_KEY")
    if not api_key:
        print("Error: MANIFOLD_API_KEY environment variable required")
        return 1
        
    client = ManifoldClient(api_key)
    sentinel = BYDSentinel(client)
    
    # Default behavior: dry run with no specific markets
    results = sentinel.run_monthly_check(market_ids=[], dry_run=True)
    
    print(f"BYD Sentinel Results:")
    print(f"  Reports found: {results['reports_found']}")
    print(f"  Comments posted: {results['comments_posted']}")
    if results['errors']:
        print(f"  Errors: {len(results['errors'])}")
        for error in results['errors']:
            print(f"    - {error}")
    
    return 0


if __name__ == "__main__":
    exit(run_cli())