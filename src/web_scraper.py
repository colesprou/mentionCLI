"""
Web scraping utilities for news, transcripts, and other data sources.
"""

import asyncio
import aiohttp
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time
from rich.console import Console
from newspaper import Article
import feedparser

console = Console()

class WebScraper:
    """Base web scraper with common functionality."""
    
    def __init__(self, user_agent: str = None, delay: float = 1.0):
        self.user_agent = user_agent or 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        self.delay = delay
        self.session = None
    
    async def __aenter__(self):
        headers = {'User-Agent': self.user_agent}
        self.session = aiohttp.ClientSession(headers=headers)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch a web page and return its content."""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    console.print(f"[yellow]Failed to fetch {url}: {response.status}[/yellow]")
                    return None
        except Exception as e:
            console.print(f"[red]Error fetching {url}: {e}[/red]")
            return None
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:\-()]', '', text)
        return text.strip()

class NewsScraper(WebScraper):
    """Scraper for news articles."""
    
    def __init__(self, user_agent: str = None, delay: float = 1.0):
        super().__init__(user_agent, delay)
        self.news_sources = {
            'reuters': 'https://www.reuters.com',
            'ap': 'https://apnews.com',
            'bbc': 'https://www.bbc.com',
            'cnn': 'https://www.cnn.com',
            'nytimes': 'https://www.nytimes.com',
            'washingtonpost': 'https://www.washingtonpost.com'
        }
    
    async def search_news(self, query: str, max_articles: int = 20) -> List[Dict[str, Any]]:
        """Search for news articles related to the query."""
        articles = []
        
        # Use Google News RSS feeds for initial search
        from urllib.parse import quote_plus
        encoded_query = quote_plus(query)
        google_news_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        try:
            feed = feedparser.parse(google_news_url)
            
            for entry in feed.entries[:max_articles]:
                article = {
                    'title': entry.get('title', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'summary': entry.get('summary', ''),
                    'source': 'google_news',
                    'content': '',
                    'keywords': []
                }
                
                # Try to get full article content
                if article['link']:
                    content = await self._extract_article_content(article['link'])
                    if content:
                        article['content'] = content
                        article['keywords'] = self._extract_keywords(content)
                
                articles.append(article)
                
                # Rate limiting
                await asyncio.sleep(self.delay)
        
        except Exception as e:
            console.print(f"[red]Error searching news: {e}[/red]")
        
        return articles
    
    async def _extract_article_content(self, url: str) -> Optional[str]:
        """Extract full article content from URL."""
        try:
            # Use newspaper3k for article extraction
            article = Article(url)
            article.download()
            article.parse()
            return self.clean_text(article.text)
        except Exception as e:
            console.print(f"[yellow]Could not extract content from {url}: {e}[/yellow]")
            return None
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text."""
        # Simple keyword extraction
        words = re.findall(r'\b\w{4,}\b', text.lower())
        
        # Remove common stop words
        stop_words = {
            'that', 'this', 'with', 'have', 'will', 'from', 'they', 'been', 'were',
            'said', 'each', 'which', 'their', 'time', 'would', 'there', 'could',
            'other', 'after', 'first', 'well', 'also', 'where', 'much', 'some',
            'very', 'when', 'here', 'just', 'into', 'over', 'think', 'back',
            'years', 'work', 'life', 'only', 'know', 'take', 'year', 'hand',
            'long', 'make', 'like', 'him', 'two', 'more', 'goes', 'right',
            'came', 'want', 'show', 'every', 'good', 'meant', 'those', 'small'
        }
        
        keywords = [word for word in words if word not in stop_words]
        
        # Count frequency and return most common
        from collections import Counter
        word_counts = Counter(keywords)
        return [word for word, count in word_counts.most_common(20)]

