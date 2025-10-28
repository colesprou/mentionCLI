# Kalshi Mention Markets - Grouped Analysis Guide

## Overview

The Kalshi Mention Markets research tool now groups markets by their title/topic, allowing you to run data pipelines and AI analysis on related markets as a group rather than individually.

## Key Features

### ✅ **Smart Grouping**
- Markets are automatically grouped by their title (e.g., "What will Apple say during earnings?")
- Each group contains all related markets for that specific topic
- Shows market count, tickers, status, bid/ask prices, and volume

### ✅ **Data Pipeline Commands**
After running `markets` or `mentions`, you can use:

- `analyze <group_number>` - Run AI analysis on a market group
- `research <group_number>` - Run research pipeline on a market group  
- `summary <group_number>` - Generate AI summary for a market group

### ✅ **Accurate Filtering**
- Only shows markets that are currently open/active
- Filters by close date (today or later)
- Ensures markets have actual bid/ask prices (tradeable)

## Usage Examples

### 1. Interactive Mode
```bash
source venv/bin/activate && python main.py
```

Then use commands:
```
[kalshi-research] markets
[kalshi-research] analyze 1
[kalshi-research] research 2
[kalshi-research] summary 3
```

### 2. Demo Script
```bash
source venv/bin/activate && python demo_grouped_analysis.py
```

### 3. Direct Testing
```bash
source venv/bin/activate && python test_cli.py
```

## Sample Output

```
📢 Mention Markets by Topic
================================================================================
╭─────────────────────────────── Market Group 1 ───────────────────────────────╮
│ Topic 1: What will Microsoft Corporation say during their next earnings call?│
│ Number of markets: 17                                                        │
│   1. KXEARNINGSMENTIONMSFT-25OCT29-SHUT | Status: active | Bid/Ask: 12/21 |  │
│ Vol: $114                                                                    │
│   2. KXEARNINGSMENTIONMSFT-25OCT29-WIND | Status: active | Bid/Ask: 95/96 |  │
│ Vol: $274                                                                    │
│   ... and 14 more markets                                                    │
│                                                                              │
│ Data Pipeline Options:                                                       │
│   • Run AI analysis: analyze 1                                               │
│   • Get news & transcripts: research 1                                       │
│   • View price history: prices 1                                             │
│   • Generate summary: summary 1                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Data Pipeline Capabilities

### AI Analysis (`analyze <group>`)
- Sentiment analysis of market titles
- Price trend analysis across related markets
- Volume pattern analysis
- Risk assessment
- Prediction confidence scoring

### Research Pipeline (`research <group>`)
- News articles related to the topic
- Past transcripts and speeches
- Social media sentiment
- Historical price data
- Related market analysis

### AI Summary (`summary <group>`)
- Market overview and key metrics
- Price trend analysis
- Volume and liquidity assessment
- Risk factors and opportunities
- Trading recommendations
- Related news and events

## Technical Details

- **API Integration**: Uses Kalshi API with proper authentication
- **Date Filtering**: Only shows markets closing today or later
- **Status Verification**: Ensures markets are truly active/tradeable
- **Grouping Logic**: Groups by exact title match
- **Error Handling**: Graceful handling of API errors and invalid inputs

## Next Steps

1. **Run the interactive CLI**: `python main.py`
2. **View grouped markets**: Use `markets` command
3. **Analyze specific groups**: Use `analyze 1`, `research 2`, etc.
4. **Extend data pipelines**: Add more sophisticated analysis features
5. **Add more data sources**: Integrate news, transcripts, social media

This system provides a powerful foundation for researching mention markets by topic, making it easy to run comprehensive analysis on related markets as a group.

