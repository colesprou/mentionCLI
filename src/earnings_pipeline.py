#!/usr/bin/env python3
"""
Earnings Call Data Pipeline using API Ninjas
Tracks empirical probability of mention terms using Kalshi rules
"""

import re
import asyncio
import aiohttp
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, Counter
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EarningsCall:
    """Represents an earnings call transcript"""
    ticker: str
    company_name: str
    year: int
    quarter: int
    date: str
    transcript: str
    url: Optional[str] = None

@dataclass
class MentionResult:
    """Result of mention term analysis"""
    term: str
    count: int
    occurrences: List[Dict]  # List of {line_number, context, full_match}
    probability: float
    total_words: int

class KalshiMentionMatcher:
    """Implements Kalshi mention market term matching rules"""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for matching according to Kalshi rules"""
        # Convert to lowercase for case-insensitive matching
        text = text.lower()
        # Remove extra whitespace
        text = ' '.join(text.split())
        return text
    
    @staticmethod
    def create_regex_pattern(term: str) -> str:
        """
        Create regex pattern based on Kalshi mention market rules:
        - Case-insensitive
        - Includes plural and possessive forms
        - Includes compound words (even hyphenated)
        - Includes ordinal forms if term includes number
        - Includes homonyms and homographs
        - Excludes homophones and synonyms
        - Excludes grammatical/tense inflections
        - Excludes closed compound words
        - Handles slash-separated terms (matches ANY of the individual words)
        """
        # Split on slashes and handle each part separately
        if '/' in term:
            # Split on slashes and clean up each part
            parts = [part.strip() for part in term.split('/')]
            # Create patterns for each part and combine with OR
            patterns = []
            for part in parts:
                if part:  # Skip empty parts
                    part_pattern = KalshiMentionMatcher._create_single_term_pattern(part)
                    patterns.append(part_pattern)
            return f"({'|'.join(patterns)})"
        else:
            return KalshiMentionMatcher._create_single_term_pattern(term)
    
    @staticmethod
    def _create_single_term_pattern(term: str) -> str:
        """Create regex pattern for a single term (no slashes)."""
        # Escape special regex characters
        escaped_term = re.escape(term.lower())
        
        # Handle plural and possessive forms
        # Add 's' or 'es' for plurals
        plural_pattern = f"{escaped_term}(?:s|es)?"
        
        # Handle possessive forms
        possessive_pattern = f"{escaped_term}(?:'s|')?"
        
        # Handle compound words (hyphenated or space-separated)
        compound_pattern = f"(?:\\w+[-\\s])?{escaped_term}(?:[-\\s]\\w+)?"
        
        # Handle ordinal forms if term includes number
        ordinal_pattern = escaped_term
        if re.search(r'\d', term):
            ordinal_pattern = f"{escaped_term}(?:st|nd|rd|th)?"
        
        # Combine all patterns
        pattern = f"({plural_pattern}|{possessive_pattern}|{compound_pattern}|{ordinal_pattern})"
        
        # Use word boundaries to avoid partial matches
        pattern = f"\\b{pattern}\\b"
        
        return pattern
    
    @staticmethod
    def find_mentions(transcript: str, term: str) -> List[Dict]:
        """
        Find all mentions of a term in transcript according to Kalshi rules
        Returns list of {line_number, context, full_match}
        """
        normalized_transcript = KalshiMentionMatcher.normalize_text(transcript)
        pattern = KalshiMentionMatcher.create_regex_pattern(term)
        
        mentions = []
        lines = normalized_transcript.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                # Get context (150 chars before and after for better context)
                start = max(0, match.start() - 150)
                end = min(len(line), match.end() + 150)
                context = line[start:end].strip()
                
                mentions.append({
                    'line_number': line_num,
                    'context': context,
                    'full_match': match.group(),
                    'start_pos': match.start(),
                    'end_pos': match.end()
                })
        
        return mentions

class APINinjasClient:
    """Client for API Ninjas Earnings Call Transcript API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.api-ninjas.com/v1"
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_earnings_transcript(self, ticker: str, year: int, quarter: int) -> Optional[EarningsCall]:
        """Get earnings call transcript for a specific company and quarter"""
        # Validate inputs
        if not ticker or ticker is None:
            logger.error(f"Invalid ticker: {ticker}")
            return None
        if year is None or quarter is None:
            logger.error(f"Invalid year/quarter: {year}/{quarter}")
            return None
        
        url = f"{self.base_url}/earningstranscript"
        params = {
            'ticker': ticker.upper(),
            'year': year,
            'quarter': quarter
        }
        headers = {
            'X-Api-Key': self.api_key
        }
        
        try:
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Handle both dict and list responses
                    if isinstance(data, list):
                        if len(data) > 0:
                            data = data[0]  # Take first item if it's a list
                        else:
                            logger.warning(f"No transcript found for {ticker} Q{quarter} {year}")
                            return None
                    
                    # Parse the response data
                    transcript_text = data.get('transcript', '')
                    if not transcript_text:
                        logger.warning(f"No transcript found for {ticker} Q{quarter} {year}")
                        return None
                    
                    return EarningsCall(
                        ticker=ticker.upper(),
                        company_name=data.get('company_name', ticker.upper()),
                        year=year,
                        quarter=quarter,
                        date=data.get('date', ''),
                        transcript=transcript_text,
                        url=data.get('url')
                    )
                else:
                    logger.error(f"API request failed: {response.status} - {await response.text()}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching transcript for {ticker} Q{quarter} {year}: {e}")
            return None
    
    async def get_available_quarters(self, ticker: str, years_back: int = 5) -> List[Tuple[int, int]]:
        """Get available quarters for a ticker (simplified - in real implementation, you'd call the list endpoint)"""
        current_date = datetime.now()
        current_year = current_date.year
        current_month = current_date.month
        
        # Determine current quarter
        if current_month <= 3:
            current_quarter = 1
        elif current_month <= 6:
            current_quarter = 2
        elif current_month <= 9:
            current_quarter = 3
        else:
            current_quarter = 4
        
        quarters = []
        
        # Start from the most recent completed quarter
        year = current_year
        quarter = current_quarter - 1 if current_quarter > 1 else 4
        if current_quarter == 1:
            year = current_year - 1
        
        # Generate quarters going backwards
        for _ in range(years_back * 4):  # 4 quarters per year
            quarters.append((year, quarter))
            
            # Move to previous quarter
            quarter -= 1
            if quarter == 0:
                quarter = 4
                year -= 1
        
        return quarters

