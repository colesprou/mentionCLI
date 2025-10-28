"""
Data pipeline framework for different event types and data sources.
"""

import asyncio
import aiohttp
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
from rich.console import Console
from rich.progress import Progress, TaskID

console = Console()

class DataSource(ABC):
    """Abstract base class for data sources."""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def fetch_data(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Fetch data from this source."""
        pass
    
    @abstractmethod
    def extract_keywords(self, content: str) -> List[str]:
        """Extract relevant keywords from content."""
        pass

class NewsSource(DataSource):
    """News data source using various APIs and web scraping."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("news", config)
        self.user_agent = config.get('user_agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
        self.request_delay = config.get('request_delay', 1.0)
    
    async def fetch_data(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Fetch news articles related to the query."""
        articles = []
        
        # Fetch from multiple news sources
        sources = [
            self._fetch_google_news(query),
            self._fetch_reddit_news(query),
            self._fetch_twitter_mentions(query)
        ]
        
        results = await asyncio.gather(*sources, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                articles.extend(result)
            elif isinstance(result, Exception):
                console.print(f"[yellow]Warning: {result}[/yellow]")
        
        return articles
    
    async def _fetch_google_news(self, query: str) -> List[Dict[str, Any]]:
        """Fetch news from Google News (simplified)."""
        # This is a placeholder - in practice, you'd use a proper news API
        # or web scraping with proper rate limiting
        return []
    
    async def _fetch_reddit_news(self, query: str) -> List[Dict[str, Any]]:
        """Fetch relevant Reddit posts."""
        # Placeholder for Reddit API integration
        return []
    
    async def _fetch_twitter_mentions(self, query: str) -> List[Dict[str, Any]]:
        """Fetch Twitter mentions."""
        # Twitter API integration disabled to avoid costs
        # Users can enable this by providing Twitter API keys
        return []
    
    def extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from news content."""
        # Simple keyword extraction - in practice, use NLP libraries
        words = content.lower().split()
        # Filter out common words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        return keywords[:20]  # Return top 20 keywords

class TranscriptSource(DataSource):
    """Source for transcripts and speeches."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("transcripts", config)
    
    async def fetch_data(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Fetch transcripts related to the query."""
        transcripts = []
        
        # Search for transcripts from various sources
        sources = [
            self._fetch_cspan_transcripts(query),
            self._fetch_whitehouse_transcripts(query),
            self._fetch_congressional_transcripts(query)
        ]
        
        results = await asyncio.gather(*sources, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                transcripts.extend(result)
            elif isinstance(result, Exception):
                console.print(f"[yellow]Warning: {result}[/yellow]")
        
        return transcripts
    
    async def _fetch_cspan_transcripts(self, query: str) -> List[Dict[str, Any]]:
        """Fetch C-SPAN transcripts."""
        # Placeholder for C-SPAN API integration
        return []
    
    async def _fetch_whitehouse_transcripts(self, query: str) -> List[Dict[str, Any]]:
        """Fetch White House transcripts."""
        # Placeholder for White House API integration
        return []
    
    async def _fetch_congressional_transcripts(self, query: str) -> List[Dict[str, Any]]:
        """Fetch Congressional transcripts."""
        # Placeholder for Congressional API integration
        return []
    
    def extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from transcript content."""
        # Similar to news source but might focus on different terms
        words = content.lower().split()
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'um', 'uh', 'you know'}
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        return keywords[:20]

class SocialMediaSource(DataSource):
    """Source for social media data."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("social_media", config)
        self.twitter_config = config.get('twitter', {})
    
    async def fetch_data(self, query: str, **kwargs) -> List[Dict[str, Any]]:
        """Fetch social media posts related to the query."""
        posts = []
        
        # Fetch from different social media platforms
        sources = [
            self._fetch_twitter_posts(query),
            self._fetch_reddit_posts(query),
            self._fetch_facebook_posts(query)
        ]
        
        results = await asyncio.gather(*sources, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                posts.extend(result)
            elif isinstance(result, Exception):
                console.print(f"[yellow]Warning: {result}[/yellow]")
        
        return posts
    
    async def _fetch_twitter_posts(self, query: str) -> List[Dict[str, Any]]:
        """Fetch Twitter posts."""
        # Twitter API integration disabled to avoid costs
        # Users can enable this by providing Twitter API keys
        return []
    
    async def _fetch_reddit_posts(self, query: str) -> List[Dict[str, Any]]:
        """Fetch Reddit posts."""
        # Placeholder for Reddit API integration
        return []
    
    async def _fetch_facebook_posts(self, query: str) -> List[Dict[str, Any]]:
        """Fetch Facebook posts."""
        # Placeholder for Facebook API integration
        return []
    
    def extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from social media content."""
        # Similar to other sources but might handle hashtags and mentions differently
        words = content.lower().split()
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'rt', 'via'}
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        return keywords[:15]

class DataPipeline:
    """Main data pipeline coordinator."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sources = {
            'news': NewsSource(config.get('web_scraping', {})),
            'transcripts': TranscriptSource(config.get('web_scraping', {})),
            'social_media': SocialMediaSource(config.get('web_scraping', {}))
        }
    
    async def run_pipeline(self, market: Dict[str, Any], progress: Progress = None) -> Dict[str, Any]:
        """Run the complete data pipeline for a market."""
        market_id = market.get('id')
        title = market.get('title', '')
        description = market.get('description', '')
        
        # Create search query from market title and description
        query = f"{title} {description}".strip()
        
        console.print(f"[blue]Running data pipeline for market: {title}[/blue]")
        
        # Initialize progress tracking
        if progress:
            task = progress.add_task(f"Processing {title[:50]}...", total=len(self.sources))
        
        results = {
            'market_id': market_id,
            'market_title': title,
            'query': query,
            'data': {},
            'keywords': set(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Fetch data from all sources
        for source_name, source in self.sources.items():
            try:
                console.print(f"[yellow]Fetching data from {source_name}...[/yellow]")
                
                async with source:
                    data = await source.fetch_data(query)
                    results['data'][source_name] = data
                    
                    # Extract keywords from all content
                    for item in data:
                        content = item.get('content', '') or item.get('text', '') or item.get('title', '')
                        if content:
                            keywords = source.extract_keywords(content)
                            results['keywords'].update(keywords)
                
                if progress:
                    progress.update(task, advance=1)
                    
            except Exception as e:
                console.print(f"[red]Error fetching from {source_name}: {e}[/red]")
                results['data'][source_name] = []
        
        # Convert keywords set to list
        results['keywords'] = list(results['keywords'])
        
        console.print(f"[green]Pipeline completed for {title}[/green]")
        return results
    
    async def run_batch_pipeline(self, markets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run pipeline for multiple markets."""
        results = []
        
        with Progress() as progress:
            task = progress.add_task("Processing markets...", total=len(markets))
            
            for market in markets:
                result = await self.run_pipeline(market, progress)
                results.append(result)
                progress.update(task, advance=1)
        
        return results
