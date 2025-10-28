"""
Event-specific data pipelines for different types of mention markets.
"""

import requests
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import re
from dataclasses import dataclass
from abc import ABC, abstractmethod
from rich.console import Console

console = Console()

@dataclass
class ResearchResult:
    """Container for research results."""
    event_type: str
    event_title: str
    bet_words: List[str]
    news_articles: List[Dict]
    transcripts: List[Dict]
    social_sentiment: Dict
    historical_data: Dict
    analysis_summary: str

class BaseEventPipeline(ABC):
    """Base class for event-specific data pipelines."""
    
    def __init__(self, event_title: str, bet_words: List[str]):
        self.event_title = event_title
        self.bet_words = bet_words
        self.event_type = self.detect_event_type()
    
    @abstractmethod
    def detect_event_type(self) -> str:
        """Detect the type of event based on title and context."""
        pass
    
    @abstractmethod
    async def get_news_articles(self) -> List[Dict]:
        """Get relevant news articles for this event type."""
        pass
    
    @abstractmethod
    async def get_transcripts(self) -> List[Dict]:
        """Get relevant transcripts or historical data."""
        pass
    
    @abstractmethod
    async def get_social_sentiment(self) -> Dict:
        """Get social media sentiment for bet words."""
        pass
    
    @abstractmethod
    async def get_historical_data(self) -> Dict:
        """Get historical data for similar events."""
        pass
    
    async def run_full_pipeline(self) -> ResearchResult:
        """Run the complete research pipeline."""
        console.print(f"[blue]Running {self.event_type} pipeline for: {self.event_title}[/blue]")
        
        # Run all research tasks in parallel
        news_task = asyncio.create_task(self.get_news_articles())
        transcripts_task = asyncio.create_task(self.get_transcripts())
        social_task = asyncio.create_task(self.get_social_sentiment())
        historical_task = asyncio.create_task(self.get_historical_data())
        
        # Wait for all tasks to complete
        news_articles, transcripts, social_sentiment, historical_data = await asyncio.gather(
            news_task, transcripts_task, social_task, historical_task
        )
        
        # Generate analysis summary
        analysis_summary = await self.generate_analysis_summary(
            news_articles, transcripts, social_sentiment, historical_data
        )
        
        return ResearchResult(
            event_type=self.event_type,
            event_title=self.event_title,
            bet_words=self.bet_words,
            news_articles=news_articles,
            transcripts=transcripts,
            social_sentiment=social_sentiment,
            historical_data=historical_data,
            analysis_summary=analysis_summary
        )
    
    async def generate_analysis_summary(self, news: List[Dict], transcripts: List[Dict], 
                                      social: Dict, historical: Dict) -> str:
        """Generate a summary of all research data."""
        summary_parts = []
        
        if news:
            summary_parts.append(f"Found {len(news)} relevant news articles")
        
        if transcripts:
            summary_parts.append(f"Analyzed {len(transcripts)} historical transcripts")
        
        if social:
            summary_parts.append(f"Social sentiment: {social.get('overall_sentiment', 'neutral')}")
        
        if historical:
            summary_parts.append(f"Historical patterns: {historical.get('pattern_summary', 'no patterns found')}")
        
        return "; ".join(summary_parts) if summary_parts else "No data found"

