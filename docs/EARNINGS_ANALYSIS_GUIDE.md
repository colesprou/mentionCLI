# Earnings Call Analysis Guide

## 🎯 Overview

The Kalshi Mention Market Research Tool now includes comprehensive earnings call analysis capabilities using API Ninjas and Kalshi-compliant mention term matching rules.

## 🚀 Features

### 1. **Earnings Call Data Pipeline**
- **API Integration**: Uses API Ninjas Earnings Call Transcript API
- **Historical Data**: Access to earnings calls from 2000 onwards
- **Flexible Time Range**: Analyze 1-5 years of historical data
- **Batch Processing**: Analyze multiple companies simultaneously

### 2. **Kalshi-Compliant Term Matching**
- **Case-Insensitive**: Matches terms regardless of case
- **Plural/Possessive Forms**: "Immigrants" matches "Immigrant"
- **Compound Words**: "pro-Palestine" matches "Palestine"
- **Ordinal Forms**: "January 6th" matches "January 6"
- **Homonyms/Homographs**: "ice water" matches "ICE"
- **Context Matching**: "Elon University" matches "Elon / Musk"

### 3. **Empirical Probability Tracking**
- **Mention Frequency**: Percentage of quarters with mentions
- **Empirical Probability**: Mentions per total words analyzed
- **Quarterly Breakdown**: Detailed analysis by quarter
- **Sample Contexts**: Real examples of term usage

## 🖥️ Web Interface

### **Access the Web Interface**
```bash
# Start the web server
python run_web.py

# Open in browser
http://localhost:5000
```

### **Web Interface Features**
- **Terminal-like Experience**: Similar to CLI but in browser
- **Interactive Forms**: Easy input for ticker symbols and terms
- **Real-time Analysis**: Live results with progress indicators
- **Batch Analysis**: Analyze multiple companies at once
- **Visual Results**: Rich formatting with metrics and charts

## 🔧 Usage Examples

### **1. Single Company Analysis**
```python
from src.earnings_pipeline import EarningsCallPipeline

pipeline = EarningsCallPipeline("your-api-key")
result = await pipeline.analyze_company_mentions(
    ticker="AAPL",
    mention_terms=["AI", "revenue", "growth", "iPhone"],
    quarters_back=8
)
```

### **2. Batch Analysis**
```python
company_terms = {
    'AAPL': ['AI', 'revenue', 'growth'],
    'MSFT': ['cloud', 'Azure', 'AI'],
    'GOOGL': ['AI', 'search', 'advertising']
}

results = await pipeline.analyze_multiple_companies(
    company_terms, 
    quarters_back=8
)
```

### **3. Web Interface Usage**
1. **Open** http://localhost:5000
2. **Click** "Analyze Earnings" button
3. **Enter** ticker symbol (e.g., "AAPL")
4. **Enter** terms separated by commas (e.g., "AI, revenue, growth")
5. **Select** number of quarters to analyze
6. **Click** "Analyze" to run analysis

## 📊 Analysis Results

### **Key Metrics**
- **Total Mentions**: Count of all term occurrences
- **Empirical Probability**: Mentions per total words (e.g., 0.001840 = 0.184%)
- **Mention Frequency**: Percentage of quarters with mentions
- **Quarters with Mentions**: X/Y quarters analyzed

### **Sample Output**
```
📊 Results for AAPL:
   Quarters analyzed: 3
   Total words: 23,915

   AI:
     Total mentions: 44
     Empirical probability: 0.001840
     Mention frequency: 100.00%
     Quarters with mentions: 3/3

   revenue:
     Total mentions: 82
     Empirical probability: 0.003429
     Mention frequency: 100.00%
     Quarters with mentions: 3/3
```

## 🎯 Kalshi Mention Market Rules

### **Included Matches**
- ✅ **Case-insensitive**: "zelenski" matches "Zelenski"
- ✅ **Plural forms**: "Immigrants" matches "Immigrant"
- ✅ **Possessive forms**: "The eggs' shells" matches "Egg"
- ✅ **Compound words**: "pro-Palestine" matches "Palestine"
- ✅ **Ordinal forms**: "January 6th" matches "January 6"
- ✅ **Homonyms**: "ice water" matches "ICE"
- ✅ **Context matching**: "Elon University" matches "Elon / Musk"

### **Excluded Matches**
- ❌ **Grammatical inflections**: "Immigration" does NOT match "Immigrant"
- ❌ **Closed compounds**: "firetruck" does NOT match "fire"
- ❌ **Homophones**: "right answer" does NOT match "write"
- ❌ **Synonyms**: Similar words are NOT included
- ❌ **Other languages**: Non-English words are NOT matched

## 🔧 Configuration

### **API Key Setup**
```bash
# Set in .env file
API_NINJAS_KEY=hvhh4S1RYUndqJNKcCzAvQ==auITJ6Np8Y2YeHrB

# Or in config.yaml
api_ninjas:
  api_key: "your-api-key-here"
```

### **Available Quarters**
- **4 quarters**: 1 year of data
- **8 quarters**: 2 years of data (recommended)
- **12 quarters**: 3 years of data
- **16 quarters**: 4 years of data
- **20 quarters**: 5 years of data

## 🚀 Getting Started

### **1. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **2. Start Web Interface**
```bash
python run_web.py
```

### **3. Open Browser**
Navigate to http://localhost:5000

### **4. Run Analysis**
- Enter company ticker (e.g., "AAPL")
- Enter mention terms (e.g., "AI, revenue, growth")
- Select quarters to analyze
- Click "Analyze"

## 📈 Use Cases

### **1. Mention Market Research**
- Analyze historical mention patterns
- Calculate empirical probabilities
- Identify trending terms in earnings calls

### **2. Investment Research**
- Track company focus areas over time
- Compare mention patterns across companies
- Identify emerging themes and topics

### **3. Market Prediction**
- Use historical data to inform mention market bets
- Track term frequency trends
- Analyze seasonal patterns in mentions

## 🔍 Technical Details

### **Regex Pattern Generation**
The system automatically generates regex patterns based on Kalshi rules:
- Handles plural/possessive forms
- Supports compound word matching
- Includes ordinal number variations
- Maintains word boundary constraints

### **Performance Optimization**
- Async/await for concurrent API calls
- Efficient regex matching with compiled patterns
- Caching of API responses
- Batch processing for multiple companies

### **Error Handling**
- Graceful handling of missing transcripts
- Retry logic for API failures
- Detailed error logging
- Fallback mechanisms for partial data

## 🎯 Next Steps

1. **Run Analysis**: Start with a few companies and terms
2. **Explore Results**: Review empirical probabilities and patterns
3. **Scale Up**: Use batch analysis for multiple companies
4. **Track Trends**: Monitor changes over time
5. **Inform Trading**: Use data to make informed mention market decisions

The earnings call analysis system provides powerful insights into historical mention patterns, helping you make more informed decisions in Kalshi mention markets!

