#!/usr/bin/env python3
"""
Web Interface for Kalshi Mention Market Research Tool
Provides terminal-like experience in a web browser
"""

from flask import Flask, render_template, request, jsonify, session
import asyncio
import json
import os
from typing import Dict, List, Any
import logging

from .config import load_config
from .cli import KalshiResearchCLI
from .earnings_pipeline import EarningsCallPipeline

# Load config for API keys
config = load_config()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='../templates', static_folder='../static')
app.secret_key = 'kalshi-research-tool-secret-key'

# Global variables for state management
current_cli = None
current_grouped_markets = {}
current_analysis_results = {}

def extract_bet_word(market: dict) -> str:
    """Extract the mention term/word from market data."""
    # First priority: custom_strike.Word (the actual mention term)
    custom_strike = market.get('custom_strike', {})
    if custom_strike and 'Word' in custom_strike:
        return custom_strike['Word']

    # Second priority: no_sub_title (also contains the mention term)
    no_sub_title = market.get('no_sub_title', '')
    if no_sub_title:
        return no_sub_title

    # Third priority: subtitle
    subtitle = market.get('subtitle', '')
    if subtitle:
        return subtitle

    # Fourth priority: title
    title = market.get('title', '')
    if title:
        return title

    # Last resort: extract from ticker
    ticker = market.get('ticker', 'N/A')
    return ticker.split('-')[-1] if '-' in ticker else ticker