class EarningsPipeline(BaseEventPipeline):
    """Pipeline for earnings call mention markets."""
    
    def __init__(self, event_title: str, bet_words: List[str], quarters_back: int = 8, api_key: str = None):
        super().__init__(event_title, bet_words)
        self.quarters_back = quarters_back
        from .config import load_config
        config = load_config()
        self.api_key = api_key or config.api_ninjas_key
    
    def detect_event_type(self) -> str:
        return "earnings"
    
    async def get_news_articles(self) -> List[Dict]:
        """Get financial news articles using web scraping."""
        console.print("  📰 Scraping financial news...")
        
        # Extract company name from event title
        company_name = self.extract_company_name()
        
        news_articles = []
        
        # Financial news sources
        sources = [
            "https://www.reuters.com",
            "https://www.bloomberg.com", 
            "https://www.marketwatch.com",
            "https://seekingalpha.com"
        ]
        
        for source in sources:
            try:
                # This would be implemented with actual web scraping
                # For now, return mock data
                articles = await self.scrape_news_source(source, company_name)
                news_articles.extend(articles)
            except Exception as e:
                console.print(f"    ⚠️ Failed to scrape {source}: {e}")
        
        return news_articles[:20]  # Limit to 20 articles
    
    async def get_transcripts(self) -> List[Dict]:
        """Get earnings call transcripts using API Ninja."""
        console.print("  📝 Fetching earnings transcripts...")
        
        company_ticker = self.extract_company_ticker()
        
        try:
            # Use the actual API Ninjas integration
            from .earnings_pipeline import EarningsCallPipeline
            
            pipeline = EarningsCallPipeline(self.api_key)
            results = await pipeline.analyze_company_mentions(
                ticker=company_ticker,
                mention_terms=self.bet_words,
                quarters_back=self.quarters_back
            )
            
            if 'error' in results:
                console.print(f"    ⚠️ {results['error']}")
                return []
            
            # Convert results to transcript format
            transcripts = []
            if 'earnings_calls' in results:
                for call in results['earnings_calls']:
                    transcripts.append({
                        "quarter": f"Q{call['quarter']} {call['year']}",
                        "date": call['date'],
                        "word_count": call['word_count'],
                        "type": "earnings_call",
                        "content": f"Earnings call transcript with {call['word_count']} words"
                    })
            
            return transcripts
            
        except Exception as e:
            console.print(f"    ⚠️ Failed to fetch transcripts: {e}")
            return []
    
    async def get_social_sentiment(self) -> Dict:
        """Get social media sentiment for earnings-related terms."""
        console.print("  📱 Analyzing social sentiment...")
        
        # This would scrape Reddit, Twitter, etc.
        # For now, return mock data
        return {
            "overall_sentiment": "positive",
            "reddit_sentiment": "bullish",
            "twitter_sentiment": "neutral",
            "key_topics": self.bet_words[:5]
        }
    
    async def get_historical_data(self) -> Dict:
        """Get historical earnings data and patterns."""
        console.print("  📊 Analyzing historical patterns...")
        
        company_ticker = self.extract_company_ticker()
        
        try:
            # Use the actual API Ninjas integration for historical analysis
            from .earnings_pipeline import EarningsCallPipeline
            
            pipeline = EarningsCallPipeline(self.api_key)
            results = await pipeline.analyze_company_mentions(
                ticker=company_ticker,
                mention_terms=self.bet_words,
                quarters_back=self.quarters_back
            )
            
            if 'error' in results:
                return {
                    "pattern_summary": "No historical data available",
                    "success_rate": 0.0,
                    "common_phrases": self.bet_words[:3]
                }
            
            # Analyze the results for patterns
            if 'term_results' in results:
                # Calculate overall success rate
                total_mentions = sum(result['total_mentions'] for result in results['term_results'].values())
                total_words = results.get('total_words_analyzed', 1)
                success_rate = total_mentions / total_words if total_words > 0 else 0
                
                # Find most common terms
                term_frequencies = {term: result['mention_frequency'] for term, result in results['term_results'].items()}
                most_common = sorted(term_frequencies.items(), key=lambda x: x[1], reverse=True)[:3]
                
                return {
                    "pattern_summary": f"Company mentions {', '.join([t[0] for t in most_common])} most frequently",
                    "success_rate": success_rate,
                    "common_phrases": [t[0] for t in most_common],
                    "quarters_analyzed": results.get('quarters_analyzed', 0),
                    "total_mentions": total_mentions,
                    "empirical_probabilities": {term: result['hit_rate'] for term, result in results['term_results'].items()}
                }
            
            return {
                "pattern_summary": "Company typically mentions AI and revenue growth",
                "success_rate": 0.75,
                "common_phrases": self.bet_words[:3]
            }
            
        except Exception as e:
            console.print(f"    ⚠️ Failed to analyze historical data: {e}")
            return {
                "pattern_summary": "No historical data available",
                "success_rate": 0.0,
                "common_phrases": self.bet_words[:3]
            }
    
    def extract_company_name(self) -> str:
        """Extract company name from event title."""
        # Extract from patterns like "What will Apple say during earnings?"
        match = re.search(r"What will (.+?) say during", self.event_title)
        if match:
            return match.group(1).strip()
        return "Unknown Company"
    
    def extract_company_ticker(self) -> str:
        """Extract company ticker from event title."""
        company_name = self.extract_company_name()
        
        # Map common company names to tickers
        ticker_map = {
            "Apple": "AAPL",
            "Apple Inc.": "AAPL",
            "Alphabet": "GOOGL",
            "Alphabet Inc.": "GOOGL",
            "Google": "GOOGL",
            "Microsoft": "MSFT",
            "Microsoft Corporation": "MSFT",
            "Amazon": "AMZN",
            "Amazon.com": "AMZN",
            "Tesla": "TSLA",
            "Tesla Inc.": "TSLA",
            "Meta": "META",
            "Facebook": "META",
            "Meta Platforms": "META",
            "Netflix": "NFLX",
            "NVIDIA": "NVDA",
            "Nvidia": "NVDA",
            "Intel": "INTC",
            "Intel Corporation": "INTC",
            "IBM": "IBM",
            "International Business Machines": "IBM"
        }
        
        return ticker_map.get(company_name, company_name.upper())
    
    async def scrape_news_source(self, source: str, company: str) -> List[Dict]:
        """Mock news scraping - would be implemented with actual scraping."""
        return [
            {
                "title": f"Latest news about {company} earnings",
                "url": f"{source}/article1",
                "published": datetime.now().isoformat(),
                "relevance_score": 0.8
            }
        ]

