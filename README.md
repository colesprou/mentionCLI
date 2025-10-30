# MentionCLI - Kalshi Mention Market Research Tool

A powerful terminal-based research platform for analyzing Kalshi mention markets. Discover edge in prediction markets by analyzing historical patterns, AI-powered insights, and comprehensive data pipelines.

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/colesprou/mentionCLI.git
cd mentionCLI

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file (copy from `env.example`):

```bash
cp env.example .env
```

Add your API keys to `.env`:

```env
# Kalshi API (Required)
KALSHI_API_KEY=your_kalshi_key_here

# API Ninjas (Required for earnings transcripts)
API_NINJAS_KEY=your_api_ninjas_key_here

# OpenAI (Optional - for AI analysis)
OPENAI_API_KEY=your_openai_key_here
```

### 3. Run

```bash
python main.py
```

## 📖 How to Use

### Basic Workflow

1. **Show mention markets:**
   ```
   markets 10
   ```
   Shows top 10 mention markets by volume traded

2. **Research an event:**
   ```
   research 1
   ```
   Analyze event #1 (e.g., earnings call, press conference)

3. **Deep dive on a term:**
   ```
   deepdive 1 "AI"
   ```
   Deep analysis of specific term with historical trends

4. **Search transcripts:**
   ```
   transcript search SBUX protein
   ```
   Search for terms in company transcripts

## Key Commands

### Market Commands

| Command | Description | Example |
|---------|-------------|---------|
| `markets N` | Show top N markets by volume | `markets 10` |
| `research i` | Research event i | `research 1` |
| `deepdive i "term"` | Deep dive on term in event i | `deepdive 1 "AI"` |

### Transcript Commands

| Command | Description | Example |
|---------|-------------|---------|
| `transcript search TICKER term` | Search for term in transcript | `transcript search SBUX protein` |
| `transcript view TICKER Q Y` | View full transcript | `transcript view SBUX 3 2025` |
| `transcript download TICKER Q Y` | Download transcript | `transcript download SBUX 3 2025` |

## Example Workflow

### Analyzing Earnings Call Markets

1. **Start with markets:**
   ```
   markets 5
   ```
   Output: Shows top 5 active mention markets

2. **Research an earnings event:**
   ```
   research 1
   ```
   How many quarters to look back? `12`
   
   Output: 
   - Historical hit rates for all terms
   - Edge analysis (hit rate vs market price)
   - Top YES/NO betting opportunities

3. **Deep dive on specific term:**
   ```
   deepdive 1 "protein"
   ```
   Output:
   - Detailed count per transcript
   - Context snippets (2500 chars before/after)
   - AI analysis with strategic insights
   - 5 critical questions for trading

4. **Search transcript manually:**
   ```
   transcript SBUX 2025 2
   ```
   Output: All instances with full context

## 📊 Key Features

### 1. Historical Hit Rate Analysis
- Calculates empirical probability based on past mentions
- Compares against market-implied probability
- Identifies edge opportunities

### 2. Expected Value Calculation
- Shows bid/ask prices for YES and NO
- Calculates edge based on hit rate vs price
- Highlights favorable betting opportunities

### 3. Context-Rich Transcripts
- 2500 characters before/after each mention
- Full transcript viewing and search
- Download transcripts for analysis

### 4. AI-Powered Insights
- Strategic analysis of term usage
- Business implications
- Critical questions for traders
- Smart context centering (ensures match is always included)

## Data Sources

### Earnings Calls
- **API Ninjas** for transcripts
- Look back up to 20 quarters
- Real-time transcript fetching

### Events
- Fed press conferences
- Earnings calls
- Political speeches

## 📁 Project Structure

```
mentionCLI/
├── src/
│   ├── cli.py              # Terminal interface
│   ├── earnings_pipeline.py  # Earnings data pipeline
│   ├── kalshi_api.py       # Kalshi API integration
│   ├── ai_analyzer.py      # OpenAI integration
│   └── ...
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── .env                    # API keys (gitignored)
└── README.md              # This file
```

### "API key error"
Check your `.env` file has correct API keys

### "Address already in use" (web interface)
Port 5000 is occupied. Try:
```bash
PORT=5001 python run_web.py
```

## API Keys

### Required
- **Kalshi API**: Get at [kalshi.com](https://kalshi.com)
- **API Ninjas**: Get at [apininjas.com](https://apininjas.com)

### Optional
- **OpenAI**: For AI analysis (get at [openai.com](https://openai.com))

### Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Submit pull request


## 🤝 Support

- Issues: [GitHub Issues](https://github.com/colesprou/mentionCLI/issues)
- Questions: Open a discussion

---
