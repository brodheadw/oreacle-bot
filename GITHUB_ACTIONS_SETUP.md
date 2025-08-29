# GitHub Actions Setup Guide

This guide will help you set up the Oreacle Bot to run automatically in GitHub Actions every 15 minutes.

## 🔐 1. Add Repository Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions → New repository secret

Add these secrets:

### Required Secrets
- `MANIFOLD_API_KEY` - Your Manifold Markets API key
- `MARKET_SLUG` - Market slug (e.g., `catl-receives-license-renewal-for-y`)
- `OPENAI_API_KEY` - Your OpenAI API key

### Optional Secrets (with defaults)
- `OREACLE_MODEL` - OpenAI model (default: `gpt-4o-mini`)
- `OREACLE_MIN_CONFIDENCE` - Minimum confidence (default: `0.75`)  
- `OREACLE_COMMENT_ONLY` - Disable trading (default: `1`)

## 🚀 2. Enable GitHub Actions

1. Push the `.github/workflows/monitor.yml` file to your repository
2. Go to your repository → Actions tab
3. You should see "Oreacle Bot Monitor" workflow
4. Click "Enable workflow" if prompted

## ⏰ 3. Schedule & Manual Triggers

### Automatic Schedule
- Runs every 15 minutes automatically
- Uses cron schedule: `*/15 * * * *`

### Manual Trigger
- Go to Actions → Oreacle Bot Monitor → Run workflow
- Click "Run workflow" button for immediate execution

## 📊 4. Monitor Execution

### View Logs
1. Go to Actions → Oreacle Bot Monitor
2. Click on any run to see detailed logs
3. Logs will show data fetching, LLM analysis, and comment posting

### Expected Output
```
🤖 Oreacle Bot - Single Cycle Mode (GitHub Actions)
LLM integration: ENABLED
Connected to market: CATL receives license renewal...
CNINFO: Found 2 items
Processing cninfo item: 宜春枧下窝采矿许可证...
LLM Analysis - Proposed: YES_CONDITION, Final: YES_CONDITION, Confidence: 0.85
Posted LLM comment for cninfo item_12345
✅ Single cycle complete. Processed 1 new items.
```

## 💾 5. Database Persistence

**⚠️ Important**: GitHub Actions runners are ephemeral, so the SQLite database resets each run. This means:

- The bot may reprocess items it's seen before
- Consider upgrading to a persistent database for production use
- Alternatively, the deduplication happens quickly due to Manifold's comment system

## 🔧 6. Customization

### Change Schedule
Edit `.github/workflows/monitor.yml` cron schedule:
```yaml
schedule:
  - cron: '0 */2 * * *'  # Every 2 hours
  - cron: '*/30 * * * *'  # Every 30 minutes
```

### Enable Trading
Set `OREACLE_COMMENT_ONLY` secret to `0` to enable trading

### Debug Mode
Add environment variable in workflow:
```yaml
OREACLE_LOG: DEBUG
```

## 🛡️ 7. Security Notes

- All API keys are stored as encrypted GitHub secrets
- Keys are only accessible to the workflow during execution
- Never commit API keys to the repository code
- Rotate keys if you suspect they've been compromised

## 📈 8. Cost Estimates

### GitHub Actions (Free Tier)
- 2,000 minutes/month free for public repos
- ~2 minutes per run × 4 runs/hour × 24 hours × 30 days = ~5,760 minutes/month
- May exceed free tier - consider reducing frequency

### OpenAI API Costs
- ~$0.01-0.10 per document analyzed with GPT-4o-mini
- Very affordable for typical mining announcement volumes

## 🔍 9. Troubleshooting

### Common Issues
1. **No secrets configured**: Check repository secrets are set
2. **Import errors**: Python dependencies not installing correctly
3. **API rate limits**: SZSE/CNINFO may return 429 errors temporarily
4. **Database errors**: tmp directory creation or SQLite issues

### Getting Help
- Check the Actions logs for detailed error messages
- Most issues are related to API key configuration or network timeouts
- The bot is designed to be resilient to individual API failures