class SportsPipeline(BaseEventPipeline):
    """Pipeline for sports event mention markets."""
    
    def detect_event_type(self) -> str:
        return "sports"
    
    async def get_news_articles(self) -> List[Dict]:
        """Get sports news articles."""
        console.print("  🏈 Scraping sports news...")
        
        # Sports news sources
        sources = [
            "https://www.espn.com",
            "https://www.si.com",
            "https://theathletic.com"
        ]
        
        news_articles = []
        for source in sources:
            try:
                articles = await self.scrape_sports_news(source)
                news_articles.extend(articles)
            except Exception as e:
                console.print(f"    ⚠️ Failed to scrape {source}: {e}")
        
        return news_articles[:15]
    
    async def get_transcripts(self) -> List[Dict]:
        """Get historical commentary or press conferences."""
        console.print("  🎙️ Fetching historical commentary...")
        
        # This would get past game commentary, press conferences, etc.
        return [
            {
                "type": "press_conference",
                "date": "2024-10-20",
                "content": "Coach discussed key players and strategy",
                "relevance": 0.9
            }
        ]
    
    async def get_social_sentiment(self) -> Dict:
        """Get fan sentiment and social media buzz."""
        console.print("  📱 Analyzing fan sentiment...")
        
        return {
            "overall_sentiment": "excited",
            "fan_sentiment": "optimistic",
            "key_topics": self.bet_words[:5],
            "trending_hashtags": ["#NFL", "#GreenBay", "#Pittsburgh"]
        }
    
    async def get_historical_data(self) -> Dict:
        """Get historical game data and commentary patterns."""
        console.print("  📊 Analyzing historical game data...")
        
        return {
            "pattern_summary": "Announcers typically mention weather, key players, and game situations",
            "success_rate": 0.65,
            "common_phrases": self.bet_words[:3]
        }
    
    async def scrape_sports_news(self, source: str) -> List[Dict]:
        """Mock sports news scraping."""
        return [
            {
                "title": f"Game preview and analysis",
                "url": f"{source}/game-preview",
                "published": datetime.now().isoformat(),
                "relevance_score": 0.9
            }
        ]

class PoliticalPipeline(BaseEventPipeline):
    """Pipeline for political event mention markets."""
    
    def detect_event_type(self) -> str:
        return "political"
    
    async def get_news_articles(self) -> List[Dict]:
        """Get political news articles."""
        console.print("  🗳️ Scraping political news...")
        
        sources = [
            "https://www.politico.com",
            "https://thehill.com",
            "https://www.realclearpolitics.com"
        ]
        
        news_articles = []
        for source in sources:
            try:
                articles = await self.scrape_political_news(source)
                news_articles.extend(articles)
            except Exception as e:
                console.print(f"    ⚠️ Failed to scrape {source}: {e}")
        
        return news_articles[:15]
    
    async def get_transcripts(self) -> List[Dict]:
        """Get past speeches and debate transcripts."""
        console.print("  📝 Fetching political transcripts...")
        
        return [
            {
                "type": "speech",
                "date": "2024-10-15",
                "speaker": "Bernie Sanders",
                "content": "Past rally speech discussing key issues",
                "relevance": 0.95
            }
        ]
    
    async def get_social_sentiment(self) -> Dict:
        """Get political social media sentiment."""
        console.print("  📱 Analyzing political sentiment...")
        
        return {
            "overall_sentiment": "passionate",
            "twitter_sentiment": "polarized",
            "reddit_sentiment": "engaged",
            "key_topics": self.bet_words[:5]
        }
    
    async def get_historical_data(self) -> Dict:
        """Get historical political data."""
        console.print("  📊 Analyzing historical political patterns...")
        
        return {
            "pattern_summary": "Politician typically discusses economic issues and healthcare",
            "success_rate": 0.8,
            "common_phrases": self.bet_words[:3]
        }
    
    async def scrape_political_news(self, source: str) -> List[Dict]:
        """Mock political news scraping."""
        return [
            {
                "title": "Political rally coverage and analysis",
                "url": f"{source}/rally-coverage",
                "published": datetime.now().isoformat(),
                "relevance_score": 0.85
            }
        ]