class EarningsCallPipeline:
    """Main pipeline for earnings call analysis"""
    
    def __init__(self, api_key: str):
        self.api_client = APINinjasClient(api_key)
        self.matcher = KalshiMentionMatcher()
        self.results = {}
    
    async def analyze_company_mentions(
        self, 
        ticker: str, 
        mention_terms: List[str], 
        quarters_back: int = 8
    ) -> Dict[str, any]:
        """
        Analyze mention terms across multiple earnings calls for a company
        
        Args:
            ticker: Company ticker symbol
            mention_terms: List of terms to search for
            quarters_back: Number of quarters to look back
        
        Returns:
            Dictionary with analysis results
        """
        logger.info(f"Analyzing {ticker} for terms: {mention_terms}")
        
        # Get available quarters
        quarters = await self.api_client.get_available_quarters(ticker, quarters_back // 4 + 1)
        quarters = quarters[:quarters_back]
        
        # Fetch earnings calls
        earnings_calls = []
        async with self.api_client as client:
            for year, quarter in quarters:
                call = await client.get_earnings_transcript(ticker, year, quarter)
                if call:
                    earnings_calls.append(call)
                    logger.info(f"Found transcript for {ticker} Q{quarter} {year}")
                else:
                    logger.warning(f"No transcript for {ticker} Q{quarter} {year}")
        
        if not earnings_calls:
            return {
                'ticker': ticker,
                'error': f'No earnings calls found for {ticker}',
                'quarters_analyzed': 0,
                'terms_analyzed': mention_terms
            }
        
        # Analyze each term across all calls
        term_results = {}
        for term in mention_terms:
            term_results[term] = self._analyze_term_across_calls(term, earnings_calls)
        
        # Calculate overall statistics
        total_calls = len(earnings_calls)
        total_words = sum(len(call.transcript.split()) for call in earnings_calls)
        
        return {
            'ticker': ticker,
            'quarters_analyzed': total_calls,
            'total_words_analyzed': total_words,
            'terms_analyzed': mention_terms,
            'term_results': term_results,
            'earnings_calls': [
                {
                    'year': call.year,
                    'quarter': call.quarter,
                    'date': call.date,
                    'word_count': len(call.transcript.split())
                }
                for call in earnings_calls
            ]
        }
    
    def _analyze_term_across_calls(self, term: str, earnings_calls: List[EarningsCall]) -> Dict:
        """Analyze a single term across multiple earnings calls"""
        all_mentions = []
        mentions_by_quarter = {}
        total_mentions = 0
        
        for call in earnings_calls:
            mentions = self.matcher.find_mentions(call.transcript, term)
            quarter_key = f"Q{call.quarter} {call.year}"
            
            mentions_by_quarter[quarter_key] = {
                'count': len(mentions),
                'mentions': mentions,
                'date': call.date,
                'word_count': len(call.transcript.split()),
                'hit': len(mentions) > 0  # Whether this quarter had at least one mention
            }
            
            all_mentions.extend(mentions)
            total_mentions += len(mentions)
        
        # Calculate empirical probability (word frequency)
        total_words = sum(len(call.transcript.split()) for call in earnings_calls)
        empirical_probability = total_mentions / total_words if total_words > 0 else 0
        
        # Calculate hit rate (probability of appearing at least once per call)
        calls_with_mentions = sum(1 for quarter_data in mentions_by_quarter.values() 
                                if quarter_data['count'] > 0)
        hit_rate = calls_with_mentions / len(earnings_calls) if earnings_calls else 0
        
        # Calculate streak analysis
        hits = [quarter_data['hit'] for quarter_data in mentions_by_quarter.values()]
        current_streak = self._calculate_current_streak(hits)
        longest_streak = self._calculate_longest_streak(hits)
        
        return {
            'term': term,
            'total_mentions': total_mentions,
            'empirical_probability': empirical_probability,  # Word frequency per word
            'hit_rate': hit_rate,  # Probability of appearing at least once per call
            'mention_frequency': hit_rate,  # Alias for backward compatibility
            'quarters_with_mentions': calls_with_mentions,
            'total_quarters_analyzed': len(earnings_calls),
            'mentions_by_quarter': mentions_by_quarter,
            'sample_contexts': [m['context'] for m in all_mentions[:5]],  # First 5 contexts
            'current_streak': current_streak,  # Current streak of hits/misses
            'longest_streak': longest_streak,  # Longest streak of hits
            'hit_pattern': hits  # List of True/False for each quarter
        }
    
    def _calculate_current_streak(self, hits: List[bool]) -> Dict:
        """Calculate current streak of hits or misses"""
        if not hits:
            return {'type': 'none', 'length': 0}
        
        current_value = hits[-1]
        streak_length = 1
        
        # Count backwards from the end
        for i in range(len(hits) - 2, -1, -1):
            if hits[i] == current_value:
                streak_length += 1
            else:
                break
        
        return {
            'type': 'hit' if current_value else 'miss',
            'length': streak_length
        }
    
    def _calculate_longest_streak(self, hits: List[bool]) -> Dict:
        """Calculate longest streak of hits"""
        if not hits:
            return {'type': 'hit', 'length': 0}
        
        max_hit_streak = 0
        max_miss_streak = 0
        current_hit_streak = 0
        current_miss_streak = 0
        
        for hit in hits:
            if hit:
                current_hit_streak += 1
                current_miss_streak = 0
                max_hit_streak = max(max_hit_streak, current_hit_streak)
            else:
                current_miss_streak += 1
                current_hit_streak = 0
                max_miss_streak = max(max_miss_streak, current_miss_streak)
        
        if max_hit_streak >= max_miss_streak:
            return {'type': 'hit', 'length': max_hit_streak}
        else:
            return {'type': 'miss', 'length': max_miss_streak}
    
    async def analyze_multiple_companies(
        self, 
        company_terms: Dict[str, List[str]], 
        quarters_back: int = 8
    ) -> Dict[str, any]:
        """
        Analyze mention terms across multiple companies
        
        Args:
            company_terms: Dict mapping ticker -> list of terms to analyze
            quarters_back: Number of quarters to look back for each company
        
        Returns:
            Dictionary with analysis results for all companies
        """
        results = {}
        
        for ticker, terms in company_terms.items():
            logger.info(f"Analyzing company: {ticker}")
            results[ticker] = await self.analyze_company_mentions(ticker, terms, quarters_back)
        
        return results
    
    def calculate_expected_value(self, hit_rate: float, yes_price: float, no_price: float) -> Dict:
        """
        Calculate expected value for a mention market based on hit rate and prices.
        
        Args:
            hit_rate: Historical probability of the term appearing (0.0 to 1.0)
            yes_price: Current YES price (0.0 to 1.0)
            no_price: Current NO price (0.0 to 1.0)
        
        Returns:
            Dictionary with expected value calculations
        """
        # Expected value for YES bet: (hit_rate * payout_if_yes) - ((1-hit_rate) * cost_if_yes)
        # payout_if_yes = 1 - yes_price, cost_if_yes = yes_price
        yes_expected_value = (hit_rate * (1 - yes_price)) - ((1 - hit_rate) * yes_price)
        
        # Expected value for NO bet: ((1-hit_rate) * payout_if_no) - (hit_rate * cost_if_no)
        # payout_if_no = 1 - no_price, cost_if_no = no_price
        no_expected_value = ((1 - hit_rate) * (1 - no_price)) - (hit_rate * no_price)
        
        # Calculate implied probability from market prices
        yes_implied_prob = yes_price
        no_implied_prob = no_price
        
        # Calculate edge (difference between historical and implied probability)
        yes_edge = hit_rate - yes_implied_prob
        no_edge = (1 - hit_rate) - no_implied_prob
        
        # Determine best bet
        best_bet = "YES" if yes_expected_value > no_expected_value else "NO"
        best_expected_value = max(yes_expected_value, no_expected_value)
        
        return {
            'hit_rate': hit_rate,
            'yes_price': yes_price,
            'no_price': no_price,
            'yes_expected_value': yes_expected_value,
            'no_expected_value': no_expected_value,
            'yes_implied_prob': yes_implied_prob,
            'no_implied_prob': no_implied_prob,
            'yes_edge': yes_edge,
            'no_edge': no_edge,
            'best_bet': best_bet,
            'best_expected_value': best_expected_value,
            'is_positive_ev': best_expected_value > 0
        }

# Example usage and testing
async def main():
    """Example usage of the earnings call pipeline"""
    import os
    api_key = os.getenv('API_NINJAS_KEY')
    
    if not api_key:
        print("Error: API_NINJAS_KEY not set in environment variables")
        return
    
    pipeline = EarningsCallPipeline(api_key)
    
    # Example: Analyze Apple for specific terms
    company_terms = {
        'AAPL': ['AI', 'artificial intelligence', 'iPhone', 'revenue', 'growth'],
        'MSFT': ['cloud', 'Azure', 'AI', 'revenue', 'growth']
    }
    
    results = await pipeline.analyze_multiple_companies(company_terms, quarters_back=8)
    
    # Print results
    for ticker, data in results.items():
        print(f"\n=== {ticker} Analysis ===")
        print(f"Quarters analyzed: {data['quarters_analyzed']}")
        print(f"Total words: {data['total_words_analyzed']:,}")
        
        if 'term_results' in data:
            for term, result in data['term_results'].items():
                print(f"\n{term}:")
                print(f"  Total mentions: {result['total_mentions']}")
                print(f"  Empirical probability: {result['empirical_probability']:.6f}")
                print(f"  Mention frequency: {result['mention_frequency']:.2%}")
                print(f"  Quarters with mentions: {result['quarters_with_mentions']}/{result['total_quarters_analyzed']}")

if __name__ == "__main__":
    asyncio.run(main())