def get_cli():
    """Get or create CLI instance"""
    global current_cli
    if current_cli is None:
        config = load_config()
        current_cli = KalshiResearchCLI(config)
    return current_cli

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/markets')
def get_markets():
    """Get mention markets"""
    try:
        # Load the high-volume markets data
        import json
        import os
        
        if os.path.exists('high_volume_mention_markets.json'):
            with open('high_volume_mention_markets.json', 'r') as f:
                all_markets = json.load(f)
            
            # Group markets by event and extract bet words
            events = {}
            for market in all_markets:
                event_ticker = market.get('event_ticker', 'Unknown')
                if event_ticker not in events:
                    events[event_ticker] = {
                        'title': market.get('event_title', market.get('title', event_ticker)),
                        'markets': [],
                        'bet_words': set()
                    }
                
                # Extract bet word from the market
                bet_word = extract_bet_word(market)
                events[event_ticker]['markets'].append(market)
                events[event_ticker]['bet_words'].add(bet_word)
            
            # Convert to list format for frontend
            events_list = []
            for event_ticker, event_data in events.items():
                events_list.append({
                    'event_ticker': event_ticker,
                    'title': event_data['title'],
                    'bet_words': list(event_data['bet_words']),
                    'market_count': len(event_data['markets']),
                    'markets': event_data['markets'][:5]  # First 5 markets for display
                })
            
            return jsonify({
                'status': 'success',
                'data': events_list
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'No markets data found. Run the CLI first to fetch markets.'
            }), 404
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/markets/<int:limit>')
def get_markets_limited(limit):
    """Get limited number of markets by volume"""
    try:
        # Load the high-volume markets data
        import json
        import os
        
        if os.path.exists('high_volume_mention_markets.json'):
            with open('high_volume_mention_markets.json', 'r') as f:
                all_markets = json.load(f)
            
            # Group markets by event and calculate total volume
            events = {}
            for market in all_markets:
                event_ticker = market.get('event_ticker', 'Unknown')
                if event_ticker not in events:
                    events[event_ticker] = {
                        'title': market.get('event_title', market.get('title', event_ticker)),
                        'markets': [],
                        'bet_words': set(),
                        'total_volume': 0
                    }
                
                # Extract bet word from the market
                bet_word = extract_bet_word(market)
                events[event_ticker]['markets'].append(market)
                events[event_ticker]['bet_words'].add(bet_word)
                events[event_ticker]['total_volume'] += market.get('volume', 0)
            
            # Sort by total volume and limit
            sorted_events = sorted(events.items(), key=lambda x: x[1]['total_volume'], reverse=True)
            limited_events = sorted_events[:limit]
            
            # Convert to list format for frontend
            events_list = []
            for event_ticker, event_data in limited_events:
                events_list.append({
                    'event_ticker': event_ticker,
                    'title': event_data['title'],
                    'bet_words': list(event_data['bet_words']),
                    'market_count': len(event_data['markets']),
                    'total_volume': event_data['total_volume'],
                    'markets': event_data['markets'][:5]  # First 5 markets for display
                })
            
            return jsonify({
                'status': 'success',
                'data': events_list
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'No markets data found. Run the CLI first to fetch markets.'
            }), 404
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/events/<path:event_ticker>/bet-words')
def get_event_bet_words(event_ticker):
    """Get bet words for a specific event"""
    try:
        import json
        import os
        
        if os.path.exists('high_volume_mention_markets.json'):
            with open('high_volume_mention_markets.json', 'r') as f:
                all_markets = json.load(f)
            
            # Filter markets for this event
            event_markets = [m for m in all_markets if m.get('event_ticker') == event_ticker]
            
            if not event_markets:
                return jsonify({
                    'status': 'error',
                    'message': f'No markets found for event {event_ticker}'
                }), 404
            
            # Extract bet words
            bet_words = set()
            for market in event_markets:
                bet_word = extract_bet_word(market)
                bet_words.add(bet_word)
            
            # Get event title
            event_title = event_markets[0].get('event_title', event_markets[0].get('title', event_ticker))
            
            return jsonify({
                'status': 'success',
                'data': {
                    'event_ticker': event_ticker,
                    'event_title': event_title,
                    'bet_words': list(bet_words),
                    'market_count': len(event_markets)
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'No markets data found. Run the CLI first to fetch markets.'
            }), 404
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/earnings/analyze', methods=['POST'])
def analyze_earnings():
    """Analyze earnings calls for mention terms"""
    try:
        data = request.get_json()
        ticker = data.get('ticker', '').upper()
        terms = data.get('terms', [])
        quarters_back = data.get('quarters_back', 8)
        
        if not ticker or not terms:
            return jsonify({
                'status': 'error',
                'message': 'Ticker and terms are required'
            }), 400
        
        # Get API key from config
        config = load_config()
        api_key = config.api_ninjas_key
        
        # Run analysis asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        pipeline = EarningsCallPipeline(api_key)
        result = loop.run_until_complete(
            pipeline.analyze_company_mentions(ticker, terms, quarters_back)
        )
        
        loop.close()
        
        return jsonify({
            'status': 'success',
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Error in earnings analysis: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/earnings/batch', methods=['POST'])
def analyze_earnings_batch():
    """Analyze multiple companies for earnings mentions"""
    try:
        data = request.get_json()
        company_terms = data.get('company_terms', {})
        quarters_back = data.get('quarters_back', 8)
        
        if not company_terms:
            return jsonify({
                'status': 'error',
                'message': 'Company terms are required'
            }), 400
        
        # Get API key from config
        config = load_config()
        api_key = config.api_ninjas_key
        
        # Run analysis asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        pipeline = EarningsCallPipeline(api_key)
        results = loop.run_until_complete(
            pipeline.analyze_multiple_companies(company_terms, quarters_back)
        )
        
        loop.close()
        
        return jsonify({
            'status': 'success',
            'data': results
        })
        
    except Exception as e:
        logger.error(f"Error in batch earnings analysis: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/mention-rules')
def get_mention_rules():
    """Get Kalshi mention market rules for reference"""
    rules = {
        "case_sensitivity": "Case-insensitive matching",
        "plural_forms": "Plural and possessive forms are included (e.g., 'Immigrants' matches 'Immigrant')",
        "compound_words": "Compound words, even hyphenated, are included (e.g., 'pro-Palestine' matches 'Palestine')",
        "ordinal_forms": "Ordinal forms included if term has number (e.g., 'January 6th' matches 'January 6')",
        "homonyms": "Homonyms and homographs are included (e.g., 'ice water' matches 'ICE')",
        "exclusions": [
            "Grammatical/tense inflections are NOT included (e.g., 'Immigration' does NOT match 'Immigrant')",
            "Closed compound words are NOT included (e.g., 'firetruck' does NOT match 'fire')",
            "Homophones are NOT included (e.g., 'right answer' does NOT match 'write')",
            "Similar words and synonyms are NOT included"
        ],
        "context_matching": "Words uttered in adjacent context are included (e.g., 'Elon University' matches 'Elon / Musk')",
        "language_restriction": "Only English words are matched (e.g., 'This queso is fuego' does NOT match 'fire')"
    }
    
    return jsonify({
        'status': 'success',
        'data': rules
    })

@app.route('/api/transcript/quarters/<ticker>')
async def get_available_quarters(ticker):
    """Get available quarters for a company."""
    try:
        pipeline = EarningsCallPipeline(config.api_ninjas_key)
        quarters = await pipeline.api_client.get_available_quarters(ticker.upper(), 5)
        
        # Check availability for each quarter
        available_quarters = []
        async with pipeline.api_client as client:
            for year, quarter in quarters:
                call = await client.get_earnings_transcript(ticker.upper(), year, quarter)
                available_quarters.append({
                    'year': year,
                    'quarter': quarter,
                    'available': call is not None,
                    'date': call.date if call else None
                })
        
        return jsonify({
            'success': True,
            'ticker': ticker.upper(),
            'quarters': available_quarters
        })
        
    except Exception as e:
        logger.error(f"Error fetching quarters for {ticker}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/transcript/<ticker>/<int:year>/<int:quarter>')
async def get_transcript(ticker, year, quarter):
    """Get a specific earnings transcript."""
    try:
        pipeline = EarningsCallPipeline(config.api_ninjas_key)
        
        async with pipeline.api_client as client:
            call = await client.get_earnings_transcript(ticker.upper(), year, quarter)
        
        if not call:
            return jsonify({
                'success': False,
                'error': f'Transcript not found for {ticker} Q{quarter} {year}'
            }), 404
        
        return jsonify({
            'success': True,
            'transcript': {
                'ticker': call.ticker,
                'company_name': call.company_name,
                'year': call.year,
                'quarter': call.quarter,
                'date': call.date,
                'transcript': call.transcript,
                'length': len(call.transcript),
                'url': call.url
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching transcript {ticker} Q{quarter} {year}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/transcript/search', methods=['POST'])
async def search_transcript():
    """Search for terms in a transcript."""
    try:
        data = request.get_json()
        ticker = data.get('ticker', '').upper()
        year = data.get('year')
        quarter = data.get('quarter')
        search_term = data.get('search_term', '')
        
        if not all([ticker, year, quarter, search_term]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: ticker, year, quarter, search_term'
            }), 400
        
        pipeline = EarningsCallPipeline(config.api_ninjas_key)
        
        async with pipeline.api_client as client:
            call = await client.get_earnings_transcript(ticker, year, quarter)
        
        if not call:
            return jsonify({
                'success': False,
                'error': f'Transcript not found for {ticker} Q{quarter} {year}'
            }), 404
        
        # Search for the term using regex (case-insensitive)
        import re
        from .earnings_pipeline import KalshiMentionMatcher
        
        matcher = KalshiMentionMatcher()
        pattern = matcher.create_regex_pattern(search_term)
        matches = []
        
        for match in re.finditer(pattern, call.transcript, re.IGNORECASE):
            # Find which line this match is in
            line_start = call.transcript.rfind('\n', 0, match.start()) + 1
            line_end = call.transcript.find('\n', match.start())
            if line_end == -1:
                line_end = len(call.transcript)
            
            line_text = call.transcript[line_start:line_end].strip()
            line_num = call.transcript[:match.start()].count('\n') + 1
            
            # Get context around the match (2500 chars before and after the exact match)
            start = max(0, match.start() - 2500)
            end = min(len(call.transcript), match.end() + 2500)
            context = call.transcript[start:end].strip()
            
            # Highlight the match within the context for web display
            highlighted_context = context
            match_text = match.group()
            match_start = context.lower().find(match_text.lower())
            if match_start != -1:
                # Add HTML highlighting
                before_match = context[:match_start]
                after_match = context[match_start + len(match_text):]
                highlighted_context = f"{before_match}<mark>{match_text}</mark>{after_match}"
            
            matches.append({
                'line_number': line_num,
                'line': line_text,
                'context': highlighted_context,
                'match_text': match_text,
                'position': match.start()
            })
        
        return jsonify({
            'success': True,
            'search_term': search_term,
            'total_matches': len(matches),
            'matches': matches[:50],  # Limit to first 50 matches
            'transcript_info': {
                'ticker': call.ticker,
                'company_name': call.company_name,
                'year': call.year,
                'quarter': call.quarter,
                'date': call.date
            }
        })
        
    except Exception as e:
        logger.error(f"Error searching transcript: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/transcript/summary', methods=['POST'])
async def generate_transcript_summary():
    """Generate AI summary of transcript search results."""
    try:
        data = request.get_json()
        ticker = data.get('ticker', '').upper()
        year = data.get('year')
        quarter = data.get('quarter')
        search_term = data.get('search_term', '')
        matches = data.get('matches', [])
        
        if not all([ticker, year, quarter, search_term]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields: ticker, year, quarter, search_term'
            }), 400
        
        pipeline = EarningsCallPipeline(config.api_ninjas_key)
        
        async with pipeline.api_client as client:
            call = await client.get_earnings_transcript(ticker, year, quarter)
        
        if not call:
            return jsonify({
                'success': False,
                'error': f'Transcript not found for {ticker} Q{quarter} {year}'
            }), 404
        
        # Prepare context for AI analysis (dynamic based on number of matches)
        match_contexts = []
        
        # Dynamic context allocation based on number of matches
        if len(matches) == 1:
            # Single match: use 2000 chars (most context)
            max_context = 2000
            num_matches = 1
        elif len(matches) <= 3:
            # Few matches: use 1000 chars each
            max_context = 1000
            num_matches = min(3, len(matches))
        elif len(matches) <= 5:
            # Some matches: use 600 chars each
            max_context = 600
            num_matches = 5
        else:
            # Many matches: use 400 chars each for more matches
            max_context = 400
            num_matches = min(10, len(matches))
        
        for i, match in enumerate(matches[:num_matches], 1):
            # Smart truncation: center the context around the actual match
            context = match.get('context', '')
            match_text = match.get('match_text', search_term)
            
            # Find the match position in the context
            match_pos = context.lower().find(match_text.lower())
            
            if match_pos != -1 and len(context) > max_context:
                # Center the truncation around the match
                chars_per_side = max_context // 2
                start = max(0, match_pos - chars_per_side)
                end = min(len(context), match_pos + len(match_text) + chars_per_side)
                
                truncated_context = context[start:end]
                if start > 0:
                    truncated_context = "..." + truncated_context
                if end < len(context):
                    truncated_context = truncated_context + "..."
            else:
                truncated_context = context
            
            match_contexts.append(f"Match {i}: {truncated_context}")
        
        # Create prompt for AI analysis
        prompt = f"""
Analyze the following mentions of "{search_term}" from {call.company_name}'s Q{call.quarter} {call.year} earnings call transcript.

Company: {call.company_name}
Quarter: Q{call.quarter} {call.year}
Date: {call.date}
Search Term: "{search_term}"
Total Matches Found: {len(matches)}

IMPORTANT: The following context excerpts contain direct mentions of "{search_term}" in the transcript. These are actual quotes from the earnings call. Use these excerpts to analyze the company's discussion.

Context from transcript matches (these excerpts contain "{search_term}"):
{chr(10).join(match_contexts)}

Based on the above context excerpts, please provide a brief summary (2-3 paragraphs) analyzing:
1. How {call.company_name} is discussing "{search_term}" in their strategy
2. Key business implications or announcements related to "{search_term}"
3. What this suggests about the company's direction or priorities

Note: The term "{search_term}" appears in the provided context excerpts above. Analyze the strategic and business implications based on these excerpts. Do NOT state that the term is not present - it is present in the provided context.
"""
        
        # Generate AI summary using the AI analyzer
        from .ai_analyzer import AIAnalyzer
        ai_analyzer = AIAnalyzer()
        summary = await ai_analyzer.generate_summary(prompt)
        
        return jsonify({
            'success': True,
            'summary': summary,
            'search_term': search_term,
            'transcript_info': {
                'ticker': call.ticker,
                'company_name': call.company_name,
                'year': call.year,
                'quarter': call.quarter,
                'date': call.date
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating transcript summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
