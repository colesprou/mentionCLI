#!/usr/bin/env python3
"""
Helper functions for finding and fetching mention markets.
This provides the interface needed by the CLI.
"""

import json
import requests
from typing import Dict, List, Optional
import time


def get_active_mention_markets(api_key: str) -> List[Dict]:
    """
    Get all active mention markets from Kalshi API.
    
    Args:
        api_key: Kalshi API key
        
    Returns:
        List of active mention market dictionaries
    """
    try:
        headers = {"authorization": f"Bearer {api_key}"}
        session = requests.Session()
        
        all_markets = []
        cursor = ""
        
        while True:
            params = {"limit": 1000, "status": "open"}
            if cursor:
                params["cursor"] = cursor
            
            response = session.get(
                "https://api.elections.kalshi.com/trade-api/v2/markets",
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            markets = data.get("markets", [])
            all_markets.extend(markets)
            
            next_cursor = data.get("cursor", "")
            if not next_cursor or not markets:
                break
            cursor = next_cursor
            
            # Rate limit
            time.sleep(0.2)
        
        # Filter for mention markets - specifically earnings mention markets
        # A mention market has "EARNINGMENTION" in its ticker (earnings mention markets)
        # OR "MENTION" in ticker with custom_strike (bet word markets like Trump says X)
        mention_markets = []
        
        print(f"Filtering {len(all_markets)} markets...")
        
        for market in all_markets:
            ticker = market.get("ticker", "").upper()
            event_ticker = market.get("event_ticker", "").upper()
            custom_strike = market.get("custom_strike")
            
            # Check if it's a mention market
            # Earnings mention markets have "EARNINGSMENTION" in event_ticker or ticker (note: EARNINGSMENTION with S)
            # Other mention markets have "MENTION" in ticker/event_ticker with custom_strike
            is_mention = ("EARNINGSMENTION" in event_ticker) or ("EARNINGSMENTION" in ticker) or \
                        ("MENTION" in ticker and custom_strike) or \
                        ("MENTION" in event_ticker and custom_strike)
            
            if is_mention:
                mention_markets.append(market)
        
        print(f"Found {len(mention_markets)} mention markets after filtering")
        
        return mention_markets
        
    except Exception as e:
        print(f"Error fetching mention markets: {e}")
        return []


def get_mention_markets_by_direct_search(api_key: str) -> List[Dict]:
    """
    Search for mention markets using ticker search.
    
    Args:
        api_key: Kalshi API key
        
    Returns:
        List of mention market dictionaries found via search
    """
    try:
        headers = {"authorization": f"Bearer {api_key}"}
        session = requests.Session()
        
        # Try searching by event tickers for earnings calls
        common_tickers = ["EARNINGS", "CONF", "SPEECH", "CALL"]
        found_markets = []
        
        for ticker in common_tickers:
            try:
                params = {"limit": 1000, "event_ticker": ticker}
                response = session.get(
                    "https://api.elections.kalshi.com/trade-api/v2/markets",
                    headers=headers,
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                markets = data.get("markets", [])
                
                # Filter for mention markets
                for market in markets:
                    ticker = market.get("ticker", "").upper()
                    event_ticker = market.get("event_ticker", "").upper()
                    custom_strike = market.get("custom_strike")
                    
                    # Earnings mention markets have "EARNINGSMENTION" in event_ticker or ticker
                    # Other mention markets have "MENTION" with custom_strike
                    is_mention = ("EARNINGSMENTION" in event_ticker) or ("EARNINGSMENTION" in ticker) or \
                                ("MENTION" in ticker and custom_strike) or \
                                ("MENTION" in event_ticker and custom_strike)
                    if is_mention:
                        found_markets.append(market)
                
                time.sleep(0.2)  # Rate limit
                
            except Exception as e:
                print(f"Error searching for {ticker}: {e}")
                continue
        
        return found_markets
        
    except Exception as e:
        print(f"Error in direct search: {e}")
        return []


def load_cached_mention_markets(filename: str = "high_volume_mention_markets.json") -> List[Dict]:
    """
    Load cached mention markets from JSON file.
    
    Args:
        filename: Path to the JSON cache file
        
    Returns:
        List of market dictionaries from cache
    """
    try:
        with open(filename, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"Error loading cache: {e}")
        return []


def get_earnings_mention_markets_direct(api_key: str) -> List[Dict]:
    """
    Efficiently fetch earnings mention markets by searching for EARNINGSMENTION event_tickers directly.
    This is much faster than fetching all markets.
    
    Args:
        api_key: Kalshi API key
        
    Returns:
        List of earnings mention market dictionaries
    """
    try:
        headers = {"authorization": f"Bearer {api_key}"}
        session = requests.Session()
        
        all_markets = []
        cursor = ""
        
        # Search specifically for EARNINGSMENTION event_tickers
        print("Searching for EARNINGSMENTION markets directly...")
        consecutive_empty_batches = 0
        max_empty_batches = 3  # Stop after 3 consecutive batches with no mention markets
        
        while True:
            params = {"limit": 1000, "status": "open"}
            if cursor:
                params["cursor"] = cursor
            
            response = session.get(
                "https://api.elections.kalshi.com/trade-api/v2/markets",
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            markets = data.get("markets", [])
            
            # Filter for EARNINGSMENTION markets immediately to reduce processing
            mentions_in_batch = 0
            for market in markets:
                event_ticker = market.get("event_ticker", "").upper()
                ticker = market.get("ticker", "").upper()
                custom_strike = market.get("custom_strike")
                
                # Only keep mention markets
                is_mention = ("EARNINGSMENTION" in event_ticker) or ("EARNINGSMENTION" in ticker) or \
                            ("MENTION" in ticker and custom_strike) or \
                            ("MENTION" in event_ticker and custom_strike)
                
                if is_mention and market.get('status') in ['open', 'active']:
                    all_markets.append(market)
                    mentions_in_batch += 1
            
            # Early exit optimization: stop after consecutive batches with no mention markets
            # This assumes mention markets are grouped together
            if mentions_in_batch == 0:
                consecutive_empty_batches += 1
                if consecutive_empty_batches >= max_empty_batches:
                    print(f"Stopping early after {consecutive_empty_batches} consecutive batches with no mention markets")
                    break
            else:
                consecutive_empty_batches = 0  # Reset counter if we found mentions
            
            next_cursor = data.get("cursor", "")
            if not next_cursor or not markets:
                break
            cursor = next_cursor
            
            time.sleep(0.1)  # Reduced rate limit delay
        
        print(f"Found {len(all_markets)} mention markets via direct search")
        return all_markets
        
    except Exception as e:
        print(f"Error in direct earnings mention search: {e}")
        return []


def generate_high_volume_cache(api_key: str, min_volume: int = 0):
    """
    Generate a cache file with all mention markets (not filtered by volume to get all events).
    Uses optimized direct search instead of fetching all markets.
    
    Args:
        api_key: Kalshi API key
        min_volume: Minimum volume threshold for inclusion (default 0 to get all)
    """
    print("Fetching mention markets using optimized search...")
    
    # Use the optimized direct search (much faster)
    all_markets = get_earnings_mention_markets_direct(api_key)
    
    # Also try the direct search method for any additional markets
    search_markets = get_mention_markets_by_direct_search(api_key)
    
    # Combine and deduplicate
    all_markets.extend(search_markets)
    unique_markets = {}
    for market in all_markets:
        ticker = market.get('ticker')
        if ticker and ticker not in unique_markets:
            unique_markets[ticker] = market
    
    all_markets = list(unique_markets.values())
    
    # Filter by status only (only open/active markets) - should already be filtered but double-check
    active_markets = [
        m for m in all_markets 
        if m.get('status') in ['open', 'active']
    ]
    
    # Sort by volume descending to prioritize high-volume markets
    active_markets.sort(key=lambda x: x.get('volume', 0), reverse=True)
    
    print(f"Found {len(active_markets)} active mention markets")
    print(f"Events: {len(set(m.get('event_ticker') for m in active_markets))}")
    
    # Save to cache
    with open('high_volume_mention_markets.json', 'w') as f:
        json.dump(active_markets, f, indent=2)
    
    print(f"Saved to high_volume_mention_markets.json")
    return active_markets


if __name__ == "__main__":
    # Test the functions
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv("KALSHI_API_KEY")
    
    if not api_key:
        print("KALSHI_API_KEY not found in environment")
    else:
        print("Generating high-volume cache...")
        generate_high_volume_cache(api_key)