class TranscriptScraper(WebScraper):
    """Scraper for transcripts and speeches."""
    
    def __init__(self, user_agent: str = None, delay: float = 1.0):
        super().__init__(user_agent, delay)
        self.transcript_sources = {
            'cspan': 'https://www.c-span.org',
            'whitehouse': 'https://www.whitehouse.gov',
            'congress': 'https://www.congress.gov'
        }
    
    async def search_transcripts(self, query: str, max_results: int = 15) -> List[Dict[str, Any]]:
        """Search for transcripts related to the query."""
        transcripts = []
        
        # Search C-SPAN for transcripts
        cspan_results = await self._search_cspan(query, max_results // 2)
        transcripts.extend(cspan_results)
        
        # Search White House transcripts
        wh_results = await self._search_whitehouse(query, max_results // 2)
        transcripts.extend(wh_results)
        
        return transcripts[:max_results]
    
    async def _search_cspan(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search C-SPAN for transcripts."""
        transcripts = []
        
        try:
            # C-SPAN search URL (this is a simplified example)
            from urllib.parse import quote_plus
            encoded_query = quote_plus(query)
            search_url = f"https://www.c-span.org/search/?searchtype=All&query={encoded_query}"
            
            content = await self.fetch_page(search_url)
            if not content:
                return transcripts
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for transcript links (this would need to be adapted based on actual C-SPAN structure)
            links = soup.find_all('a', href=True)
            
            for link in links[:max_results]:
                href = link.get('href')
                if href and ('transcript' in href.lower() or 'video' in href.lower()):
                    transcript = {
                        'title': link.get_text(strip=True),
                        'url': urljoin('https://www.c-span.org', href),
                        'source': 'cspan',
                        'content': '',
                        'date': '',
                        'speaker': ''
                    }
                    
                    # Try to get transcript content
                    transcript_content = await self._extract_transcript_content(transcript['url'])
                    if transcript_content:
                        transcript['content'] = transcript_content
                    
                    transcripts.append(transcript)
                    
                    await asyncio.sleep(self.delay)
        
        except Exception as e:
            console.print(f"[red]Error searching C-SPAN: {e}[/red]")
        
        return transcripts
    
    async def _search_whitehouse(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search White House for transcripts."""
        transcripts = []
        
        try:
            # White House search URL
            from urllib.parse import quote_plus
            encoded_query = quote_plus(query)
            search_url = f"https://www.whitehouse.gov/search/?query={encoded_query}"
            
            content = await self.fetch_page(search_url)
            if not content:
                return transcripts
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for transcript/briefing links
            links = soup.find_all('a', href=True)
            
            for link in links[:max_results]:
                href = link.get('href')
                if href and ('briefing' in href.lower() or 'transcript' in href.lower()):
                    transcript = {
                        'title': link.get_text(strip=True),
                        'url': urljoin('https://www.whitehouse.gov', href),
                        'source': 'whitehouse',
                        'content': '',
                        'date': '',
                        'speaker': 'White House'
                    }
                    
                    # Try to get transcript content
                    transcript_content = await self._extract_transcript_content(transcript['url'])
                    if transcript_content:
                        transcript['content'] = transcript_content
                    
                    transcripts.append(transcript)
                    
                    await asyncio.sleep(self.delay)
        
        except Exception as e:
            console.print(f"[red]Error searching White House: {e}[/red]")
        
        return transcripts
    
    async def _extract_transcript_content(self, url: str) -> Optional[str]:
        """Extract transcript content from URL."""
        try:
            content = await self.fetch_page(url)
            if not content:
                return None
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for common transcript content selectors
            content_selectors = [
                '.transcript-content',
                '.transcript',
                '.content',
                '.entry-content',
                'main',
                'article'
            ]
            
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text()
                    if len(text) > 100:  # Ensure we have substantial content
                        return self.clean_text(text)
            
            # Fallback to body text
            body = soup.find('body')
            if body:
                return self.clean_text(body.get_text())
            
            return None
        
        except Exception as e:
            console.print(f"[yellow]Could not extract transcript from {url}: {e}[/yellow]")
            return None

class SocialMediaScraper(WebScraper):
    """Scraper for social media content."""
    
    def __init__(self, user_agent: str = None, delay: float = 1.0):
        super().__init__(user_agent, delay)
    
    async def search_reddit(self, query: str, subreddit: str = None, max_posts: int = 10) -> List[Dict[str, Any]]:
        """Search Reddit for relevant posts."""
        posts = []
        
        try:
            # Reddit search URL
            from urllib.parse import quote_plus
            encoded_query = quote_plus(query)
            if subreddit:
                search_url = f"https://www.reddit.com/r/{subreddit}/search.json?q={encoded_query}&sort=relevance&limit={max_posts}"
            else:
                search_url = f"https://www.reddit.com/search.json?q={encoded_query}&sort=relevance&limit={max_posts}"
            
            content = await self.fetch_page(search_url)
            if not content:
                return posts
            
            # Parse Reddit JSON response
            import json
            data = json.loads(content)
            
            for post_data in data.get('data', {}).get('children', []):
                post = post_data.get('data', {})
                
                reddit_post = {
                    'title': post.get('title', ''),
                    'content': post.get('selftext', ''),
                    'url': f"https://reddit.com{post.get('permalink', '')}",
                    'score': post.get('score', 0),
                    'comments': post.get('num_comments', 0),
                    'subreddit': post.get('subreddit', ''),
                    'author': post.get('author', ''),
                    'created_utc': post.get('created_utc', 0),
                    'source': 'reddit',
                    'keywords': []
                }
                
                # Extract keywords
                full_text = f"{reddit_post['title']} {reddit_post['content']}"
                reddit_post['keywords'] = self._extract_keywords(full_text)
                
                posts.append(reddit_post)
        
        except Exception as e:
            console.print(f"[red]Error searching Reddit: {e}[/red]")
        
        return posts
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from social media text."""
        # Similar to news scraper but might handle hashtags and mentions differently
        words = re.findall(r'\b\w{3,}\b', text.lower())
        
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
            'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his',
            'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'way', 'who',
            'boy', 'did', 'man', 'oil', 'sit', 'try', 'use', 'she', 'put', 'end',
            'why', 'let', 'ask', 'ran', 'read', 'run', 'set', 'saw', 'say', 'use'
        }
        
        keywords = [word for word in words if word not in stop_words]
        
        from collections import Counter
        word_counts = Counter(keywords)
        return [word for word, count in word_counts.most_common(15)]


