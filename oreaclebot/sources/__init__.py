"""
Data source scrapers for Chinese regulatory websites.

This subpackage contains scrapers for:
- CNINFO: Official CATL company filings and announcements
- SZSE: Shenzhen Stock Exchange notices
- Jiangxi: Provincial mining rights announcements
"""

from .cninfo import fetch_cninfo
from .szse import fetch_szse
from .jiangxi import fetch_jiangxi

__all__ = ["fetch_cninfo", "fetch_szse", "fetch_jiangxi"]
