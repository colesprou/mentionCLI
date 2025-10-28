#!/usr/bin/env python3
"""
Efficiently fetch ALL mention markets from Kalshi API.

A mention market is any market about whether a specific word/phrase will be said
in a speech, broadcast, interview, debate, press conference, game commentary, 
earnings call, etc.
"""

import json
import re
import time
from typing import Dict, List, Optional

import requests


# Mention market detection phrases (case-insensitive)
MENTION_PHRASES = [
    "said",
    "say", 
    "mention",
    "mentioned",
    "be said",
    "be mentioned", 
    "be heard",
    "said during",
    "said in",
    "mentioned in",
    "announcer say",
    "commentator say",
    "broadcast say",
    "earnings call mention",
    "press conference mention",
    "debate say",
    "will [X] be said"
]

# API configuration
BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"
MARKETS_ENDPOINT = f"{BASE_URL}/markets"
MAX_LIMIT = 1000
MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # seconds


def normalize_text(text: str) -> str:
    """Normalize text for phrase matching."""
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace punctuation with spaces
    text = re.sub(r'[^a-z0-9 ]', ' ', text)
    
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def is_mention_market(mkt: Dict) -> bool:
    """
    Check if a market is a mention market based on title/subtitle content.
    
    Args:
        mkt: Market dictionary from Kalshi API
        
    Returns:
        True if market matches mention criteria
    """
    title = mkt.get("title", "")
    subtitle = mkt.get("subtitle", "")
    
    # Normalize both title and subtitle
    normalized_title = normalize_text(title)
    normalized_subtitle = normalize_text(subtitle)
    
    # Check each phrase against both title and subtitle
    for phrase in MENTION_PHRASES:
        normalized_phrase = normalize_text(phrase)
        
        # Check if phrase appears in title or subtitle
        if (normalized_phrase in normalized_title or 
            normalized_phrase in normalized_subtitle):
            return True
    
    return False


def extract_minimal_fields(mkt: Dict) -> Dict:
    """
    Extract only the essential fields from a market.
    
    Args:
        mkt: Market dictionary from Kalshi API
        
    Returns:
        Dictionary with minimal market data
    """
    return {
        "ticker": mkt["ticker"],
        "event_ticker": mkt.get("event_ticker"),
        "title": mkt.get("title"),
        "subtitle": mkt.get("subtitle"),
        "status": mkt.get("status"),
        "close_time": mkt.get("close_time"),
        "expiration_time": mkt.get("expiration_time"),
        "category": mkt.get("category"),
        "yes_bid": mkt.get("yes_bid"),
        "yes_ask": mkt.get("yes_ask"),
        "no_bid": mkt.get("no_bid"),
        "no_ask": mkt.get("no_ask"),
        "volume": mkt.get("volume"),
        "volume_24h": mkt.get("volume_24h"),
    }


def fetch_all_markets() -> List[Dict]:
    """
    Fetch all open markets from Kalshi API with pagination.
    
    Returns:
        List of all open market dictionaries
        
    Raises:
        requests.RequestException: If API requests fail after retries
    """
    all_markets = []
    cursor = ""
    session = requests.Session()
    
    print("Fetching open markets from Kalshi API...")
    
    while True:
        # Prepare request parameters - only fetch open markets
        params = {"limit": MAX_LIMIT, "status": "open"}
        if cursor:
            params["cursor"] = cursor
            
        # Retry logic for this page
        for attempt in range(MAX_RETRIES):
            try:
                print(f"Fetching page with cursor: {cursor[:20] if cursor else 'first page'}...")
                
                response = session.get(MARKETS_ENDPOINT, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                markets = data.get("markets", [])
                next_cursor = data.get("cursor", "")
                
                print(f"  Found {len(markets)} markets on this page")
                all_markets.extend(markets)
                
                # Check if we should continue pagination
                if not next_cursor or not markets:
                    print("Reached end of pagination")
                    break
                    
                cursor = next_cursor
                break  # Success, exit retry loop
                
            except requests.RequestException as e:
                if attempt < MAX_RETRIES - 1:
                    delay = RETRY_DELAYS[attempt]
                    print(f"  Request failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                    print(f"  Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    print(f"  All retry attempts failed: {e}")
                    raise
        else:
            # If we break out of the retry loop, we're done with pagination
            break
    
    print(f"Total markets fetched: {len(all_markets)}")
    return all_markets


def get_all_mention_markets() -> List[Dict]:
    """
    Get all mention markets from Kalshi.
    
    Returns:
        List of mention market dictionaries with minimal fields
    """
    print("Starting mention market detection...")
    
    # Fetch all markets
    all_markets = fetch_all_markets()
    
    # Filter for mention markets
    print("Filtering for mention markets...")
    mention_markets = []
    seen_tickers = set()
    
    for market in all_markets:
        if is_mention_market(market):
            ticker = market.get("ticker")
            if ticker and ticker not in seen_tickers:
                mention_markets.append(extract_minimal_fields(market))
                seen_tickers.add(ticker)
    
    # Sort by expiration time (nulls last)
    mention_markets.sort(
        key=lambda x: x.get("expiration_time") or "9999-12-31T23:59:59Z"
    )
    
    print(f"Found {len(mention_markets)} unique mention markets")
    return mention_markets


def main():
    """Main function to fetch and display mention markets."""
    try:
        mention_markets = get_all_mention_markets()
        
        print(f"\n=== RESULTS ===")
        print(f"Total markets scanned: {len(fetch_all_markets())}")
        print(f"Total mention markets found: {len(mention_markets)}")
        print(f"\n=== MENTION MARKETS (JSON) ===")
        
        # Output each market as a separate JSON line
        for market in mention_markets:
            print(json.dumps(market, sort_keys=True))
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