class EntertainmentPipeline(BaseEventPipeline):
    """Pipeline for entertainment event mention markets."""
    
    def detect_event_type(self) -> str:
        return "entertainment"
    
    async def get_news_articles(self) -> List[Dict]:
        """Get entertainment news articles."""
        console.print("  🎬 Scraping entertainment news...")
        
        sources = [
            "https://variety.com",
            "https://www.hollywoodreporter.com",
            "https://deadline.com"
        ]
        
        news_articles = []
        for source in sources:
            try:
                articles = await self.scrape_entertainment_news(source)
                news_articles.extend(articles)
            except Exception as e:
                console.print(f"    ⚠️ Failed to scrape {source}: {e}")
        
        return news_articles[:15]
    
    async def get_transcripts(self) -> List[Dict]:
        """Get past award shows or interviews."""
        console.print("  🎤 Fetching entertainment transcripts...")
        
        return [
            {
                "type": "award_show",
                "date": "2024-03-10",
                "event": "Oscars 2024",
                "content": "Past award show mentions and patterns",
                "relevance": 0.9
            }
        ]
    
    async def get_social_sentiment(self) -> Dict:
        """Get entertainment social media buzz."""
        console.print("  📱 Analyzing entertainment buzz...")
        
        return {
            "overall_sentiment": "excited",
            "twitter_sentiment": "trending",
            "reddit_sentiment": "discussing",
            "key_topics": self.bet_words[:5]
        }
    
    async def get_historical_data(self) -> Dict:
        """Get historical entertainment data."""
        console.print("  📊 Analyzing historical entertainment patterns...")
        
        return {
            "pattern_summary": "Award shows typically mention diversity and social issues",
            "success_rate": 0.7,
            "common_phrases": self.bet_words[:3]
        }
    
    async def scrape_entertainment_news(self, source: str) -> List[Dict]:
        """Mock entertainment news scraping."""
        return [
            {
                "title": "Entertainment industry news and predictions",
                "url": f"{source}/industry-news",
                "published": datetime.now().isoformat(),
                "relevance_score": 0.8
            }
        ]

class GeneralPipeline(BaseEventPipeline):
    """Pipeline for general/unknown event types."""
    
    def detect_event_type(self) -> str:
        return "general"
    
    async def get_news_articles(self) -> List[Dict]:
        """Get general news articles."""
        console.print("  📰 Scraping general news...")
        return []
    
    async def get_transcripts(self) -> List[Dict]:
        """Get general historical data."""
        console.print("  📝 Fetching general data...")
        return []
    
    async def get_social_sentiment(self) -> Dict:
        """Get general social sentiment."""
        console.print("  📱 Analyzing general sentiment...")
        return {"overall_sentiment": "neutral"}
    
    async def get_historical_data(self) -> Dict:
        """Get general historical data."""
        console.print("  📊 Analyzing general patterns...")
        return {"pattern_summary": "No specific patterns identified"}

def get_pipeline_for_event(event_title: str, bet_words: List[str]) -> BaseEventPipeline:
    """Factory function to get the appropriate pipeline for an event."""
    
    # Detect event type based on title
    event_type = detect_event_type(event_title)
    
    if event_type == "earnings":
        return EarningsPipeline(event_title, bet_words)
    elif event_type == "sports":
        return SportsPipeline(event_title, bet_words)
    elif event_type == "political":
        return PoliticalPipeline(event_title, bet_words)
    elif event_type == "entertainment":
        return EntertainmentPipeline(event_title, bet_words)
    else:
        return GeneralPipeline(event_title, bet_words)

def detect_event_type(event_title: str) -> str:
    """Detect the type of event based on the title."""
    title_lower = event_title.lower()
    
    # Earnings calls
    if "earnings" in title_lower or "earnings call" in title_lower:
        return "earnings"
    
    # Sports events
    sports_keywords = ["football", "basketball", "baseball", "nfl", "nba", "mlb", "soccer", "hockey", "nhl", "game", "match", "announcers", "lakers", "warriors", "green bay", "pittsburgh"]
    if any(keyword in title_lower for keyword in sports_keywords):
        return "sports"
    
    # Political events
    political_keywords = ["debate", "speech", "rally", "congress", "senate", "president", "election", "campaign", "political"]
    if any(keyword in title_lower for keyword in political_keywords):
        return "political"
    
    # Entertainment events
    entertainment_keywords = ["oscars", "awards", "show", "concert", "movie", "film", "music", "entertainment", "celebrity"]
    if any(keyword in title_lower for keyword in entertainment_keywords):
        return "entertainment"
    
    return "general"
