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

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

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
        Fetch recent BYD announcements from HKEXnews using titlesearch (server-rendered).
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of announcement dictionaries
        """
        if BeautifulSoup is None:
            raise ImportError("beautifulsoup4 not installed - run: pip install beautifulsoup4")
        
        return self._fetch_hkex_probe(days_back)
    
    def _fetch_hkex_probe(self, days_back: int = 7) -> List[Dict]:
        """
        HKEX directory probe: directly try known PDF URL patterns instead of broken search APIs.
        BYD typically posts monthly reports on the 1st of the following month in HKT.
        """
        from datetime import datetime, timedelta
        try:
            from zoneinfo import ZoneInfo
        except ImportError:
            ZoneInfo = None
            
        hits = []
        tz = ZoneInfo("Asia/Hong_Kong") if ZoneInfo else None
        now_hkt = datetime.now(tz) if tz else datetime.utcnow()
        
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0"})
        
        # Check recent days for PDF posting patterns
        for day_offset in range(days_back):
            check_date = now_hkt - timedelta(days=day_offset)
            year = check_date.year
            month = check_date.month
            day = check_date.day
            
            # Try HKEX directory probe for this date
            probe_hits = self._hkex_probe_window(session, year, month, day)
            if probe_hits:
                hits.extend(probe_hits)
                self.logger.info(f"📄 HKEX probe found {len(probe_hits)} PDFs for {year}-{month:02d}-{day:02d}")
                
        self.logger.info(f"📄 Total HKEX probe hits: {len(hits)}")
        return hits
    
    def _hkex_probe_window(self, session: requests.Session, year: int, month: int, day: int, 
                          start: str = "03220", end: str = "03250") -> List[Dict]:
        """
        Probe HKEX directory for BYD monthly PDFs in a narrow numeric window.
        Based on known pattern: /sehk/YYYY/MMDD/YYYYMMDD####_c.pdf
        """
        base = f"https://www1.hkexnews.hk/listedco/listconews/sehk/{year}/{month:02d}{day:02d}"
        hits = []
        
        # Narrow range based on known August pattern: 2025090103226_c.pdf (03226)
        for suffix in range(int(start), int(end) + 1, 2):  # Step by 2 for targeted search
            for lang in ("_c.pdf", "_e.pdf"):
                url = f"{base}/{year}{month:02d}{day:02d}{suffix:05d}{lang}"
                try:
                    # Fast HEAD request to check if PDF exists
                    head_response = session.head(url, timeout=8)
                    if head_response.status_code != 200:
                        continue
                        
                    # Found PDF on expected BYD posting date - trust it
                    # BYD typically posts monthly reports on 1st of following month
                    if day == 1:  # Only trust PDFs found on 1st of month (typical BYD posting day)
                        self.logger.info(f"✅ HKEX probe found PDF on BYD posting day: {url}")
                        hits.append({
                            "announcementTitle": f"Monthly production/sales {year}-{month:02d} (detected by date probe)",
                            "adjunctUrl": url,
                            "content": "",
                            "publishDate": f"{year}-{month:02d}-{day:02d}",
                            "lang": "ZH" if lang == "_c.pdf" else "EN",
                            "source": "HKEX_PROBE"
                        })
                        # Continue to find all PDFs, don't return early
                        
                except Exception:
                    continue  # Silently continue to next suffix
                    
        return hits
    
    def _passes_title_filter(self, announcement: Dict) -> bool:
        """Check if announcement title passes initial monthly sales filter."""
        title = announcement.get('announcementTitle', '')
        
        # Check if this is a monthly sales/production report (case-insensitive matching)
        monthly_keywords = [
            'monthly sales', 'monthly production', 'monthly delivery',
            '月度销量', '月度產銷', '月度产量', '月度產量', 
            '产销快报', '產銷快報', '销量快报', '銷量快報',
            'sales volume', 'production volume',
            'production and sales volume', 'voluntary announcement'
        ]
        
        # Case-insensitive matching for English, exact matching for Chinese
        title_lower = title.lower()
        
        # Test both case-insensitive (for English) and exact (for Chinese)
        english_keywords = [kw for kw in monthly_keywords if all(ord(char) < 256 for char in kw)]
        chinese_keywords = [kw for kw in monthly_keywords if not all(ord(char) < 256 for char in kw)]
        
        english_match = any(keyword.lower() in title_lower for keyword in english_keywords)
        chinese_match = any(keyword in title for keyword in chinese_keywords)
        
        return english_match or chinese_match
    
    def _diagnose_parse_failure(self, announcement: Dict) -> str:
        """Diagnose why monthly data parsing failed."""
        title = announcement.get('announcementTitle', '')
        content = announcement.get('content', '')
        
        if not content:
            return "no content available"
            
        # Check for key Chinese terms
        if not re.search(r'(新能源汽車|纯电动|插电式混合动力|產銷|产销)', content):
            return "missing key Chinese terms (新能源汽車/產銷)"
            
        # Check for numbers
        numbers = re.findall(r'(\d+(?:,\d{3})*)', content)
        if not numbers:
            return "no comma-formatted numbers found"
            
        if len(numbers) < 3:
            return f"too few numbers ({len(numbers)} found, need ≥3 for total/BEV/PHEV)"
            
        # Check for period extraction
        if not re.search(r'(20\d{2}).*?([0-9]{1,2}).*?(月|MONTH)', content, re.I):
            return "period not detected (no YYYY-MM pattern)"
            
        return "unknown parsing failure"
    
    def fetch_byd_ir_latest(self) -> List[Dict]:
        """
        Primary discovery: BYD IR latest announcements (static HTML).
        Follow 'Latest Announcements' link to find actual announcements.
        """
        base_url = "https://www.bydglobal.com/cn/en/BYD_ENInvestor/InvestorNotice_mob.html"
        self.logger.info(f"🌐 BYD IR fetch: {base_url}")
        
        try:
            response = requests.get(base_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            response.raise_for_status()
        except Exception as e:
            self.logger.warning(f"BYD IR base page fetch failed: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Look for "Latest Announcements" link to follow
        announcements_link = None
        for a in soup.find_all("a", href=True):
            text = a.get_text(strip=True)
            if "Latest Announcements" in text or "Announcements" in text:
                announcements_link = a["href"]
                if not announcements_link.startswith("http"):
                    announcements_link = "https://www.bydglobal.com" + announcements_link
                self.logger.info(f"🔗 Found announcements link: {announcements_link}")
                break
        
        if not announcements_link:
            # Fallback: try common announcement page URLs
            potential_urls = [
                "https://www.bydglobal.com/cn/en/BYD_ENInvestor/announcement.html",
                "https://www.bydglobal.com/en/Investor-Relations/announcements",
                "https://www.bydglobal.com/announcements",
            ]
            self.logger.info("🔍 No announcements link found, trying fallback URLs")
        else:
            potential_urls = [announcements_link]
        
        hits = []
        
        # Try each potential announcements page  
        for url in potential_urls:
            self.logger.info(f"🌐 Trying announcements page: {url}")
            try:
                response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
                if response.status_code != 200:
                    self.logger.info(f"📡 HTTP {response.status_code} for {url}")
                    continue
                    
                soup = BeautifulSoup(response.text, "html.parser")
                anchors = soup.find_all("a", href=True)
                self.logger.info(f"🔍 Scanning {len(anchors)} anchors on announcements page")
                
                # Show sample for debugging
                sample_titles = []
                for i, a in enumerate(anchors[:10]):
                    title = " ".join(a.get_text(strip=True).split())
                    if title and len(title) > 8:
                        sample_titles.append(f"  {i+1}. {title[:80]}")
                if sample_titles:
                    self.logger.info(f"📋 Sample announcements:\n" + "\n".join(sample_titles))
                
                # Look for monthly sales/production announcements
                for a in anchors:
                    title = " ".join(a.get_text(strip=True).split())
                    if not title or len(title) < 8:
                        continue
                        
                    # Match monthly production/sales announcements
                    is_monthly = (
                        "PRODUCTION AND SALES VOLUME" in title.upper()
                        or re.search(r"(產銷快報|产销快报|月度产销)", title)
                        or ("2025" in title and "august" in title.lower())
                    )
                    
                    if is_monthly:
                        href = a["href"]
                        if not href.startswith("http"):
                            href = "https://www.bydglobal.com" + href
                            
                        self.logger.info(f"✅ MATCHED BYD IR: {title}")
                        hits.append({
                            "announcementTitle": title,
                            "adjunctUrl": href,
                            "content": "",  # Will be fetched from PDF
                            "publishDate": "",  # Unknown from this page
                            "lang": "EN", 
                            "source": "BYD_IR",
                        })
                        
                if hits:
                    break  # Found announcements, no need to try other URLs
                    
            except Exception as e:
                self.logger.warning(f"Failed to fetch announcements from {url}: {e}")
                continue
                
# Removed temporary mock - now using real server-rendered HKEX discovery
        
        self.logger.info(f"BYD IR hits: {len(hits)}")
        return hits
    
    def _follow_to_pdf_and_extract(self, announcement: Dict) -> Optional[Dict]:
        """
        Follow through to final PDF and extract text content.
        
        If URL is HKEX HTML announcement, find PDF link and follow it.
        If URL is already PDF, extract text directly.
        Returns enriched announcement with content or None if failed.
        """
        url = announcement.get('adjunctUrl', '')
        if not url:
            return announcement
            
        self.logger.info(f"📄 Following through: {url[:60]}...")
        
        try:
            # Try to fetch the URL
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            response.raise_for_status()
            
            # Check if this is already a PDF
            content_type = response.headers.get('content-type', '').lower()
            is_pdf = 'pdf' in content_type or url.lower().endswith('.pdf')
            
            if is_pdf:
                # Extract text from PDF
                self.logger.info("📄 Extracting text from PDF...")
                pdf_text = self._extract_pdf_text(response.content)
                if pdf_text:
                    announcement['content'] = pdf_text
                    self.logger.info(f"📄 Extracted {len(pdf_text)} chars from PDF")
                else:
                    self.logger.warning("📄 PDF text extraction failed")
                return announcement
                
            else:
                # This is HTML - look for PDF links
                soup = BeautifulSoup(response.text, "html.parser")
                pdf_links = []
                
                # Find all links that might be PDFs
                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    link_text = a.get_text(strip=True)
                    
                    # Check if this looks like a PDF link
                    is_pdf_link = (
                        href.lower().endswith('.pdf') 
                        or 'pdf' in href.lower()
                        or 'announcement' in link_text.lower()
                        or 'document' in link_text.lower()
                    )
                    
                    if is_pdf_link:
                        if not href.startswith('http'):
                            if href.startswith('/'):
                                href = 'https://www1.hkexnews.hk' + href
                            else:
                                base_url = '/'.join(url.split('/')[:-1])
                                href = base_url + '/' + href
                        pdf_links.append((href, link_text))
                
                # Try the first PDF link found
                if pdf_links:
                    pdf_url, pdf_text = pdf_links[0]
                    self.logger.info(f"📄 Found PDF link: {pdf_url}")
                    
                    # Follow to PDF
                    pdf_response = requests.get(pdf_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
                    pdf_response.raise_for_status()
                    
                    # Extract text from PDF
                    pdf_content = self._extract_pdf_text(pdf_response.content)
                    if pdf_content:
                        announcement['content'] = pdf_content
                        announcement['adjunctUrl'] = pdf_url  # Update to final PDF URL
                        self.logger.info(f"📄 Extracted {len(pdf_content)} chars from linked PDF")
                    else:
                        # Fall back to HTML content if PDF extraction fails
                        announcement['content'] = soup.get_text()
                        self.logger.info(f"📄 PDF extraction failed, using HTML text ({len(announcement['content'])} chars)")
                else:
                    # No PDF found, use HTML content
                    announcement['content'] = soup.get_text()  
                    self.logger.info(f"📄 No PDF found, using HTML content ({len(announcement['content'])} chars)")
                    
                return announcement
                
        except Exception as e:
            self.logger.warning(f"Failed to follow through {url[:50]}: {e}")
            return announcement  # Return original on failure
    
    def _extract_pdf_text(self, pdf_content: bytes) -> Optional[str]:
        """
        Extract text from PDF content bytes.
        Uses simple fallback approach - can be enhanced with proper PDF libraries.
        """
        try:
            # Try to use PyMuPDF if available
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(stream=pdf_content, filetype="pdf")
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
                return text.strip()
            except ImportError:
                pass
                
            # Try pdfminer.six if available
            try:
                from pdfminer.high_level import extract_text
                from io import BytesIO
                text = extract_text(BytesIO(pdf_content))
                return text.strip()
            except ImportError:
                pass
                
            # Simple fallback - look for readable text in PDF bytes
            # This is crude but can catch basic text-based PDFs
            text_content = pdf_content.decode('latin-1', errors='ignore')
            
            # Extract text between common PDF text markers
            import re
            text_matches = re.findall(r'\(([^)]+)\)', text_content)
            if text_matches:
                extracted = ' '.join(text_matches)
                # Filter out garbage and keep only meaningful text
                meaningful = re.sub(r'[^\w\s\u4e00-\u9fff.,()%:：\-—]+', ' ', extracted)
                if len(meaningful) > 100:  # Only return if we got substantial text
                    return meaningful.strip()
                    
            self.logger.warning("📄 No PDF libraries available and fallback extraction found insufficient text")
            return None
            
        except Exception as e:
            self.logger.warning(f"📄 PDF text extraction failed: {e}")
            return None
    
    def _dedupe_by_url(self, announcements: List[Dict]) -> List[Dict]:
        """
        Deduplicate announcements by final URL to avoid duplicate processing.
        Keeps the first occurrence of each unique URL.
        """
        seen_urls = set()
        deduped = []
        
        for ann in announcements:
            url = ann.get('adjunctUrl', '')
            # Normalize URL for comparison
            normalized_url = url.lower().strip()
            
            if normalized_url and normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                deduped.append(ann)
            elif normalized_url in seen_urls:
                self.logger.debug(f"🔄 Skipping duplicate URL: {url[:50]}...")
        
        self.logger.info(f"📋 Deduplication: {len(announcements)} -> {len(deduped)} announcements")
        return deduped
    
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
        title = announcement.get('announcementTitle', '')
        content = announcement.get('content', '')
        
        # Check if this is a monthly sales/production report (case-insensitive matching)
        monthly_keywords = [
            'monthly sales', 'monthly production', 'monthly delivery',
            '月度销量', '月度產銷', '月度产量', '月度產量', 
            '产销快报', '產銷快報', '销量快报', '銷量快報',
            'sales volume', 'production volume',
            'production and sales volume', 'voluntary announcement'
        ]
        
        # Case-insensitive matching for English, exact matching for Chinese
        title_lower = title.lower()
        
        # Test both case-insensitive (for English) and exact (for Chinese)
        english_keywords = [kw for kw in monthly_keywords if all(ord(char) < 256 for char in kw)]
        chinese_keywords = [kw for kw in monthly_keywords if not all(ord(char) < 256 for char in kw)]
        
        english_match = any(keyword.lower() in title_lower for keyword in english_keywords)
        chinese_match = any(keyword in title for keyword in chinese_keywords)
        
        is_monthly = english_match or chinese_match
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
        
        # Extract from Traditional Chinese table format (BYD's actual format)
        # Look for the table structure with 本月 (current month) sales column
        
        # Simplified approach: Extract all comma-formatted numbers and identify them by context
        all_numbers = re.findall(r'(\d+(?:,\d{3})*)', content)
        number_values = [self._parse_number(num) for num in all_numbers]
        
        self.logger.debug(f"📊 Found numbers in PDF: {all_numbers}")
        
        # Context-based extraction: Find sales numbers after key Chinese terms
        # NEV total after "新能源汽車"
        nev_context = re.search(r'新能源汽車[\s\S]*?(\d+(?:,\d{3})*)', content)
        if nev_context:
            data.total_sales = self._parse_number(nev_context.group(1))
            data.nev_sales = data.total_sales  # For BYD, NEV = total (no ICE vehicles)
            self.logger.info(f"✅ Extracted total_sales: {data.total_sales:,}")
            
        # BEV after "純電動"  
        bev_context = re.search(r'純電動[\s\S]*?(\d+(?:,\d{3})*)', content)
        if bev_context:
            data.bev_sales = self._parse_number(bev_context.group(1))
            self.logger.info(f"✅ Extracted bev_sales: {data.bev_sales:,}")
            
        # PHEV after "插電式混合動力"
        phev_context = re.search(r'插電式混合動力[\s\S]*?(\d+(?:,\d{3})*)', content)
        if phev_context:
            data.phev_sales = self._parse_number(phev_context.group(1))
            self.logger.info(f"✅ Extracted phev_sales: {data.phev_sales:,}")
            
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
            # Use extended date window to account for HKT timezone (UTC+8)
            # When it's morning in US, it might already be evening of next day in HKT
            # Also need larger window for HKEX probe to catch monthly reports posted on 1st
            extended_days_back = 7  # 7-day window to catch monthly reports
            self.logger.info(f"🕐 Using {extended_days_back}-day window to catch monthly reports and HKT timezone (UTC+8)")
            
            # Discovery: CNINFO (primary), HKEX probe (secondary), BYD IR (best-effort)
            cninfo_hits = self.fetch_cninfo_announcements(days_back=extended_days_back)
            hkex_hits = self._fetch_hkex_probe(days_back=extended_days_back) 
            byd_ir_hits = self.fetch_byd_ir_latest()
            
            # Merge and deduplicate by URL to avoid duplicates  
            candidates = self._dedupe_by_url(cninfo_hits + hkex_hits + byd_ir_hits)
            
            self.logger.info(f"📊 Discovery: CNINFO={len(cninfo_hits)} HKEX_PROBE={len(hkex_hits)} BYD_IR={len(byd_ir_hits)} total={len(candidates)}")
            
            # Show first 3 candidates for debugging
            if candidates:
                self.logger.info("📋 First 3 candidates:")
                for i, candidate in enumerate(candidates[:3]):
                    title = candidate.get('announcementTitle', 'No title')[:80]
                    url = candidate.get('adjunctUrl', 'No URL')[:60]
                    source = candidate.get('source', 'Unknown')
                    self.logger.info(f"  {i+1}. [{source}] {title}... → {url}...")
            else:
                self.logger.warning("❌ No discovery candidates found from any source")
            
            # Follow through to PDFs and extract content for each candidate
            all_announcements = []
            for i, candidate in enumerate(candidates):
                title = candidate.get('announcementTitle', 'No title')[:60]
                try:
                    # Follow through to final PDF if needed and extract content
                    enriched = self._follow_to_pdf_and_extract(candidate)
                    if enriched and enriched.get('content'):
                        chars = len(enriched['content'])
                        self.logger.info(f"✅ PDF extracted {i+1}/{len(candidates)}: {chars} chars from {title}")
                        all_announcements.append(enriched)
                    elif enriched:
                        self.logger.warning(f"⚠️  PDF follow failed {i+1}/{len(candidates)}: no content from {title}")
                        all_announcements.append(candidate)  # Keep original
                    else:
                        self.logger.warning(f"❌ PDF follow failed {i+1}/{len(candidates)}: {title}")
                        all_announcements.append(candidate)  # Keep original
                        
                except Exception as e:
                    self.logger.error(f"❌ PDF follow error {i+1}/{len(candidates)}: {title} → {e}")
                    all_announcements.append(candidate)  # Keep original even if PDF extraction fails
                    
            self.logger.info(f"📊 After PDF follow-through: {len(all_announcements)} announcements with content")
            
            # Parse monthly reports with explicit skip reasons
            monthly_reports = []
            for i, announcement in enumerate(all_announcements):
                title = announcement.get('announcementTitle', 'No title')[:60]
                content = announcement.get('content', '')
                
                # Test title filter first
                if not self._passes_title_filter(announcement):
                    skip_reason = "title filter failed (no monthly/sales keywords)"
                    self.logger.info(f"❌ Skip {i+1}/{len(all_announcements)}: {skip_reason} → {title}")
                    continue
                
                monthly_data = self.parse_monthly_sales_report(announcement)
                
                if not monthly_data:
                    # Determine specific skip reason
                    skip_reason = self._diagnose_parse_failure(announcement)
                    self.logger.info(f"❌ Skip {i+1}/{len(all_announcements)}: {skip_reason} → {title}")
                    continue
                
                # Success - show what was parsed
                self.logger.info(f"✅ Parsed {i+1}/{len(all_announcements)}: total={monthly_data.total_sales:,} "
                               f"BEV={monthly_data.bev_sales:,} PHEV={monthly_data.phev_sales:,} "
                               f"period={monthly_data.period} → {title}")
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
                                comment = Comment(contractId=market_id, markdown=comment_text)
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