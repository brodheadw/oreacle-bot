# Oreacle Bot

A monitoring bot that tracks Chinese regulatory sources for CATL lithium mine license updates and automatically posts analysis to Manifold Markets.

## Overview

Oreacle-bot v1.0 monitors the exact sources cited in the ["CATL receives license renewal for Yichun Lithium mine by x"](https://manifold.markets/MikhailTal/catl-receives-license-renewal-for-y) prediction market:

- **CNINFO** - Official CATL (300750.SZ) company disclosures
- **SZSE** - Shenzhen Stock Exchange notices  
- **Jiangxi Natural Resources** - Provincial mining rights announcements

The bot automatically translates Chinese documents, classifies their relevance (e.g., "provisional approval allowing restart" vs "exploration only"), and posts concise, cited updates as Manifold comments with optional rule-based trading.

## Quick Start

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables**
   ```bash
   export MANIFOLD_API_KEY="your_manifold_api_key"
   export MARKET_SLUG="MikhailTal/catl-receives-license-renewal-for-y"
   export DEEPL_API_KEY="your_deepl_key"  # Optional: for translation
   ```

3. **Run the monitor**
   ```bash
   python src/monitor.py
   ```

## Configuration

### Required Environment Variables
- `MANIFOLD_API_KEY` - Your Manifold Markets API key
- `MARKET_SLUG` - The market to monitor (e.g., "MikhailTal/catl-receives-license-renewal-for-y")

### Optional Environment Variables
- `DEEPL_API_KEY` - DeepL API key for translation (recommended)
- `GOOGLE_TRANSLATE_API_KEY` - Google Translate API key (fallback)
- `OREACLE_COMMENT_ONLY` - Set to "1" to disable trading (default: "1")
- `OREACLE_INTERVAL` - Check interval in seconds (default: 900)
- `OREACLE_DB` - SQLite database path (default: "./tmp/oreacle.db")
- `OREACLE_LOG` - Log level: DEBUG, INFO, WARNING, ERROR (default: "INFO")

## Data Sources

### CNINFO (China Securities Information)
- **URL**: https://www.cninfo.com.cn/
- **Purpose**: Official CATL company filings and announcements
- **Keywords**: Chinese terms for mining permits, renewals, production status

### SZSE (Shenzhen Stock Exchange)  
- **URL**: https://www.szse.cn/disclosure/listed/notice/
- **Purpose**: Exchange notices related to CATL (300750.SZ)
- **Scope**: Regulatory notices and company announcements

### Jiangxi Natural Resources Department
- **URLs**: 
  - https://bnr.jiangxi.gov.cn/jxszrzyt/kyqjygggs/kyqjygsg/
  - https://bnr.jiangxi.gov.cn/jxszrzyt/ckqcrgggs/ckqcrgsg/
  - https://www.yichun.gov.cn/ycsrmzf/gytdsyqhkyqcr/
- **Purpose**: Mining rights transactions and permits for Yichun region
- **Focus**: License renewals, exploration permits, production approvals

## How It Works

1. **Data Collection**: Scans all three sources every 15 minutes using Chinese keywords
2. **Deduplication**: Uses SQLite database to track previously seen items
3. **Translation**: Automatically translates Chinese text to English
4. **Classification**: Analyzes content using regex patterns to determine:
   - `YES_CONDITION` - License renewals, production approvals
   - `NO_CONDITION` - Exploration only, production suspensions  
   - `IRRELEVANT` - No regional relevance
   - `AMBIGUOUS` - Unclear status
5. **Action**: Posts formatted comments with source links and analysis

## Relevant Links

- [Target Manifold Market](https://manifold.markets/MikhailTal/catl-receives-license-renewal-for-y) - The prediction market being monitored
- [CNINFO Portal](https://www.cninfo.com.cn/) - CATL official filings
- [SZSE Disclosure Portal](https://www.szse.cn/disclosure/listed/notice/) - Stock exchange notices
- [Jiangxi Natural Resources](https://bnr.jiangxi.gov.cn/) - Provincial mining authority