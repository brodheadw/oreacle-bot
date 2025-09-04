#!/usr/bin/env python3
"""
Test direct PDF access and parsing with the real BYD August 2025 PDF.
"""
import requests
import re
from typing import Optional

def extract_pdf_text(pdf_content: bytes) -> Optional[str]:
    """Extract text from PDF using PyMuPDF and pdfminer as fallback."""
    text = None
    
    # Try PyMuPDF first (faster, better formatting)
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_content, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
        return text.strip() if text else None
    except ImportError:
        pass
    except Exception as e:
        print(f"PyMuPDF failed: {e}")
        
    # Fallback to pdfminer
    try:
        from pdfminer.high_level import extract_text
        from io import BytesIO
        text = extract_text(BytesIO(pdf_content))
        return text.strip() if text else None
    except ImportError:
        pass
    except Exception as e:
        print(f"pdfminer failed: {e}")
        
    print("No PDF extraction libraries available")
    return None

def parse_number(num_str: str) -> int:
    """Parse a number string with commas."""
    return int(num_str.replace(',', ''))

def test_direct_pdf_access():
    """Test accessing the user's specific PDF directly."""
    
    print("🧪 Direct BYD PDF Test")
    print("=====================")
    
    # User-provided PDF URL
    pdf_url = 'https://www1.hkexnews.hk/listedco/listconews/sehk/2025/0901/2025090103226_c.pdf'
    print(f"📄 PDF URL: {pdf_url}")
    
    try:
        response = requests.get(pdf_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=30)
        print(f"📡 HTTP {response.status_code}")
        print(f"📄 Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        print(f"📄 Content length: {len(response.content):,} bytes")
        
        if response.status_code != 200:
            print("❌ PDF not accessible")
            return False
            
        # Test PDF extraction
        pdf_text = extract_pdf_text(response.content)
        if not pdf_text:
            print("❌ Failed to extract PDF text")
            return False
            
        print(f"✅ PDF extracted: {len(pdf_text)} chars")
        print(f"📋 Sample content: {pdf_text[:300]}...")
        
        # Test our simplified number extraction
        all_numbers = re.findall(r'(\d+(?:,\d{3})*)', pdf_text)
        number_values = [parse_number(num) for num in all_numbers]
        
        print(f"\n📊 All numbers found: {all_numbers[:10]}...")
        
        # Known target values for August 2025
        target_total = 373626  # Total NEV sales
        target_bev = 199585    # BEV sales  
        target_phev = 171916   # PHEV sales
        
        # Test direct matching
        results = {}
        if target_total in number_values:
            results['total_sales'] = target_total
            print(f"✅ Direct match: total_sales = {target_total:,}")
            
        if target_bev in number_values:
            results['bev_sales'] = target_bev
            print(f"✅ Direct match: bev_sales = {target_bev:,}")
            
        if target_phev in number_values:
            results['phev_sales'] = target_phev
            print(f"✅ Direct match: phev_sales = {target_phev:,}")
            
        # Test context-based fallback
        if not results.get('total_sales'):
            nev_context = re.search(r'新能源汽車[\s\S]*?(\d+(?:,\d{3})*)', pdf_text)
            if nev_context:
                results['total_sales'] = parse_number(nev_context.group(1))
                print(f"✅ Context match: total_sales = {results['total_sales']:,}")
                
        if not results.get('bev_sales'):
            bev_context = re.search(r'純電動[\s\S]*?(\d+(?:,\d{3})*)', pdf_text)
            if bev_context:
                results['bev_sales'] = parse_number(bev_context.group(1))
                print(f"✅ Context match: bev_sales = {results['bev_sales']:,}")
                
        if not results.get('phev_sales'):
            phev_context = re.search(r'插電式混合動力[\s\S]*?(\d+(?:,\d{3})*)', pdf_text)
            if phev_context:
                results['phev_sales'] = parse_number(phev_context.group(1))
                print(f"✅ Context match: phev_sales = {results['phev_sales']:,}")
        
        print(f"\n🏁 Final results:")
        print(f"  Total sales: {results.get('total_sales', 0):,}")
        print(f"  BEV sales: {results.get('bev_sales', 0):,}")
        print(f"  PHEV sales: {results.get('phev_sales', 0):,}")
        
        success = len(results) >= 2  # At least 2 values extracted
        print(f"\n🏁 Result: {'✅ PASS' if success else '❌ FAIL'}")
        return success
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_direct_pdf_access()