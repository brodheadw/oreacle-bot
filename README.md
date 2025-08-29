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
   export OPENAI_API_KEY="your_openai_api_key"  # For LLM analysis
   ```

3. **Run the monitor**
   ```bash
   source .env && python src/monitor.py
   ```

## Configuration

### Required Environment Variables
- `MANIFOLD_API_KEY` - Your Manifold Markets API key
- `MARKET_SLUG` - The market to monitor (e.g., "MikhailTal/catl-receives-license-renewal-for-y")

### LLM Integration (Recommended)
- `OPENAI_API_KEY` - OpenAI API key for GPT-4o-mini analysis
- `OREACLE_MODEL` - OpenAI model to use (default: "gpt-4o-mini")
- `OREACLE_MIN_CONFIDENCE` - Minimum confidence for decisions (default: 0.75)

### Legacy Translation (Optional - LLM handles translation internally)
- `DEEPL_API_KEY` - DeepL API key for translation fallback
- `GOOGLE_TRANSLATE_API_KEY` - Google Translate API key fallback

### Other Settings
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

### With LLM Integration (Recommended)
1. **Data Collection**: Scans all three sources every 15 minutes using Chinese keywords
2. **Deduplication**: Uses SQLite database to track previously seen items
3. **LLM Analysis**: GPT-4o-mini analyzes Chinese regulatory documents to determine:
   - **Mine Match**: `JIANXIAWO_MATCH`, `POSSIBLE_MATCH`, `NO_MATCH`
   - **Classification**: `YES_CONDITION`, `NO_CONDITION`, `AMBIGUOUS`, `IRRELEVANT`
   - **Confidence Score**: 0.0-1.0 with evidence quotes and reasoning
   - **Built-in Translation**: Chinese→English with exact quote preservation
4. **Conservative Gates**: Strict decision logic prevents false positives in trading
5. **Rich Comments**: Bilingual analysis with confidence indicators and source links
6. **Optional Trading**: Only executes with high-confidence LLM analysis passing strict gates

### Fallback Mode (No OpenAI Key)
- Uses legacy regex classification and optional DeepL/Google translation
- Less sophisticated but functional for basic keyword detection
- Automatically enabled when `OPENAI_API_KEY` is not provided

### Analysis Pipeline
```
Document → LLM Extraction → Decision Gates → Comment/Trade
           ↓
         - Exact Chinese quotes
         - English translations  
         - Confidence scores
         - Evidence reasoning
         - Risk flags
```

## Architecture & Files

### Core LLM Components
- `src/models.py` - Pydantic schemas for structured LLM outputs
- `src/llm_client.py` - OpenAI client with JSON Schema validation  
- `src/decision.py` - Conservative decision gates for trading safety
- `src/comment_renderer.py` - Rich bilingual comment formatting
- `phrasebook.yml` - Chinese/English term definitions for LLM context

### Legacy Components (Fallback)
- `src/translate.py` - DeepL/Google translation (used when no LLM)
- `src/classify.py` - Regex-based classification (used when no LLM)

### Data Sources & Storage
- `src/sources/cninfo.py` - CATL official filings scraper
- `src/sources/szse.py` - Stock exchange notices scraper  
- `src/sources/jiangxi.py` - Provincial mining authority scraper
- `src/storage.py` - SQLite deduplication database
- `src/client.py` - Manifold Markets API client

### Main Application
- `src/monitor.py` - Main monitoring loop with LLM integration

## Relevant Links

- [Target Manifold Market](https://manifold.markets/MikhailTal/catl-receives-license-renewal-for-y) - The prediction market being monitored
- [CNINFO Portal](https://www.cninfo.com.cn/) - CATL official filings
- [SZSE Disclosure Portal](https://www.szse.cn/disclosure/listed/notice/) - Stock exchange notices
- [Jiangxi Natural Resources](https://bnr.jiangxi.gov.cn/) - Provincial mining authority