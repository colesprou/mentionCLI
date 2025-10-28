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
        
        # Filter for mention markets (markets with "said", "mention", etc.)
        mention_keywords = ["said", "say", "mention", "mentioned", "be said", "be mentioned"]
        
        mention_markets = []
        for market in all_markets:
            title = (market.get("title", "") + " " + market.get("subtitle", "")).lower()
            
            # Check if it's a mention market
            is_mention = any(keyword in title for keyword in mention_keywords)
            
            # Also check category or event_ticker for earnings/events
            category = market.get("category", "")
            if "earnings" in category.lower() or "conference" in category.lower():
                is_mention = True
            
            if is_mention:
                mention_markets.append(market)
        
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
                    title = (market.get("title", "") + " " + market.get("subtitle", "")).lower()
                    if any(kw in title for kw in ["said", "say", "mention"]):
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


def generate_high_volume_cache(api_key: str, min_volume: int = 50000):
    """
    Generate a high-volume mention markets cache file.
    
    Args:
        api_key: Kalshi API key
        min_volume: Minimum volume threshold for inclusion
    """
    print("Fetching mention markets...")
    all_markets = get_active_mention_markets(api_key)
    search_markets = get_mention_markets_by_direct_search(api_key)
    
    # Combine and deduplicate
    all_markets.extend(search_markets)
    unique_markets = {}
    for market in all_markets:
        ticker = market.get('ticker')
        if ticker and ticker not in unique_markets:
            unique_markets[ticker] = market
    
    all_markets = list(unique_markets.values())
    
    # Filter by volume
    high_volume = [m for m in all_markets if m.get('volume', 0) >= min_volume]
    
    # Sort by volume descending
    high_volume.sort(key=lambda x: x.get('volume', 0), reverse=True)
    
    print(f"Found {len(high_volume)} high-volume mention markets (min volume: {min_volume:,})")
    
    # Save to cache
    with open('high_volume_mention_markets.json', 'w') as f:
        json.dump(high_volume, f, indent=2)
    
    print(f"Saved to high_volume_mention_markets.json")
    return high_volume


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

