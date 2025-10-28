# Kalshi Mention Markets - Event-Based Analysis Guide

## Overview

The Kalshi Mention Markets research tool now correctly groups markets by **event** (e.g., "What will Apple say during earnings?") and shows the individual **bet words** (e.g., "AI", "revenue", "shutdown") as separate markets within each event group.

## Key Structure

### ✅ **Event-Based Grouping**
- **Event**: The main question/topic (e.g., "What will Apple say during earnings?")
- **Bet Markets**: Individual markets for different words/phrases that might be mentioned
- **Bet Words**: The actual words being bet on (extracted from ticker symbols)

### ✅ **Example Structure**
```
Event: "What will Apple say during earnings?"
├── Bet: "AI" (Bid/Ask: 45/55, Vol: $1,200)
├── Bet: "revenue" (Bid/Ask: 30/40, Vol: $800)
├── Bet: "shutdown" (Bid/Ask: 15/25, Vol: $500)
└── ... 10 more bet options
```

## Usage Examples

### 1. Interactive Mode
```bash
source venv/bin/activate && python main.py
```

Commands:
```
[kalshi-research] markets          # Show events and their bet markets
[kalshi-research] analyze 1        # Analyze all bets for event 1
[kalshi-research] research 2       # Research all bets for event 2
[kalshi-research] summary 3        # Generate summary for event 3
```

### 2. Demo Script
```bash
source venv/bin/activate && python demo_grouped_analysis.py
```

## Sample Output

```
📢 Mention Markets by Event
================================================================================
╭─────────────────────────────── Event Group 1 ────────────────────────────────╮
│ Event 1: What will the announcers say during the Green Bay at Pittsburgh pro │
│ football game?                                                               │
│ Number of bet markets: 26                                                    │
│                                                                              │
│ Available Bets:                                                              │
│   • INTE | Bid/Ask: 24/38 | Vol: $159                                        │
│   • WILD | Bid/Ask: 20/60 | Vol: $231                                        │
│   • WHTC | Bid/Ask: 35/36 | Vol: $2,667                                      │
│   • VETE | Bid/Ask: 90/91 | Vol: $915                                        │
│   • TURF | Bid/Ask: 47/50 | Vol: $2,523                                      │
│   ... and 21 more bet options                                                │
│                                                                              │
│ Data Pipeline Options:                                                       │
│   • Run AI analysis: analyze 1                                               │
│   • Get news & transcripts: research 1                                       │
│   • View price history: prices 1                                             │
│   • Generate summary: summary 1                                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Data Pipeline Capabilities

### AI Analysis (`analyze <event_number>`)
- **Bet Word Analysis**: Sentiment analysis of each bet word
- **Cross-Bet Analysis**: Price trends across all bets for the event
- **Volume Patterns**: Trading volume analysis for each bet
- **Risk Assessment**: Risk evaluation for each bet word
- **Correlation Analysis**: How bets relate to each other
- **Confidence Scoring**: Prediction confidence for each bet

### Research Pipeline (`research <event_number>`)
- **Event Research**: News articles about the specific event
- **Bet Word Research**: News mentioning each specific bet word
- **Transcript Analysis**: Past speeches/transcripts mentioning these words
- **Social Media**: Sentiment for each bet word
- **Historical Data**: Similar events and their outcomes
- **Market Correlations**: How similar bets performed historically

### AI Summary (`summary <event_number>`)
- **Event Overview**: Key metrics for the entire event
- **Bet Analysis**: Individual analysis of each bet word
- **Price Trends**: Cross-bet price movement analysis
- **Volume Assessment**: Liquidity analysis for each bet
- **Risk Factors**: Opportunities and risks for each bet
- **Trading Recommendations**: Specific recommendations for each bet word
- **Correlation Insights**: How bets might influence each other

## Technical Details

- **Event Grouping**: Groups by `event_title` field from API
- **Bet Word Extraction**: Extracts from ticker symbols (last part after dash)
- **Date Filtering**: Only shows active markets closing today or later
- **Status Verification**: Ensures markets are tradeable with bid/ask prices
- **Error Handling**: Graceful handling of API errors and invalid inputs

## Current Results

- **26 active mention markets** grouped into **1 main event**:
  - Green Bay vs Pittsburgh football game (26 bet markets)
  - Bet words: INTE, WILD, WHTC, VETE, TURF, TIE, STUF, STEE, SPED, SAFE, etc.

## Next Steps

1. **Run the interactive CLI**: `python main.py`
2. **View event groups**: Use `markets` command
3. **Analyze specific events**: Use `analyze 1`, `research 1`, etc.
4. **Extend data pipelines**: Add more sophisticated analysis features
5. **Add more data sources**: Integrate news, transcripts, social media

This system provides a powerful foundation for researching mention markets by event, making it easy to run comprehensive analysis on all related bet markets for a specific event.

