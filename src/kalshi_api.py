"""
Kalshi API integration for fetching market data.
"""

import requests
import asyncio
import aiohttp
import time
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json
from rich.console import Console

console = Console()

class KalshiAPI:
    """Client for interacting with the Kalshi API."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.elections.kalshi.com/trade-api/v2"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """Make a request to the Kalshi API."""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            console.print(f"[red]API request failed: {e}[/red]")
            return {}
    
    def get_events(self, cursor: str = None) -> Dict[str, Any]:
        """Get all events from Kalshi with pagination support."""
        params = {}
        if cursor:
            params['cursor'] = cursor
        
        response = self._make_request('events', params)
        return response
    
    def get_markets(self, limit: int = 1000, event_ticker: str = None, cursor: str = None, 
                   tickers: str = None, status: str = None) -> Dict[str, Any]:
        """Get markets from Kalshi with pagination support."""
        params = {
            'limit': min(limit, 1000)  # API max is 1000
        }
        
        if event_ticker:
            params['event_ticker'] = event_ticker
        if cursor:
            params['cursor'] = cursor
        if tickers:
            params['tickers'] = tickers
        if status:
            params['status'] = status
        
        response = self._make_request('markets', params)
        return response
    
    def get_market_details(self, ticker: str) -> Dict[str, Any]:
        """Get detailed market data for a specific ticker."""
        response = self._make_request(f'markets/{ticker}')
        return response
    
    def get_mention_markets(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get mention markets efficiently by querying markets directly and filtering by ticker."""
        all_markets = []
        
        try:
            # Direct approach: Get all markets and filter by ticker containing 'mention'
            console.print("[blue]Getting all markets and filtering for mention markets...[/blue]")
            
            # Get all markets with pagination
            all_markets_data = self._get_all_paginated('markets')
            console.print(f"[green]Found {len(all_markets_data)} total markets[/green]")
            
            # Filter for mention markets by ticker
            mention_markets = [
                market for market in all_markets_data 
                if market.get('ticker') and 'mention' in market.get('ticker', '').lower()
            ]
            
            console.print(f"[green]Found {len(mention_markets)} mention markets by ticker filter[/green]")
            
            # Return the filtered markets (they already contain the data we need)
            all_markets = mention_markets
            
        except Exception as e:
            console.print(f"[red]Error getting mention markets: {e}[/red]")
            return []
        
        return all_markets[:limit]
    
    def _get_all_paginated(self, endpoint: str, event_ticker: str = None) -> List[Dict[str, Any]]:
        """Get all data from a paginated endpoint."""
        all_data = []
        cursor = None
        
        while True:
            try:
                if endpoint == 'events':
                    response = self.get_events(cursor=cursor)
                elif endpoint == 'markets':
                    response = self.get_markets(limit=1000, event_ticker=event_ticker, cursor=cursor)
                else:
                    break
                
                data = response.get(endpoint, [])
                all_data.extend(data)
                
                # Check for pagination
                cursor = response.get('cursor')
                if not cursor:
                    break
                    
            except Exception as e:
                console.print(f"[yellow]Error in pagination for {endpoint}: {e}[/yellow]")
                break
        
        return all_data
    
    def _is_mention_market(self, market: Dict[str, Any]) -> bool:
        """Check if a market is a mention market."""
        ticker = market.get('ticker', '').lower()
        title = market.get('title', '').lower()
        description = market.get('description', '').lower()
        
        # First check if ticker contains 'mention'
        if 'mention' in ticker:
            return True
        
        # Then check title and description for mention keywords
        mention_keywords = [
            'mention', 'will mention', 'mentioned', 'discuss', 
            'talk about', 'speak about', 'say', 'reference'
        ]
        
        return any(keyword in title or keyword in description for keyword in mention_keywords)
    
    def _filter_mention_markets(self, markets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter markets to find mention markets."""
        mention_markets = []
        
        for market in markets:
            title = market.get('title', '').lower()
            description = market.get('description', '').lower()
            
            mention_keywords = [
                'mention', 'will mention', 'mentioned', 'discuss', 'discussion',
                'talk about', 'speak about', 'address', 'reference', 'bring up'
            ]
            
            if any(keyword in title or keyword in description for keyword in mention_keywords):
                mention_markets.append(market)
        
        return mention_markets
    
    def get_market_details(self, market_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific market."""
        return self._make_request(f'markets/{market_id}')
    
    def get_market_history(self, market_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get price history for a market."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        params = {
            'market_id': market_id,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
        
        return self._make_request('markets/history', params)
    
    def search_markets(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search for markets by query."""
        try:
            # Get all markets with pagination
            all_markets = self._get_all_paginated('markets')
            
            # Filter markets by query
            markets = self._filter_markets_by_query(all_markets, query)
            
            return markets[:limit]
        except Exception as e:
            console.print(f"[red]Error searching markets: {e}[/red]")
            return []
    
    def _filter_markets_by_query(self, markets: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        """Filter markets by query string."""
        filtered_markets = []
        query_lower = query.lower()
        
        for market in markets:
            title = market.get('title', '').lower()
            description = market.get('description', '').lower()
            
            if query_lower in title or query_lower in description:
                filtered_markets.append(market)
        
        return filtered_markets
    
    async def scrape_mention_markets(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Scrape mention markets directly from Kalshi website as fallback."""
        import aiohttp
        from bs4 import BeautifulSoup
        import re
        
        markets = []
        
        try:
            async with aiohttp.ClientSession() as session:
                # Try multiple URLs to find mention markets
                urls_to_try = [
                    "https://kalshi.com/?category=mentions",
                    "https://kalshi.com/markets?category=mentions",
                    "https://kalshi.com/",
                    "https://kalshi.com/markets"
                ]
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                }
                
                for url in urls_to_try:
                    try:
                        console.print(f"[blue]Trying to scrape: {url}[/blue]")
                        async with session.get(url, headers=headers) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')
                                
                                # Look for various market element patterns
                                market_selectors = [
                                    'div[data-testid*="market"]',
                                    'div[class*="market"]',
                                    'div[class*="Market"]',
                                    'article[class*="market"]',
                                    'div[class*="card"]',
                                    'div[class*="item"]'
                                ]
                                
                                market_elements = []
                                for selector in market_selectors:
                                    elements = soup.select(selector)
                                    if elements:
                                        market_elements.extend(elements)
                                        console.print(f"[green]Found {len(elements)} elements with selector: {selector}[/green]")
                                
                                # If no specific market elements found, look for any divs with text containing "mention"
                                if not market_elements:
                                    all_divs = soup.find_all('div')
                                    for div in all_divs:
                                        text = div.get_text().lower()
                                        if 'mention' in text and len(text) > 10 and len(text) < 200:
                                            market_elements.append(div)
                                
                                console.print(f"[blue]Total market elements found: {len(market_elements)}[/blue]")
                                
                                for i, element in enumerate(market_elements[:limit]):
                                    try:
                                        # Extract market data from various possible structures
                                        market = self._extract_market_data(element)
                                        
                                        if market and market.get('title'):
                                            # Only include markets that contain mention-related keywords
                                            title_lower = market['title'].lower()
                                            if any(keyword in title_lower for keyword in ['mention', 'will mention', 'mentioned', 'discuss', 'talk about', 'speak about']):
                                                markets.append(market)
                                                console.print(f"[green]Found mention market: {market['title'][:50]}...[/green]")
                                        
                                        if len(markets) >= limit:
                                            break
                                            
                                    except Exception as e:
                                        console.print(f"[yellow]Error extracting market {i}: {e}[/yellow]")
                                        continue
                                
                                if markets:
                                    console.print(f"[green]Successfully scraped {len(markets)} mention markets from {url}[/green]")
                                    break
                                    
                    except Exception as e:
                        console.print(f"[yellow]Failed to scrape {url}: {e}[/yellow]")
                        continue
        
        except Exception as e:
            console.print(f"[red]Web scraping failed: {e}[/red]")
        
        return markets[:limit]
    
    def _extract_market_data(self, element) -> Dict[str, Any]:
        """Extract market data from a DOM element."""
        try:
            # Try to find title in various possible locations
            title = ""
            title_selectors = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', '[class*="title"]', '[class*="name"]', '[class*="question"]']
            
            for selector in title_selectors:
                title_elem = element.find(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if title and len(title) > 5:
                        break
            
            # If no title found, try to get text from the element itself
            if not title:
                title = element.get_text(strip=True)
                # Clean up the title
                title = re.sub(r'\s+', ' ', title)
                if len(title) > 100:
                    title = title[:100] + "..."
            
            # Try to find description
            description = ""
            desc_selectors = ['p', '[class*="description"]', '[class*="summary"]']
            for selector in desc_selectors:
                desc_elem = element.find(selector)
                if desc_elem:
                    description = desc_elem.get_text(strip=True)
                    if description and len(description) > 10:
                        break
            
            # Try to find prices
            yes_price = 0
            no_price = 0
            price_selectors = ['[class*="price"]', '[class*="yes"]', '[class*="no"]', 'span', 'div']
            
            for selector in price_selectors:
                price_elements = element.find_all(selector)
                for price_elem in price_elements:
                    text = price_elem.get_text(strip=True)
                    # Look for percentage patterns
                    if re.match(r'^\d+%$', text):
                        try:
                            price = float(text.replace('%', ''))
                            if yes_price == 0:
                                yes_price = price
                            elif no_price == 0:
                                no_price = price
                        except:
                            pass
            
            # Generate a simple ID if none found
            market_id = element.get('id', '') or element.get('data-id', '') or f"scraped_{hash(title)}"
            
            return {
                'id': market_id,
                'title': title,
                'description': description,
                'yes_price': yes_price,
                'no_price': no_price,
                'volume': 0,
                'status': 'open',
                'source': 'scraped'
            }
            
        except Exception as e:
            console.print(f"[yellow]Error extracting market data: {e}[/yellow]")
            return None
    
    def get_trending_markets(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get trending markets based on volume and activity."""
        try:
            # Get all markets with pagination
            markets = self._get_all_paginated('markets')
            
            # Sort by volume and open interest
            trending = sorted(markets, 
                             key=lambda x: (x.get('volume', 0) + x.get('open_interest', 0)), 
                             reverse=True)
            
            return trending[:limit]
        except Exception as e:
            console.print(f"[red]Error getting trending markets: {e}[/red]")
            return []

class MarketAnalyzer:
    """Analyzer for market data and trends."""
    
    def __init__(self, api: KalshiAPI):
        self.api = api
    
    def analyze_market_sentiment(self, market: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment indicators for a market."""
        yes_price = market.get('yes_price', 0)
        no_price = market.get('no_price', 0)
        volume = market.get('volume', 0)
        open_interest = market.get('open_interest', 0)
        
        # Calculate basic sentiment metrics
        total_price = yes_price + no_price
        if total_price > 0:
            yes_percentage = (yes_price / total_price) * 100
            no_percentage = (no_price / total_price) * 100
        else:
            yes_percentage = no_percentage = 0
        
        # Determine sentiment
        if yes_percentage > 60:
            sentiment = "bullish"
        elif no_percentage > 60:
            sentiment = "bearish"
        else:
            sentiment = "neutral"
        
        return {
            'sentiment': sentiment,
            'yes_percentage': yes_percentage,
            'no_percentage': no_percentage,
            'volume_score': min(volume / 1000, 10),  # Normalize to 0-10
            'interest_score': min(open_interest / 100, 10),  # Normalize to 0-10
            'confidence': abs(yes_percentage - no_percentage) / 100
        }
    
    def find_similar_markets(self, market: Dict[str, Any], all_markets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find markets similar to the given market."""
        target_title = market.get('title', '').lower()
        target_description = market.get('description', '').lower()
        
        similar_markets = []
        
        for other_market in all_markets:
            if other_market.get('id') == market.get('id'):
                continue
                
            other_title = other_market.get('title', '').lower()
            other_description = other_market.get('description', '').lower()
            
            # Simple keyword matching for similarity
            title_words = set(target_title.split())
            other_title_words = set(other_title.split())
            
            # Calculate similarity score
            common_words = title_words.intersection(other_title_words)
            similarity_score = len(common_words) / max(len(title_words), 1)
            
            if similarity_score > 0.3:  # 30% word overlap
                other_market['similarity_score'] = similarity_score
                similar_markets.append(other_market)
        
        # Sort by similarity score
        return sorted(similar_markets, key=lambda x: x.get('similarity_score', 0), reverse=True)
