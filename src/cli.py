"""
Terminal-style CLI interface for the Kalshi research tool.
"""

import click
import asyncio
import re
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.layout import Layout
from rich.live import Live
from rich.align import Align
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from .kalshi_api import KalshiAPI, MarketAnalyzer
from .data_pipeline import DataPipeline
from .ai_analyzer import AIAnalyzer, SentimentAnalyzer
from .web_scraper import NewsScraper, TranscriptScraper, SocialMediaScraper
from .database import get_session, MentionMarket, ResearchData, AIAnalysis, PriceHistory
from .config import load_config
from .event_pipelines import get_pipeline_for_event, detect_event_type

console = Console()

class KalshiResearchCLI:
    """Main CLI class for the Kalshi research tool."""
    
    def __init__(self, config):
        self.config = config
        self.kalshi_api = None
        self.market_analyzer = None
        self.data_pipeline = None
        self.ai_analyzer = None
        self.sentiment_analyzer = SentimentAnalyzer()
        self.current_grouped_markets = {}  # Store current grouped markets
        self.current_research_event = {} # Store markets for the currently researched event
        self.last_research_result = None  # Store last research result for expected value analysis
        self.last_quarters_back = 8  # Store last quarters_back used in research
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all components with configuration."""
        try:
            if self.config.kalshi_api_key:
                self.kalshi_api = KalshiAPI(self.config.kalshi_api_key, self.config.kalshi_api_url)
                self.market_analyzer = MarketAnalyzer(self.kalshi_api)
            
            self.data_pipeline = DataPipeline({
                'web_scraping': self.config.web_scraping,
                'twitter': self.config.twitter
            })
            
            if self.config.openai_api_key:
                self.ai_analyzer = AIAnalyzer(
                    self.config.openai_api_key,
                    self.config.openai_model,
                    self.config.openai_max_tokens,
                    self.config.openai_temperature
                )
        except Exception as e:
            console.print(f"[red]Error initializing components: {e}[/red]")
    
    def display_welcome(self):
        """Display welcome screen."""
        welcome_text = """
        🎯 Kalshi Mention Market Research Tool
        
        A comprehensive terminal-based research platform for analyzing
        Kalshi mention markets with AI-powered insights, data pipelines,
        and real-time market analysis.
        
        Type 'help' for available commands or 'exit' to quit.
        """
        
        console.print(Panel(welcome_text, title="Welcome", border_style="blue"))
    
    def display_help(self):
        """Display help information."""
        help_text = """
        📋 Available Commands:
        
        🔍 RESEARCH COMMANDS:
        • search <query>           - Search for mention markets
        • markets / mentions       - Show all mention markets grouped by topic
        • markets <N> / mentions <N> - Show top N events by volume (e.g., 'markets 10')
        • trending                 - Show trending mention markets
        • similar <market_id>      - Find similar markets
        
        📊 DATA PIPELINE COMMANDS (after running 'markets'):
        • analyze <group_number>   - Run AI analysis on market group
        • research <group_number>  - Run research pipeline on market group
        • summary <group_number>   - Generate AI summary for market group
        • deepdive <group_number> <term> - Deep dive analysis for specific term
        
        📄 TRANSCRIPT COMMANDS:
        • transcript <ticker> <year> <quarter> - Download/view full earnings transcript
        • transcript <ticker> - Show available quarters for company
        
        📊 DATA COMMANDS:
        • pipeline <market_id>     - Run data pipeline for market
        • news <query>             - Search news articles
        • transcripts <query>      - Search transcripts
        • social <query>           - Search social media
        
        🤖 AI COMMANDS:
        • sentiment <market_id>    - Analyze sentiment
        • predict <market_id>      - Generate prediction
        • insights <market_id>     - Extract key insights
        
        📈 MARKET COMMANDS:
        • markets                  - List all mention markets
        • mentions                 - Show all mention markets (same as markets)
        • url                      - Extract market data from Kalshi URL
        • prices <market_id>       - Show price history
        • volume <market_id>       - Show volume data
        
        💰 BETTING COMMANDS:
        • kelly <bankroll> <win_prob%> [market_price] - Calculate optimal bet size using Kelly Criterion
        • bankroll <bankroll> <win_prob%> [market_price] - Same as kelly (alternative command)
        
        🛠️  UTILITY COMMANDS:
        • config                   - Show configuration
        • clear                    - Clear screen
        • help                     - Show this help
        • exit                     - Exit the program
        """
        
        console.print(Panel(help_text, title="Help", border_style="green"))
    
    def display_markets_table(self, markets: List[Dict[str, Any]], title: str = "Mention Markets"):
        """Display markets in a table format."""
        if not markets:
            console.print("[yellow]No markets found.[/yellow]")
            return
        
        table = Table(title=title)
        table.add_column("ID", style="cyan", width=12)
        table.add_column("Title", style="white", width=50)
        table.add_column("Yes Price", style="green", justify="right")
        table.add_column("No Price", style="red", justify="right")
        table.add_column("Volume", style="blue", justify="right")
        table.add_column("Status", style="yellow")
        
        for market in markets[:20]:  # Limit to 20 for readability
            table.add_row(
                market.get('id', 'N/A')[:12],
                market.get('title', 'N/A')[:50],
                f"{market.get('yes_price', 0):.2f}",
                f"{market.get('no_price', 0):.2f}",
                str(market.get('volume', 0)),
                market.get('status', 'N/A')
            )
        
        console.print(table)
    
    def display_analysis_results(self, analysis: Dict[str, Any]):
        """Display AI analysis results."""
        if 'error' in analysis:
            console.print(f"[red]Analysis error: {analysis['error']}[/red]")
            return
        
        # Display summary
        if 'summary' in analysis:
            summary = analysis['summary']
            console.print(Panel(
                summary.get('executive_summary', 'No summary available'),
                title="📋 Executive Summary",
                border_style="blue"
            ))
        
        # Display sentiment
        if 'sentiment' in analysis:
            sentiment = analysis['sentiment']
            sentiment_color = {
                'positive': 'green',
                'negative': 'red',
                'neutral': 'yellow'
            }.get(sentiment.get('overall_sentiment', 'neutral'), 'yellow')
            
            console.print(Panel(
                f"Overall Sentiment: {sentiment.get('overall_sentiment', 'Unknown')}\n"
                f"Confidence: {sentiment.get('confidence', 0)}%",
                title="😊 Sentiment Analysis",
                border_style=sentiment_color
            ))
        
        # Display prediction
        if 'prediction' in analysis:
            prediction = analysis['prediction']
            console.print(Panel(
                f"Predicted Outcome: {prediction.get('predicted_outcome', 'Unknown')}\n"
                f"Confidence: {prediction.get('confidence', 0)}%",
                title="🔮 Prediction",
                border_style="magenta"
            ))
    
    async def search_markets(self, query: str):
        """Search for mention markets."""
        if not self.kalshi_api:
            console.print("[red]Kalshi API not configured.[/red]")
            return
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Searching markets...", total=None)
            
            try:
                markets = self.kalshi_api.search_markets(query)
                progress.update(task, description="Found markets!")
                
                if markets:
                    self.display_markets_table(markets, f"Search Results for: {query}")
                else:
                    console.print(f"[yellow]No markets found for query: {query}[/yellow]")
            
            except Exception as e:
                console.print(f"[red]Error searching markets: {e}[/red]")
    
    async def analyze_market(self, market_id: str):
        """Analyze a specific market."""
        if not self.kalshi_api:
            console.print("[red]Kalshi API not configured.[/red]")
            return
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Analyzing market...", total=None)
            
            try:
                # Get market details
                market = self.kalshi_api.get_market_details(market_id)
                if not market:
                    console.print(f"[red]Market {market_id} not found.[/red]")
                    return
                
                progress.update(task, description="Running data pipeline...")
                
                # Run data pipeline
                research_data = await self.data_pipeline.run_pipeline(market)
                
                progress.update(task, description="Running AI analysis...")
                
                # Run AI analysis
                if self.ai_analyzer:
                    analysis = await self.ai_analyzer.analyze_market_data(market, research_data)
                    self.display_analysis_results(analysis)
                else:
                    console.print("[yellow]AI analyzer not configured. Showing basic analysis.[/yellow]")
                    # Basic sentiment analysis
                    sentiment = self.sentiment_analyzer.analyze_text_sentiment(
                        f"{market.get('title', '')} {market.get('description', '')}"
                    )
                    console.print(f"Basic sentiment: {sentiment['sentiment']} (confidence: {sentiment['confidence']:.2f})")
                
                progress.update(task, description="Analysis complete!")
            
            except Exception as e:
                console.print(f"[red]Error analyzing market: {e}[/red]")
    
    async def show_trending_markets(self):
        """Show trending mention markets."""
        if not self.kalshi_api:
            console.print("[red]Kalshi API not configured.[/red]")
            return
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Fetching trending markets...", total=None)
            
            try:
                markets = self.kalshi_api.get_trending_markets()
                progress.update(task, description="Found trending markets!")
                
                if markets:
                    self.display_markets_table(markets, "🔥 Trending Mention Markets")
                else:
                    console.print("[yellow]No trending markets found.[/yellow]")
            
            except Exception as e:
                console.print(f"[red]Error fetching trending markets: {e}[/red]")
    
    async def show_mention_markets(self, limit=None):
        """Show high-volume mention markets, optionally limited to top N by volume."""
        if not self.kalshi_api:
            console.print("[red]Kalshi API not configured.[/red]")
            return
        
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Loading high-volume mention markets...", total=None)
            
            try:
                # Use smart caching: refresh only if cache is older than 1 hour
                import json
                import os
                import time
                from accurate_mention_finder import get_active_mention_markets, get_mention_markets_by_direct_search, generate_high_volume_cache
                
                cache_file = 'high_volume_mention_markets.json'
                cache_age_threshold = 3600  # 1 hour in seconds
                
                # Check if cache exists and is fresh
                should_refresh = True
                if os.path.exists(cache_file):
                    cache_age = time.time() - os.path.getmtime(cache_file)
                    if cache_age < cache_age_threshold:
                        progress.update(task, description="Loading from cache...")
                        with open(cache_file, 'r') as f:
                            all_markets = json.load(f)
                        
                        # If cache is empty, treat it as stale and refresh
                        if len(all_markets) > 0:
                            should_refresh = False
                            console.print(f"[green]Loaded {len(all_markets)} markets from cache (cache is {int(cache_age/60)} minutes old)[/green]")
                        else:
                            console.print("[yellow]Cache is empty, refreshing...[/yellow]")
                
                # Refresh cache if needed
                if should_refresh:
                    progress.update(task, description="Fetching fresh markets from API...")
                    console.print("[blue]Cache is stale or missing. Refreshing...[/blue]")
                    all_markets = generate_high_volume_cache(self.config.kalshi_api_key, min_volume=1000)
                    console.print(f"[green]Fetched {len(all_markets)} active mention markets[/green]")
                unique_markets = {}
                for market in all_markets:
                    ticker = market.get('ticker')
                    if ticker and ticker not in unique_markets:
                        unique_markets[ticker] = market
                
                all_markets = list(unique_markets.values())
                progress.update(task, description=f"Found {len(all_markets)} active mention markets!")
                
                if all_markets:
                    # Group markets by event and calculate total volume
                    events = {}
                    for market in all_markets:
                        event_ticker = market.get('event_ticker', 'Unknown')
                        if event_ticker not in events:
                            events[event_ticker] = []
                        events[event_ticker].append(market)

                    # Calculate volume for each event and sort by volume
                    event_volumes = []
                    for event_ticker, markets_list in events.items():
                        total_volume = sum(market.get('volume', 0) for market in markets_list)
                        event_volumes.append((event_ticker, markets_list, total_volume))

                    # Sort by volume (descending)
                    event_volumes.sort(key=lambda x: x[2], reverse=True)

                    # Apply limit if specified
                    if limit:
                        event_volumes = event_volumes[:limit]
                        console.print(f"[green]Showing top {limit} events by volume[/green]")

                    # Group the limited events back into the format expected by display_grouped_markets
                    grouped_markets = {}
                    for event_ticker, markets_list, total_volume in event_volumes:
                        # Get event title using the same logic as group_markets_by_event
                        sample_market = markets_list[0]
                        event_title = sample_market.get('event_title')
                        if not event_title:
                            # Try to create a meaningful event title from event_ticker
                            if 'FEDMENTION' in event_ticker:
                                event_title = "Will Powell say [term] at his Oct 2025 press conference?"
                            elif 'EARNINGSMENTION' in event_ticker:
                                # Extract company from ticker (e.g., KXEARNINGSMENTIONGOOGL-25NOV04 -> GOOGL)
                                parts = event_ticker.split('MENTION')
                                if len(parts) > 1:
                                    company_part = parts[1].split('-')[0]
                                    event_title = f"What will {company_part} say during their next earnings call?"
                                else:
                                    event_title = "What will [company] say during their next earnings call?"
                            elif 'TRUMPMENTION' in event_ticker:
                                event_title = "What will Trump say during [event]?"
                            else:
                                # Fall back to using the first market's title as event title
                                event_title = sample_market.get('title', event_ticker)
                        grouped_markets[event_title] = markets_list

                    self.current_grouped_markets = grouped_markets  # Store for later use
                    self.display_grouped_markets(grouped_markets, f"📢 Top {len(grouped_markets)} High-Volume Mention Markets")
                else:
                    console.print("[yellow]No mention markets found. This could be due to API issues or no active mention markets.[/yellow]")
                    console.print("[blue]Try visiting https://kalshi.com/?category=mentions to see available markets.[/blue]")
            
            except Exception as e:
                console.print(f"[red]Error fetching mention markets: {e}[/red]")
    
    def group_markets_by_event(self, markets: List[Dict]) -> Dict[str, List[Dict]]:
        """Group markets by their event for data pipeline analysis."""
        grouped = {}
        for market in markets:
            # Use event_title if available, otherwise create from event_ticker or fall back to title
            event_title = market.get('event_title')
            if not event_title:
                # Try to create a meaningful event title from event_ticker
                event_ticker = market.get('event_ticker', '')
                if event_ticker:
                    # Create event title from event_ticker
                    if 'FEDMENTION' in event_ticker:
                        event_title = "Will Powell say [term] at his Oct 2025 press conference?"
                    elif 'EARNINGSMENTION' in event_ticker:
                        # Extract company from ticker (e.g., KXEARNINGSMENTIONGOOGL-25NOV04 -> GOOGL)
                        parts = event_ticker.split('MENTION')
                        if len(parts) > 1:
                            company_part = parts[1].split('-')[0]
                            event_title = f"What will {company_part} say during their next earnings call?"
                        else:
                            event_title = "What will [company] say during their next earnings call?"
                    elif 'TRUMPMENTION' in event_ticker:
                        event_title = "What will Trump say during [event]?"
                    else:
                        # Fall back to using the first market's title as event title
                        event_title = market.get('title', 'Unknown')
                else:
                    event_title = market.get('title', 'Unknown')
            
            if event_title not in grouped:
                grouped[event_title] = []
            grouped[event_title].append(market)
        return grouped
    
    def extract_bet_word(self, market: Dict) -> str:
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
    
    def display_research_results(self, research_result):
        """Display the results from a research pipeline."""
        from .event_pipelines import ResearchResult
        
        console.print(f"\n[bold green]Research Results for {research_result.event_type.title()} Event[/bold green]")
        console.print("=" * 60)
        
        # News articles
        if research_result.news_articles:
            console.print(f"\n[bold blue]📰 News Articles ({len(research_result.news_articles)} found)[/bold blue]")
            for i, article in enumerate(research_result.news_articles[:3], 1):
                console.print(f"  {i}. {article.get('title', 'No title')}")
                console.print(f"     [dim]URL: {article.get('url', 'No URL')}[/dim]")
            if len(research_result.news_articles) > 3:
                console.print(f"  ... and {len(research_result.news_articles) - 3} more articles")
        
        # Transcripts
        if research_result.transcripts:
            console.print(f"\n[bold blue]📝 Transcripts ({len(research_result.transcripts)} found)[/bold blue]")
            for i, transcript in enumerate(research_result.transcripts[:3], 1):
                console.print(f"  {i}. {transcript.get('quarter', transcript.get('type', 'Unknown'))} - {transcript.get('date', 'No date')}")
                console.print(f"     [dim]{transcript.get('content', 'No content')}[/dim]")
            if len(research_result.transcripts) > 3:
                console.print(f"  ... and {len(research_result.transcripts) - 3} more transcripts")
        
        # Social sentiment
        if research_result.social_sentiment:
            console.print(f"\n[bold blue]📱 Social Sentiment[/bold blue]")
            console.print(f"  Overall: {research_result.social_sentiment.get('overall_sentiment', 'Unknown')}")
            if 'reddit_sentiment' in research_result.social_sentiment:
                console.print(f"  Reddit: {research_result.social_sentiment['reddit_sentiment']}")
            if 'twitter_sentiment' in research_result.social_sentiment:
                console.print(f"  Twitter: {research_result.social_sentiment['twitter_sentiment']}")
        
        # Historical data - Enhanced for earnings
        if research_result.historical_data:
            console.print(f"\n[bold blue]📊 Historical Analysis[/bold blue]")
            console.print(f"  Pattern: {research_result.historical_data.get('pattern_summary', 'No patterns found')}")
            if 'success_rate' in research_result.historical_data:
                console.print(f"  Success Rate: {research_result.historical_data['success_rate']:.1%}")
            
            # Show earnings-specific data
            if research_result.event_type == "earnings":
                if 'quarters_analyzed' in research_result.historical_data:
                    console.print(f"  Quarters Analyzed: {research_result.historical_data['quarters_analyzed']}")
                if 'total_mentions' in research_result.historical_data:
                    console.print(f"  Total Mentions Found: {research_result.historical_data['total_mentions']}")
                if 'empirical_probabilities' in research_result.historical_data:
                    console.print(f"\n[bold yellow]📈 Historical Hit Rates (per earnings call):[/bold yellow]")
                    quarters_count = research_result.historical_data.get('quarters_analyzed', 0)
                    if quarters_count:
                        console.print(f"[dim]  Based on {quarters_count} quarters of data[/dim]")
                    for term, prob in research_result.historical_data['empirical_probabilities'].items():
                        console.print(f"  • {term}: {prob:.1%} hit rate")
                
                # Show expected value analysis if we have market data
                if hasattr(self, 'current_research_event') and self.current_research_event:
                    console.print(f"\n[bold green]💰 Expected Value Analysis:[/bold green]")
                    self._display_expected_value_analysis(research_result)
        
        # Analysis summary
        if research_result.analysis_summary:
            console.print(f"\n[bold blue]🤖 AI Analysis Summary[/bold blue]")
            console.print(f"  {research_result.analysis_summary}")
    
    def display_comprehensive_summary(self, research_result, markets):
        """Display a comprehensive summary combining research and market data."""
        console.print(f"\n[bold green]📊 Comprehensive Summary[/bold green]")
        console.print("=" * 60)
        
        # Event overview
        console.print(f"\n[bold blue]🎯 Event Overview[/bold blue]")
        console.print(f"  Event: {research_result.event_title}")
        console.print(f"  Type: {research_result.event_type.title()}")
        console.print(f"  Bet Words: {', '.join(research_result.bet_words[:5])}")
        if len(research_result.bet_words) > 5:
            console.print(f"  ... and {len(research_result.bet_words) - 5} more")
        
        # Market metrics
        console.print(f"\n[bold blue]💰 Market Metrics[/bold blue]")
        total_volume = sum(market.get('volume', 0) for market in markets)
        avg_yes_bid = sum(market.get('yes_bid', 0) for market in markets if market.get('yes_bid')) / len([m for m in markets if m.get('yes_bid')]) if markets else 0
        console.print(f"  Total Markets: {len(markets)}")
        console.print(f"  Total Volume: ${total_volume:,}")
        console.print(f"  Average Yes Bid: {avg_yes_bid:.2f}")
        
        # Research insights
        if research_result.news_articles:
            console.print(f"\n[bold blue]📰 Key News Insights[/bold blue]")
            console.print(f"  Found {len(research_result.news_articles)} relevant articles")
            if research_result.news_articles:
                console.print(f"  Latest: {research_result.news_articles[0].get('title', 'No title')}")
        
        if research_result.transcripts:
            console.print(f"\n[bold blue]📝 Historical Context[/bold blue]")
            console.print(f"  Analyzed {len(research_result.transcripts)} historical sources")
            if research_result.transcripts:
                console.print(f"  Most Recent: {research_result.transcripts[0].get('date', 'Unknown date')}")
        
        # Sentiment analysis
        if research_result.social_sentiment:
            console.print(f"\n[bold blue]📱 Market Sentiment[/bold blue]")
            sentiment = research_result.social_sentiment.get('overall_sentiment', 'neutral')
            sentiment_color = 'green' if sentiment in ['positive', 'bullish', 'excited'] else 'red' if sentiment in ['negative', 'bearish'] else 'yellow'
            console.print(f"  Overall: [{sentiment_color}]{sentiment}[/{sentiment_color}]")
        
        # Trading recommendations
        console.print(f"\n[bold blue]🎯 Trading Recommendations[/bold blue]")
        console.print("  • Monitor news flow for event-specific developments")
        console.print("  • Watch for volume spikes in individual bet words")
        console.print("  • Consider correlation between related bet words")
        console.print("  • Set stop-losses based on event timeline")
        
        # Risk factors
        console.print(f"\n[bold blue]⚠️ Risk Factors[/bold blue]")
        console.print("  • Event timing uncertainty")
        console.print("  • Market liquidity variations")
        console.print("  • News sentiment shifts")
        console.print("  • Cross-market correlations")
    
    def display_grouped_markets(self, grouped_markets: Dict[str, List[Dict]], title: str):
        """Display markets grouped by event with data pipeline options."""
        console.print(f"\n{title}")
        console.print("=" * 80)
        
        for i, (event_title, markets) in enumerate(grouped_markets.items(), 1):
            # Create a panel for each event group
            panel_content = []
            panel_content.append(f"[bold blue]Event {i}: {event_title}[/bold blue]")
            panel_content.append(f"[dim]Number of bet markets: {len(markets)}[/dim]")
            panel_content.append("")
            
            # Show the different bet words/markets
            panel_content.append("[bold yellow]Available Bets:[/bold yellow]")
            for j, market in enumerate(markets[:5]):  # Show first 5 markets
                ticker = market.get('ticker', 'N/A')
                # Get the full bet word from the market title or subtitle
                bet_word = self.extract_bet_word(market)
                status = market.get('status', 'N/A')
                yes_bid = market.get('yes_bid')
                yes_ask = market.get('yes_ask')
                no_bid = market.get('no_bid')
                no_ask = market.get('no_ask')
                volume = market.get('volume', 0)
                
                # Format bid/ask for both YES and NO
                yes_spread = f"{yes_bid}/{yes_ask}" if yes_bid is not None and yes_ask is not None else "N/A"
                no_spread = f"{no_bid}/{no_ask}" if no_bid is not None and no_ask is not None else "N/A"
                
                panel_content.append(f"  • [bold]{bet_word}[/bold] | YES: {yes_spread} | NO: {no_spread} | Vol: ${volume:,}")
            
            if len(markets) > 5:
                panel_content.append(f"  ... and {len(markets) - 5} more bet options")
            
            # Add data pipeline options
            panel_content.append("")
            panel_content.append("[bold green]Data Pipeline Options:[/bold green]")
            panel_content.append("  • Run AI analysis: [cyan]analyze {i}[/cyan]")
            panel_content.append("  • Get news & transcripts: [cyan]research {i}[/cyan]")
            panel_content.append("  • View price history: [cyan]prices {i}[/cyan]")
            panel_content.append("  • Generate summary: [cyan]summary {i}[/cyan]")
            
            console.print(Panel("\n".join(panel_content), title=f"Event Group {i}", border_style="blue"))
            console.print()
    
    async def analyze_market_group(self, group_index: int, grouped_markets: Dict[str, List[Dict]]):
        """Run AI analysis on a specific event group."""
        event_titles = list(grouped_markets.keys())
        if group_index < 1 or group_index > len(event_titles):
            console.print(f"[red]Invalid group index. Please choose 1-{len(event_titles)}[/red]")
            return
        
        event_title = event_titles[group_index - 1]
        markets = grouped_markets[event_title]
        
        console.print(f"[bold blue]Analyzing event: {event_title}[/bold blue]")
        console.print(f"Found {len(markets)} bet markets for this event")
        
        # Show the bet words
        bet_words = [self.extract_bet_word(market) for market in markets]
        console.print(f"[bold yellow]Bet words: {', '.join(bet_words[:10])}[/bold yellow]")
        if len(bet_words) > 10:
            console.print(f"[dim]... and {len(bet_words) - 10} more[/dim]")
        
        # Detect event type and get appropriate pipeline
        event_type = detect_event_type(event_title)
        console.print(f"[dim]Event type detected: {event_type}[/dim]")
        
        # Run the event-specific pipeline
        try:
            pipeline = get_pipeline_for_event(event_title, bet_words)
            research_result = await pipeline.run_full_pipeline()
            
            # Display the results
            self.display_research_results(research_result)
            
            # Store the research result for expected value analysis
            self.last_research_result = research_result
            
        except Exception as e:
            console.print(f"[red]Error running analysis pipeline: {e}[/red]")
            console.print("\n[yellow]Fallback analysis:[/yellow]")
            console.print("  • Sentiment analysis of bet words")
            console.print("  • Price trend analysis across all bets")
            console.print("  • Volume pattern analysis")
            console.print("  • Risk assessment for each bet")
            console.print("  • Prediction confidence scoring")
            console.print("  • Cross-bet correlation analysis")
    
    async def research_market_group(self, group_index: int, grouped_markets: Dict[str, List[Dict]], quarters_back: int = None):
        """Run research data pipeline on a specific event group."""
        event_titles = list(grouped_markets.keys())
        if group_index < 1 or group_index > len(event_titles):
            console.print(f"[red]Invalid group index. Please choose 1-{len(event_titles)}[/red]")
            return
        
        event_title = event_titles[group_index - 1]
        markets = grouped_markets[event_title]
        
        # Store the current event's markets for expected value analysis
        # Don't overwrite the full grouped markets, just store the current event
        self.current_research_event = {event_title: markets}
        
        console.print(f"[bold blue]Researching event: {event_title}[/bold blue]")
        console.print(f"Found {len(markets)} bet markets for this event")
        
        # Show the bet words
        bet_words = [self.extract_bet_word(market) for market in markets]
        console.print(f"[bold yellow]Researching bets: {', '.join(bet_words[:10])}[/bold yellow]")
        if len(bet_words) > 10:
            console.print(f"[dim]... and {len(bet_words) - 10} more[/dim]")
        
        # Detect event type and get appropriate pipeline
        event_type = detect_event_type(event_title)
        console.print(f"[dim]Event type detected: {event_type}[/dim]")
        
        # Ask for quarters input if it's an earnings event
        if event_type == "earnings":
            if quarters_back is None:
                console.print(f"\n[bold yellow]📊 Earnings Call Analysis[/bold yellow]")
                console.print("How many quarters back would you like to analyze?")
                console.print("  • 4 quarters (1 year)")
                console.print("  • 8 quarters (2 years) - [bold]default[/bold]")
                console.print("  • 12 quarters (3 years)")
                console.print("  • 16 quarters (4 years)")
                console.print("  • 20 quarters (5 years)")
                
                try:
                    quarters_input = Prompt.ask("Enter number of quarters", default="8")
                    quarters_back = int(quarters_input)
                    if quarters_back < 1 or quarters_back > 20:
                        console.print("[yellow]Invalid input, using default of 8 quarters[/yellow]")
                        quarters_back = 8
                except (ValueError, KeyboardInterrupt):
                    console.print("[yellow]Using default of 8 quarters[/yellow]")
                    quarters_back = 8
            else:
                console.print(f"\n[bold yellow]📊 Earnings Call Analysis[/bold yellow]")
                console.print(f"Analyzing {quarters_back} quarters back")
        else:
            # For non-earnings events, use default if not specified
            if quarters_back is None:
                quarters_back = 8
        
        # Run the event-specific research pipeline
        try:
            if event_type == "earnings":
                # Create earnings pipeline with quarters parameter
                from .event_pipelines import EarningsPipeline
                pipeline = EarningsPipeline(event_title, bet_words, quarters_back)
            else:
                pipeline = get_pipeline_for_event(event_title, bet_words)
            
            research_result = await pipeline.run_full_pipeline()
            
            # Store the research result and quarters_back for expected value analysis
            self.last_research_result = research_result
            self.last_quarters_back = quarters_back
            
            # Display the research results
            self.display_research_results(research_result)
            
        except Exception as e:
            console.print(f"[red]Error running research pipeline: {e}[/red]")
            console.print("\n[yellow]Fallback research:[/yellow]")
            console.print("  • News articles related to the event and bet words")
            console.print("  • Past transcripts and speeches mentioning these words")
            console.print("  • Social media sentiment for each bet word")
            console.print("  • Historical price data for similar events")
            console.print("  • Related market analysis and correlations")
    
    async def generate_summary(self, group_index: int, grouped_markets: Dict[str, List[Dict]]):
        """Generate AI summary for a specific event group."""
        event_titles = list(grouped_markets.keys())
        if group_index < 1 or group_index > len(event_titles):
            console.print(f"[red]Invalid group index. Please choose 1-{len(event_titles)}[/red]")
            return
        
        event_title = event_titles[group_index - 1]
        markets = grouped_markets[event_title]
        
        console.print(f"[bold blue]Generating summary for event: {event_title}[/bold blue]")
        console.print(f"Found {len(markets)} bet markets for this event")
        
        # Show the bet words
        bet_words = [self.extract_bet_word(market) for market in markets]
        console.print(f"[bold yellow]Summary for bets: {', '.join(bet_words[:10])}[/bold yellow]")
        if len(bet_words) > 10:
            console.print(f"[dim]... and {len(bet_words) - 10} more[/dim]")
        
        # Detect event type and get appropriate pipeline
        event_type = detect_event_type(event_title)
        console.print(f"[dim]Event type detected: {event_type}[/dim]")
        
        # Run the event-specific pipeline for summary
        try:
            pipeline = get_pipeline_for_event(event_title, bet_words)
            research_result = await pipeline.run_full_pipeline()
            
            # Generate comprehensive summary
            self.display_comprehensive_summary(research_result, markets)
            
        except Exception as e:
            console.print(f"[red]Error running summary pipeline: {e}[/red]")
            console.print("\n[yellow]Fallback summary:[/yellow]")
            console.print("  • Event overview and key metrics")
            console.print("  • Price trend analysis across all bets")
            console.print("  • Volume and liquidity assessment for each bet")
            console.print("  • Risk factors and opportunities")
            console.print("  • Trading recommendations for each bet word")
            console.print("  • Related news and events")
        console.print("  • Cross-bet correlation insights")
    
    def _display_expected_value_analysis(self, research_result):
        """Display expected value analysis for earnings markets."""
        from .earnings_pipeline import EarningsCallPipeline
        
        pipeline = EarningsCallPipeline(self.config.api_ninjas_key)
        
        # Get the current event's markets
        event_title = research_result.event_title
        if hasattr(self, 'current_research_event') and event_title in self.current_research_event:
            markets = self.current_research_event[event_title]
            
            # Get hit rates from historical data
            hit_rates = research_result.historical_data.get('empirical_probabilities', {})
            
            # Separate markets into YES edge and NO edge opportunities
            yes_edge_markets = []
            no_edge_markets = []
            
            for market in markets:
                bet_word = self.extract_bet_word(market)
                hit_rate = hit_rates.get(bet_word, 0.0)
                
                yes_bid = market.get('yes_bid', 0)
                yes_ask = market.get('yes_ask', 0)
                no_bid = market.get('no_bid', 0)
                no_ask = market.get('no_ask', 0)
                
                # Convert from cents to decimal (Kalshi stores prices as integers representing cents)
                yes_bid = yes_bid / 100 if yes_bid else 0
                yes_ask = yes_ask / 100 if yes_ask else 0
                no_bid = no_bid / 100 if no_bid else 0
                no_ask = no_ask / 100 if no_ask else 0
                
                # Use ask prices for edge calculation (what you actually pay to enter position)
                # For YES edge: compare hit_rate vs yes_ask (price to buy YES)
                # For NO edge: compare (1-hit_rate) vs no_ask (price to buy NO)
                yes_price_for_edge = yes_ask
                no_price_for_edge = no_ask
                
                # Use mid-price for expected value calculation (fair value estimate)
                yes_price_for_ev = (yes_bid + yes_ask) / 2 if yes_bid and yes_ask else (yes_bid or yes_ask or 0)
                no_price_for_ev = (no_bid + no_ask) / 2 if no_bid and no_ask else (no_bid or no_ask or 0)
                
                if yes_price_for_ev > 0 and no_price_for_ev > 0:
                    ev_analysis = pipeline.calculate_expected_value(hit_rate, yes_price_for_ev, no_price_for_ev)
                    
                    # Calculate edge using ask prices (what you actually pay)
                    yes_edge = hit_rate - yes_price_for_edge  # Hit rate vs YES ask price
                    no_edge = (1 - hit_rate) - no_price_for_edge  # (1-Hit rate) vs NO ask price
                    
                    # Update the ev_analysis with ask-based edge
                    ev_analysis['yes_edge'] = yes_edge
                    ev_analysis['no_edge'] = no_edge
                    
                    market_data = {
                        'bet_word': bet_word,
                        'hit_rate': hit_rate,
                        'yes_price': yes_price_for_ev,  # Mid-price for EV
                        'no_price': no_price_for_ev,   # Mid-price for EV
                        'yes_bid': yes_bid,
                        'yes_ask': yes_ask,
                        'no_bid': no_bid,
                        'no_ask': no_ask,
                        'ev_analysis': ev_analysis
                    }
                    
                    # Categorize by edge direction
                    if ev_analysis['yes_edge'] > 0:
                        yes_edge_markets.append(market_data)
                    elif ev_analysis['no_edge'] > 0:
                        no_edge_markets.append(market_data)
            
            # Sort by edge size (largest first)
            yes_edge_markets.sort(key=lambda x: x['ev_analysis']['yes_edge'], reverse=True)
            no_edge_markets.sort(key=lambda x: x['ev_analysis']['no_edge'], reverse=True)
            
            # Display YES Edge Opportunities
            if yes_edge_markets:
                console.print(f"\n[bold green]📈 YES Edge Opportunities (Historical Hit Rate > Market Price)[/bold green]")
                console.print("  [dim]Term | Hit Rate | YES Bid/Ask | NO Bid/Ask | Expected Value | Edge[/dim]")
                console.print("  " + "-" * 120)
                
                for market_data in yes_edge_markets:
                    ev_analysis = market_data['ev_analysis']
                    # Get original bid/ask prices
                    market = next(m for m in markets if self.extract_bet_word(m) == market_data['bet_word'])
                    yes_bid = market.get('yes_bid', 0) / 100 if market.get('yes_bid', 0) else 0
                    yes_ask = market.get('yes_ask', 0) / 100 if market.get('yes_ask', 0) else 0
                    no_bid = market.get('no_bid', 0) / 100 if market.get('no_bid', 0) else 0
                    no_ask = market.get('no_ask', 0) / 100 if market.get('no_ask', 0) else 0
                    
                    console.print(f"  {market_data['bet_word'][:25]:<25} | {market_data['hit_rate']:>7.1%} | {yes_bid:>4.3f}/{yes_ask:<4.3f} | {no_bid:>4.3f}/{no_ask:<4.3f} | {ev_analysis['yes_expected_value']:>13.3f} | {ev_analysis['yes_edge']:>6.3f}")
            
            # Display NO Edge Opportunities
            if no_edge_markets:
                console.print(f"\n[bold red]📉 NO Edge Opportunities (Historical Hit Rate < Market Price)[/bold red]")
                console.print("  [dim]Term | Hit Rate | YES Bid/Ask | NO Bid/Ask | Expected Value | Edge[/dim]")
                console.print("  " + "-" * 120)
                
                for market_data in no_edge_markets:
                    ev_analysis = market_data['ev_analysis']
                    # Get original bid/ask prices
                    market = next(m for m in markets if self.extract_bet_word(m) == market_data['bet_word'])
                    yes_bid = market.get('yes_bid', 0) / 100 if market.get('yes_bid', 0) else 0
                    yes_ask = market.get('yes_ask', 0) / 100 if market.get('yes_ask', 0) else 0
                    no_bid = market.get('no_bid', 0) / 100 if market.get('no_bid', 0) else 0
                    no_ask = market.get('no_ask', 0) / 100 if market.get('no_ask', 0) else 0
                    
                    console.print(f"  {market_data['bet_word'][:25]:<25} | {market_data['hit_rate']:>7.1%} | {yes_bid:>4.3f}/{yes_ask:<4.3f} | {no_bid:>4.3f}/{no_ask:<4.3f} | {ev_analysis['no_expected_value']:>13.3f} | {ev_analysis['no_edge']:>6.3f}")
            
            # Summary
            total_opportunities = len(yes_edge_markets) + len(no_edge_markets)
            console.print(f"\n[bold]Summary:[/bold] {total_opportunities} total opportunities found")
            console.print(f"  • {len(yes_edge_markets)} YES edge opportunities")
            console.print(f"  • {len(no_edge_markets)} NO edge opportunities")
            
            console.print(f"\n[dim]Legend:[/dim]")
            console.print(f"[dim]Hit Rate = Historical probability of term appearing in earnings call[/dim]")
            console.print(f"[dim]Expected Value = (Hit Rate × Payout) - ((1-Hit Rate) × Cost)[/dim]")
            console.print(f"[dim]Edge = Historical Hit Rate - Ask Price (what you actually pay)[/dim]")
            console.print(f"[dim]YES Edge: Hit Rate > YES Ask Price (bet YES)[/dim]")
            console.print(f"[dim]NO Edge: (1-Hit Rate) > NO Ask Price (bet NO)[/dim]")
    
    async def deep_dive_analysis(self, group_index: int, term: str, grouped_markets: Dict[str, List[Dict]], quarters_back: int = None):
        """Deep dive analysis for a specific term: earnings mentions, context, and critical AI analysis."""
        event_titles = list(grouped_markets.keys())
        if group_index < 1 or group_index > len(event_titles):
            console.print(f"[red]Invalid group index. Please choose 1-{len(event_titles)}[/red]")
            return
        
        event_title = event_titles[group_index - 1]
        markets = grouped_markets[event_title]
        
        # Use the same quarters_back as the research command, or default to 8
        if quarters_back is None:
            quarters_back = 8
        
        console.print(f"[bold blue]🔍 Deep Dive Analysis: {term}[/bold blue]")
        console.print(f"Event: {event_title}")
        console.print("=" * 80)
        
        # Step 1: Analyze earnings mentions with context and market data
        console.print(f"\n[bold yellow]📊 Step 1: Historical Earnings Analysis[/bold yellow]")
        earnings_data = await self._analyze_earnings_mentions(term, event_title, quarters_back)
        
        # Step 2: Market analysis with edge calculations
        console.print(f"\n[bold yellow]💰 Step 2: Market Analysis & Edge Calculation[/bold yellow]")
        market_data = await self._analyze_market_edge(term, markets)
        
        # Step 3: Critical AI analysis with all data
        console.print(f"\n[bold yellow]🤖 Step 3: Critical Analysis & Decision Framework[/bold yellow]")
        await self._generate_critical_analysis(term, event_title, earnings_data, market_data)
    
    async def _analyze_earnings_mentions(self, term: str, event_title: str, quarters_back: int = 8) -> Dict:
        """Analyze which earnings calls mentioned the term and provide context."""
        from .earnings_pipeline import EarningsCallPipeline
        
        pipeline = EarningsCallPipeline(self.config.api_ninjas_key)
        
        # Extract company ticker
        company_ticker = self._extract_company_ticker_from_event(event_title)
        
        console.print(f"  Analyzing {company_ticker} earnings calls for '{term}'...")
        
        try:
            results = await pipeline.analyze_company_mentions(
                ticker=company_ticker,
                mention_terms=[term],
                quarters_back=quarters_back
            )
            
            if 'error' in results:
                console.print(f"  [red]Error: {results['error']}[/red]")
                return {}
            
            if 'term_results' in results and term in results['term_results']:
                term_data = results['term_results'][term]
                
                console.print(f"  [green]Hit Rate: {term_data['hit_rate']:.1%}[/green]")
                console.print(f"  [green]Total Mentions: {term_data['total_mentions']}[/green]")
                console.print(f"  [green]Quarters with Mentions: {term_data['quarters_with_mentions']}/{term_data['total_quarters_analyzed']}[/green]")
                console.print(f"  [dim]Analyzing {quarters_back} quarters back[/dim]")
                console.print(f"  [dim]Search term: '{term}'[/dim]")
                
                # Show mentions by quarter with context
                console.print(f"\n  [bold]Mentions by Quarter:[/bold]")
                for quarter, data in term_data['mentions_by_quarter'].items():
                    if data['count'] > 0:
                        console.print(f"    [green]{quarter}: {data['count']} mentions[/green]")
                        # Show sample contexts
                        for i, mention in enumerate(data['mentions'][:2]):
                            context = mention['context']
                            console.print(f"      {i+1}. \"{mention['full_match']}\" - {context[:100]}...")
                    else:
                        console.print(f"    [dim]{quarter}: No mentions[/dim]")
                
                # Show current streak
                current_streak = term_data['current_streak']
                longest_streak = term_data['longest_streak']
                console.print(f"\n  [bold]Streak Analysis:[/bold]")
                console.print(f"    Current: {current_streak['type']} streak of {current_streak['length']} quarters")
                console.print(f"    Longest: {longest_streak['type']} streak of {longest_streak['length']} quarters")
                
                return {
                    'hit_rate': term_data['hit_rate'],
                    'total_mentions': term_data['total_mentions'],
                    'quarters_analyzed': term_data['total_quarters_analyzed'],
                    'quarters_with_mentions': term_data['quarters_with_mentions'],
                    'mentions_by_quarter': term_data['mentions_by_quarter'],
                    'current_streak': current_streak,
                    'longest_streak': longest_streak,
                    'company_ticker': company_ticker
                }
            else:
                console.print(f"  [yellow]No historical data found for '{term}'[/yellow]")
                return {}
                
        except Exception as e:
            console.print(f"  [red]Error analyzing earnings: {e}[/red]")
            return {}
    
    async def _analyze_market_edge(self, term: str, markets: List[Dict]) -> Dict:
        """Analyze market prices and calculate edge for the term."""
        console.print(f"  Analyzing market prices and edge for '{term}'...")
        
        # Find the market for this specific term
        target_market = None
        for market in markets:
            bet_word = self.extract_bet_word(market)
            if bet_word and bet_word.lower() == term.lower():
                target_market = market
                break
        
        if not target_market:
            console.print(f"  [yellow]No market found for term '{term}'[/yellow]")
            return {}
        
        yes_bid = target_market.get('yes_bid', 0)
        yes_ask = target_market.get('yes_ask', 0)
        no_bid = target_market.get('no_bid', 0)
        no_ask = target_market.get('no_ask', 0)
        volume = target_market.get('volume', 0)
        
        # Convert from cents to decimal (Kalshi stores prices as integers representing cents)
        yes_bid = yes_bid / 100 if yes_bid else 0
        yes_ask = yes_ask / 100 if yes_ask else 0
        no_bid = no_bid / 100 if no_bid else 0
        no_ask = no_ask / 100 if no_ask else 0
        
        console.print(f"  [green]Market Prices:[/green]")
        console.print(f"    YES: Bid {yes_bid:.3f} | Ask {yes_ask:.3f}")
        console.print(f"    NO:  Bid {no_bid:.3f} | Ask {no_ask:.3f}")
        console.print(f"    Volume: ${volume:,.0f}")
        
        # Calculate implied probabilities
        yes_implied_prob = (yes_bid + yes_ask) / 2
        no_implied_prob = (no_bid + no_ask) / 2
        
        console.print(f"  [green]Implied Probabilities:[/green]")
        console.print(f"    YES: {yes_implied_prob:.1%}")
        console.print(f"    NO:  {no_implied_prob:.1%}")
        
        return {
            'yes_bid': yes_bid,
            'yes_ask': yes_ask,
            'no_bid': no_bid,
            'no_ask': no_ask,
            'yes_implied_prob': yes_implied_prob,
            'no_implied_prob': no_implied_prob,
            'volume': volume,
            'market_ticker': target_market.get('ticker', '')
        }
    
    async def _generate_critical_analysis(self, term: str, event_title: str, earnings_data: Dict, market_data: Dict):
        """Generate critical analysis with 5 unique questions for the term."""
        if not self.ai_analyzer:
            console.print("  [yellow]AI analyzer not configured. Skipping critical analysis.[/yellow]")
            return
        
        console.print(f"  Generating critical analysis for '{term}'...")
        
        try:
            # Prepare comprehensive data context
            data_context = f"""
            HISTORICAL EARNINGS DATA:
            - Hit Rate: {earnings_data.get('hit_rate', 0):.1%}
            - Total Mentions: {earnings_data.get('total_mentions', 0)}
            - Quarters Analyzed: {earnings_data.get('quarters_analyzed', 0)}
            - Quarters with Mentions: {earnings_data.get('quarters_with_mentions', 0)}
            - Current Streak: {earnings_data.get('current_streak', {}).get('type', 'N/A')} streak of {earnings_data.get('current_streak', {}).get('length', 0)} quarters
            - Longest Streak: {earnings_data.get('longest_streak', {}).get('type', 'N/A')} streak of {earnings_data.get('longest_streak', {}).get('length', 0)} quarters
            
            MARKET DATA:
            - YES Implied Probability: {market_data.get('yes_implied_prob', 0):.1%}
            - NO Implied Probability: {market_data.get('no_implied_prob', 0):.1%}
            - Market Volume: ${market_data.get('volume', 0):,.0f}
            - YES Bid/Ask: {market_data.get('yes_bid', 0):.3f}/{market_data.get('yes_ask', 0):.3f}
            - NO Bid/Ask: {market_data.get('no_bid', 0):.3f}/{market_data.get('no_ask', 0):.3f}
            
            HISTORICAL CONTEXT BY QUARTER:
            """
            
            # Add quarter-by-quarter context
            mentions_by_quarter = earnings_data.get('mentions_by_quarter', {})
            for quarter, data in mentions_by_quarter.items():
                if data['count'] > 0:
                    data_context += f"\n{quarter}: {data['count']} mentions"
                    for mention in data['mentions'][:2]:  # Show up to 2 contexts per quarter
                        context = mention['context'][:150] + "..." if len(mention['context']) > 150 else mention['context']
                        data_context += f"\n  - \"{mention['full_match']}\" in context: {context}"
            
            prompt = f"""
            You are a quantitative analyst conducting a critical analysis of whether the term "{term}" will be mentioned in the upcoming earnings call for "{event_title}".
            
            CRITICAL ANALYSIS REQUIREMENTS:
            1. Base analysis on the HISTORICAL DATA provided below
            2. Calculate the EDGE (Historical Hit Rate - Market Implied Probability)
            3. Identify patterns and trends in the historical context
            4. Provide 5 UNIQUE critical thinking questions specific to this term
            5. Be analytical, not assumptional - use data to support conclusions
            
            {data_context}
            
            ANALYSIS FRAMEWORK:
            
            A. QUANTITATIVE ANALYSIS
            - Calculate edge: Historical Hit Rate vs Market Implied Probability
            - Analyze trend direction (increasing/decreasing mentions over time)
            - Assess streak reliability and potential mean reversion
            - Evaluate volume and market efficiency
            
            B. CONTEXTUAL ANALYSIS
            - Analyze the contexts where the term appears
            - Identify patterns in usage (positive/negative sentiment, strategic vs operational)
            - Look for seasonal or cyclical patterns
            - Assess company-specific factors that drive mentions
            
            C. RISK ASSESSMENT
            - Identify potential risks to historical patterns
            - Consider alternative scenarios
            - Assess information gaps and limitations
            - Evaluate market efficiency vs historical data
            
            OUTPUT FORMAT (JSON):
            {{
                "probability_assessment": "X%",
                "confidence_level": "High/Medium/Low",
                "edge_analysis": {{
                    "historical_hit_rate": "{earnings_data.get('hit_rate', 0):.1%}",
                    "market_implied_probability": "{market_data.get('yes_implied_prob', 0):.1%}",
                    "edge": "X.X%",
                    "edge_direction": "Positive/Negative",
                    "edge_significance": "Significant/Moderate/Minimal"
                }},
                "trend_analysis": {{
                    "direction": "Increasing/Decreasing/Stable",
                    "volatility": "High/Medium/Low",
                    "reliability": "High/Medium/Low",
                    "key_patterns": ["pattern1", "pattern2"]
                }},
                "context_analysis": {{
                    "primary_contexts": ["context1", "context2"],
                    "sentiment_pattern": "Positive/Negative/Mixed",
                    "strategic_vs_operational": "Strategic/Operational/Mixed",
                    "seasonal_patterns": ["pattern1", "pattern2"]
                }},
                "risk_factors": {{
                    "high_probability_risks": ["risk1", "risk2"],
                    "low_probability_risks": ["risk1", "risk2"],
                    "information_gaps": ["gap1", "gap2"]
                }},
                "critical_questions": [
                    "Question 1: [Specific question about historical patterns and reliability]",
                    "Question 2: [Specific question about edge calculation and market efficiency]",
                    "Question 3: [Specific question about context patterns and future applicability]",
                    "Question 4: [Specific question about risk management and position sizing]",
                    "Question 5: [Specific question about alternative scenarios and exit strategies]"
                ],
                "analytical_reasoning": "Detailed explanation of how conclusions were reached based on historical data, market prices, and contextual patterns"
            }}
            
            Make each critical question UNIQUE and SPECIFIC to this term and its historical patterns.
            Base all conclusions on the provided data, not assumptions.
            """
            
            analysis = await self.ai_analyzer.generate_summary(prompt)
            
            console.print(f"  [green]Critical Analysis Complete[/green]")
            console.print(f"\n[bold]Critical Analysis & Decision Framework:[/bold]")
            console.print(analysis)
            
            # Ask if user wants to ask questions
            console.print(f"\n[bold]💬 Interactive Q&A[/bold]")
            console.print("You can ask follow-up questions about the analysis and transcript data.")
            answer = Prompt.ask("Would you like to ask a question? (y/n)", default="n")
            
            if answer.lower() == 'y':
                await self._interactive_qa(term, event_title, earnings_data, analysis)
            
        except Exception as e:
            console.print(f"  [red]Error generating critical analysis: {e}[/red]")
    
    async def _interactive_qa(self, term: str, event_title: str, earnings_data: Dict, previous_analysis: str):
        """Interactive Q&A session with the AI."""
        if not self.ai_analyzer:
            console.print("  [yellow]AI analyzer not configured.[/yellow]")
            return
        
        while True:
            question = Prompt.ask("\n💬 Your question (or 'q' to quit)")
            
            if question.lower() == 'q':
                break
            
            try:
                # Prepare comprehensive context
                data_context = f"""
                PREVIOUS ANALYSIS:
                {previous_analysis}
                
                HISTORICAL EARNINGS DATA:
                - Hit Rate: {earnings_data.get('hit_rate', 0):.1%}
                - Total Mentions: {earnings_data.get('total_mentions', 0)}
                - Quarters Analyzed: {earnings_data.get('quarters_analyzed', 0)}
                - Quarters with Mentions: {earnings_data.get('quarters_with_mentions', 0)}
                - Current Streak: {earnings_data.get('current_streak', {}).get('type', 'N/A')} streak of {earnings_data.get('current_streak', {}).get('length', 0)} quarters
                
                HISTORICAL CONTEXT BY QUARTER:
                """
                
                # Add relevant quarter context
                mentions_by_quarter = earnings_data.get('mentions_by_quarter', {})
                for quarter, data in list(mentions_by_quarter.items())[:5]:  # Show last 5 quarters
                    if data['count'] > 0:
                        data_context += f"\n{quarter}: {data['count']} mentions"
                        for mention in data['mentions'][:2]:
                            context = mention['context'][:200] + "..." if len(mention['context']) > 200 else mention['context']
                            data_context += f"\n  - \"{mention['full_match']}\" in context: {context}"
                
                prompt = f"""
                You are a quantitative analyst helping with a follow-up question about the term "{term}" in the earnings call for "{event_title}".
                
                USER'S QUESTION:
                {question}
                
                CONTEXT:
                {data_context}
                
                Please provide a clear, data-driven answer based on the historical context and analysis above.
                """
                
                answer = await self.ai_analyzer.generate_summary(prompt)
                console.print(f"\n[bold]📊 Answer:[/bold]")
                console.print(answer)
                
            except Exception as e:
                console.print(f"  [red]Error: {e}[/red]")
    
    async def _analyze_news_sources(self, term: str, event_title: str):
        """Scrape news sources for the term and event."""
        from .web_scraper import NewsScraper
        
        console.print(f"  Scraping news sources for '{term}' and '{event_title}'...")
        
        try:
            async with NewsScraper() as scraper:
                # Search for news related to the term and event
                search_queries = [
                    f"{term} earnings",
                    f"{term} quarterly results",
                    f"{term} Alphabet"
                ]
                
                all_articles = []
                for query in search_queries:
                    articles = await scraper.search_news(query, max_articles=5)
                    all_articles.extend(articles)
                
                # Remove duplicates
                seen_urls = set()
                unique_articles = []
                for article in all_articles:
                    if article.get('url') not in seen_urls:
                        seen_urls.add(article.get('url'))
                        unique_articles.append(article)
                
                console.print(f"  [green]Found {len(unique_articles)} relevant articles[/green]")
                
                # Display top articles
                for i, article in enumerate(unique_articles[:5], 1):
                    console.print(f"    {i}. [bold]{article.get('title', 'No title')}[/bold]")
                    console.print(f"       [dim]Source: {article.get('source', 'Unknown')}[/dim]")
                    console.print(f"       [dim]URL: {article.get('url', 'No URL')}[/dim]")
                    console.print(f"       [dim]Published: {article.get('published', 'Unknown date')}[/dim]")
                    console.print()
                
                return unique_articles
                
        except Exception as e:
            console.print(f"  [red]Error scraping news: {e}[/red]")
            return []
    
    async def _generate_ai_summary(self, term: str, event_title: str, news_articles: List[Dict] = None):
        """Generate AI summary with reasoning and critical analysis."""
        if not self.ai_analyzer:
            console.print("  [yellow]AI analyzer not configured. Skipping AI summary.[/yellow]")
            return
        
        console.print(f"  Generating AI summary for '{term}' in '{event_title}'...")
        
        try:
            # Prepare news context
            news_context = ""
            if news_articles and len(news_articles) > 0:
                news_context = "\n\nRecent News Articles Found:\n"
                for i, article in enumerate(news_articles[:5], 1):
                    news_context += f"{i}. {article.get('title', 'No title')} - {article.get('source', 'Unknown source')}\n"
                    if article.get('summary'):
                        news_context += f"   Summary: {article['summary'][:200]}...\n"
                    news_context += f"   URL: {article.get('link', 'No URL')}\n\n"
            else:
                news_context = "\n\nNote: No recent news articles were found for this analysis."
            
            prompt = f"""
            You are a financial analyst conducting a critical analysis of whether the term "{term}" will be mentioned in the upcoming earnings call for "{event_title}".
            
            CRITICAL ANALYSIS REQUIREMENTS:
            1. Base your analysis on DATA and EVIDENCE, not assumptions
            2. Cite specific sources and data points
            3. Identify potential biases and limitations
            4. Provide 3 critical questions investors should ask before trading
            
            ANALYSIS FRAMEWORK:
            
            A. HISTORICAL DATA ANALYSIS
            - Analyze historical mention patterns from earnings calls
            - Identify trends, frequency, and context of mentions
            - Note any seasonal or cyclical patterns
            
            B. CURRENT MARKET CONTEXT
            - Recent company announcements and strategic initiatives
            - Industry trends and competitive landscape
            - Regulatory environment and policy changes
            - Market sentiment and analyst expectations
            
            C. NEWS AND MEDIA ANALYSIS
            {news_context}
            
            D. RISK ASSESSMENT
            - Identify potential risks and uncertainties
            - Consider alternative scenarios
            - Assess information gaps and limitations
            
            E. CRITICAL QUESTIONS FOR TRADERS
            Provide 3 specific questions traders should ask themselves before making this trade.
            
            OUTPUT FORMAT (JSON):
            {{
                "probability_assessment": "X%",
                "confidence_level": "High/Medium/Low",
                "historical_analysis": {{
                    "mention_frequency": "X%",
                    "trend_direction": "Increasing/Decreasing/Stable",
                    "key_contexts": ["context1", "context2"],
                    "data_sources": ["source1", "source2"]
                }},
                "current_context": {{
                    "company_factors": ["factor1", "factor2"],
                    "industry_factors": ["factor1", "factor2"],
                    "regulatory_factors": ["factor1", "factor2"],
                    "news_sentiment": "Positive/Neutral/Negative"
                }},
                "risk_factors": {{
                    "high_probability_risks": ["risk1", "risk2"],
                    "low_probability_risks": ["risk1", "risk2"],
                    "information_gaps": ["gap1", "gap2"]
                }},
                "critical_questions": [
                    "Question 1: [Specific question about the trade]",
                    "Question 2: [Specific question about risk management]",
                    "Question 3: [Specific question about alternative scenarios]"
                ],
                "source_verification": {{
                    "data_sources_used": ["source1", "source2"],
                    "news_articles_analyzed": {len(news_articles) if news_articles else 0},
                    "limitations": ["limitation1", "limitation2"]
                }},
                "analytical_reasoning": "Detailed explanation of how conclusions were reached based on available data"
            }}
            
            Be analytical, not assumptional. Base conclusions on evidence.
            """
            
            summary = await self.ai_analyzer.generate_summary(prompt)
            
            console.print(f"  [green]AI Analysis Complete[/green]")
            console.print(f"\n[bold]Critical Analysis Summary:[/bold]")
            console.print(summary)
            
        except Exception as e:
            console.print(f"  [red]Error generating AI summary: {e}[/red]")
    
    def _extract_company_ticker_from_event(self, event_title: str) -> str:
        """Extract company ticker from event title."""
        # Extract from patterns like "What will Apple say during earnings?"
        match = re.search(r"What will (.+?) say during", event_title)
        if match:
            company_name = match.group(1).strip()
            
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
        
        return "UNKNOWN"
    
    async def extract_from_url(self, url: str):
        """Extract market data from a Kalshi URL."""
        import re
        
        console.print(f"\n[blue]Processing URL: {url}[/blue]")
        
        # Extract ticker from URL
        # Pattern for URLs like: kalshi.com/markets/kxfedmention/fed-mention/kxfedmention-25oct
        url = url.replace('https://', '').replace('http://', '')
        match = re.search(r'kalshi\.com/markets/[^/]+/[^/]+/([^/?]+)', url)
        
        if not match:
            # Try alternative pattern
            match = re.search(r'/([^/?]+)$', url)
        
        if not match:
            console.print("[red]❌ Could not extract ticker from URL[/red]")
            return
        
        ticker = match.group(1)
        console.print(f"[green]✅ Extracted ticker: {ticker}[/green]")
        
        try:
            # Get market data using the ticker
            market_data = self.kalshi_api.get_market_details(ticker)
            
            if not market_data:
                console.print("[yellow]⚠️ No market data returned[/yellow]")
                return
            
            console.print(f"[green]✅ Successfully retrieved market data[/green]")
            
            # Display market data
            table = Table(title="📊 Market Data")
            table.add_column("Field", style="cyan", width=20)
            table.add_column("Value", style="white", width=60)
            
            fields_to_show = [
                ('ticker', 'Ticker'),
                ('title', 'Title'),
                ('description', 'Description'),
                ('status', 'Status'),
                ('yes_ask', 'Yes Ask'),
                ('no_ask', 'No Ask'),
                ('yes_bid', 'Yes Bid'),
                ('no_bid', 'No Bid'),
                ('volume', 'Volume'),
                ('open_interest', 'Open Interest'),
                ('close_time', 'Close Time')
            ]
            
            for field, label in fields_to_show:
                value = market_data.get(field, 'N/A')
                if value != 'N/A' and value is not None:
                    if isinstance(value, (int, float)):
                        value = f"{value:.2f}" if field in ['yes_ask', 'no_ask', 'yes_bid', 'no_bid'] else str(value)
                    table.add_row(label, str(value)[:60])
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]❌ Error retrieving market data: {e}[/red]")
    
    async def search_news(self, query: str):
        """Search for news articles."""
        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}")) as progress:
            task = progress.add_task("Searching news...", total=None)
            
            try:
                async with NewsScraper() as scraper:
                    articles = await scraper.search_news(query, max_articles=10)
                    progress.update(task, description="Found news articles!")
                    
                    if articles:
                        table = Table(title=f"News Articles for: {query}")
                        table.add_column("Title", style="white", width=60)
                        table.add_column("Source", style="cyan")
                        table.add_column("Published", style="yellow")
                        
                        for article in articles:
                            table.add_row(
                                article.get('title', 'N/A')[:60],
                                article.get('source', 'N/A'),
                                article.get('published', 'N/A')[:20]
                            )
                        
                        console.print(table)
                    else:
                        console.print(f"[yellow]No news articles found for: {query}[/yellow]")
            
            except Exception as e:
                console.print(f"[red]Error searching news: {e}[/red]")
    
    def calculate_kelly(self, bankroll: float, win_prob_percent: float, market_price: float = None):
        """
        Calculate optimal bet size using Kelly Criterion.
        
        Kelly Criterion formula: f = (p * b - q) / b
        Where:
        - f = fraction of bankroll to bet
        - p = probability of winning (as decimal)
        - q = probability of losing (1 - p)
        - b = net odds received on the wager
        
        For Kalshi markets:
        - If market price is P cents, you pay P cents per share
        - If you win, you get 100 cents (1 dollar) per share
        - Net profit = (100 - P) cents per share
        - So b = (100 - P) / P
        
        Args:
            bankroll: Total bankroll amount
            win_prob_percent: Win probability as a percentage (e.g., 50 for 50%)
            market_price: Market price in cents (0-100). If None, assumes even odds (b=1)
        """
        try:
            # Convert percentage to decimal
            p = win_prob_percent / 100.0
            q = 1 - p
            
            # Calculate odds based on market price
            if market_price is not None:
                # For Kalshi: if you buy at price P, you get (100-P) profit when you win
                # So odds b = (100 - P) / P
                if market_price <= 0 or market_price >= 100:
                    console.print("[red]Market price must be between 1 and 99 cents.[/red]")
                    return
                b = (100 - market_price) / market_price
            else:
                # Even odds: you double your money if you win
                b = 1.0
            
            # Kelly Criterion formula
            kelly_fraction = (p * b - q) / b
            
            # Kelly fraction should be between 0 and 1
            if kelly_fraction < 0:
                kelly_fraction = 0
                edge = "No positive edge - don't bet"
            elif kelly_fraction > 1:
                kelly_fraction = 1
                edge = "Very high edge - max bet"
            else:
                # Edge as percentage of bet
                edge_pct = (p * (1 + b) - 1) * 100
                edge = f"Edge: {edge_pct:.2f}%"
            
            # Calculate bet amount
            bet_amount = bankroll * kelly_fraction
            
            # Calculate expected value
            expected_value = (p * (1 + b) - 1) * bet_amount
            
            # Display results
            table = Table(title="Kelly Criterion Betting Calculator", show_header=True, header_style="bold magenta")
            table.add_column("Metric", style="cyan", no_wrap=True)
            table.add_column("Value", style="green")
            
            table.add_row("Bankroll", f"${bankroll:,.2f}")
            table.add_row("Win Probability", f"{win_prob_percent:.1f}%")
            if market_price is not None:
                table.add_row("Market Price", f"{market_price:.1f} cents")
                table.add_row("Odds (b)", f"{b:.3f}")
            else:
                table.add_row("Odds (b)", f"{b:.3f} (even odds)")
            table.add_row("Kelly Fraction", f"{kelly_fraction:.4f} ({kelly_fraction*100:.2f}%)")
            table.add_row("Recommended Bet", f"${bet_amount:,.2f}")
            table.add_row("Expected Value", f"${expected_value:,.2f}")
            table.add_row("", edge)
            
            console.print(table)
            
            # Additional recommendations
            if kelly_fraction == 0:
                console.print("\n[yellow]⚠️  No positive expected value. Kelly Criterion recommends not betting.[/yellow]")
            elif kelly_fraction > 0.25:
                console.print("\n[yellow]⚠️  Kelly fraction is high (>25%). Consider using fractional Kelly (half-Kelly) for lower risk.[/yellow]")
                half_kelly_bet = bankroll * (kelly_fraction / 2)
                console.print(f"[yellow]Half-Kelly bet: ${half_kelly_bet:,.2f}[/yellow]")
            else:
                console.print("\n[green]✓ Kelly Criterion recommends this bet size.[/green]")
                
        except Exception as e:
            console.print(f"[red]Error calculating Kelly Criterion: {e}[/red]")
    
    def show_config(self):
        """Show current configuration."""
        config_text = f"""
        🔧 Configuration:
        
        Kalshi API: {'✓ Configured' if self.config.kalshi_api_key else '✗ Not configured'}
        OpenAI API: {'✓ Configured' if self.config.openai_api_key else '✗ Not configured'}
        Twitter API: {'✓ Configured' if self.config.twitter.get('api_key') else '✗ Disabled (costs money)'}
        Database: {self.config.database_url}
        AI Model: {self.config.openai_model}
        Max Tokens: {self.config.openai_max_tokens}
        Temperature: {self.config.openai_temperature}
        """
        
        console.print(Panel(config_text, title="Configuration", border_style="yellow"))
    
    async def handle_transcript_command(self, args: str):
        """Handle transcript download/view commands."""
        parts = args.strip().split()
        
        if len(parts) == 1:
            # Show available quarters for company
            ticker = parts[0].upper()
            await self.show_available_quarters(ticker)
        elif len(parts) == 3:
            # Download/view specific transcript
            ticker = parts[0].upper()
            try:
                year = int(parts[1])
                quarter = int(parts[2])
                await self.download_transcript(ticker, year, quarter)
            except ValueError:
                console.print("[red]Invalid year or quarter. Please use numbers (e.g., transcript GOOGL 2025 2)[/red]")
        else:
            console.print("[red]Invalid transcript command format.[/red]")
            console.print("[yellow]Usage:[/yellow]")
            console.print("  transcript <ticker>                    - Show available quarters")
            console.print("  transcript <ticker> <year> <quarter>    - Download/view transcript")
            console.print("[yellow]Examples:[/yellow]")
            console.print("  transcript GOOGL                       - Show GOOGL quarters")
            console.print("  transcript GOOGL 2025 2                - Download GOOGL Q2 2025")
    
    async def show_available_quarters(self, ticker: str):
        """Show available quarters for a company."""
        console.print(f"[bold blue]📅 Available Quarters for {ticker}[/bold blue]")
        
        try:
            from .earnings_pipeline import EarningsCallPipeline
            pipeline = EarningsCallPipeline(self.config.api_ninjas_key)
            
            # Get available quarters
            quarters = await pipeline.api_client.get_available_quarters(ticker, 5)  # Last 5 years
            
            if not quarters:
                console.print(f"[yellow]No quarters found for {ticker}[/yellow]")
                return
            
            table = Table(title=f"Available Quarters for {ticker}")
            table.add_column("Quarter", style="cyan")
            table.add_column("Year", style="yellow")
            table.add_column("Status", style="green")
            
            for year, quarter in quarters:
                # Check if transcript exists
                async with pipeline.api_client as client:
                    call = await client.get_earnings_transcript(ticker, year, quarter)
                    status = "✅ Available" if call else "❌ Not available"
                
                table.add_row(f"Q{quarter}", str(year), status)
            
            console.print(table)
            
        except Exception as e:
            console.print(f"[red]Error fetching quarters for {ticker}: {e}[/red]")
    
    async def download_transcript(self, ticker: str, year: int, quarter: int):
        """Download or view a specific earnings transcript."""
        console.print(f"[bold blue]📄 Fetching {ticker} Q{quarter} {year} Transcript[/bold blue]")
        
        try:
            from .earnings_pipeline import EarningsCallPipeline
            pipeline = EarningsCallPipeline(self.config.api_ninjas_key)
            
            # Fetch the transcript
            async with pipeline.api_client as client:
                call = await client.get_earnings_transcript(ticker, year, quarter)
            
            if not call:
                console.print(f"[red]❌ Transcript not found for {ticker} Q{quarter} {year}[/red]")
                return
            
            # Show transcript info
            console.print(f"[green]✅ Found transcript: {call.company_name} Q{quarter} {year}[/green]")
            console.print(f"[dim]Date: {call.date}[/dim]")
            console.print(f"[dim]Length: {len(call.transcript):,} characters[/dim]")
            
            # Ask user what they want to do
            console.print("\n[yellow]What would you like to do?[/yellow]")
            console.print("1. View full transcript in terminal (paginated)")
            console.print("2. Download transcript to file")
            console.print("3. Search for specific terms in transcript")
            
            choice = Prompt.ask("Choose option (1-3)", default="1")
            
            if choice == "1":
                await self.view_transcript_in_terminal(call)
            elif choice == "2":
                await self.download_transcript_to_file(call)
            elif choice == "3":
                await self.search_transcript(call)
            else:
                console.print("[yellow]Invalid choice, showing transcript in terminal...[/yellow]")
                await self.view_transcript_in_terminal(call)
                
        except Exception as e:
            console.print(f"[red]Error fetching transcript: {e}[/red]")
    
    async def view_transcript_in_terminal(self, call):
        """View transcript in terminal with pagination."""
        console.print(f"\n[bold blue]📖 {call.company_name} Q{call.quarter} {call.year} Transcript[/bold blue]")
        console.print(f"[dim]Date: {call.date}[/dim]")
        console.print("=" * 80)
        
        # Split transcript into pages
        lines = call.transcript.split('\n')
        page_size = 50  # Lines per page
        total_pages = (len(lines) + page_size - 1) // page_size
        
        current_page = 0
        
        while current_page < total_pages:
            start_line = current_page * page_size
            end_line = min(start_line + page_size, len(lines))
            
            console.print(f"\n[bold yellow]Page {current_page + 1} of {total_pages}[/bold yellow]")
            console.print("-" * 40)
            
            for i in range(start_line, end_line):
                line = lines[i].strip()
                if line:
                    console.print(line)
            
            console.print("-" * 40)
            console.print(f"[dim]Lines {start_line + 1}-{end_line} of {len(lines)}[/dim]")
            
            if current_page < total_pages - 1:
                action = Prompt.ask("Press Enter for next page, 'q' to quit, 'g' to go to specific page, or 's' to search", default="")
                if action.lower() == 'q':
                    break
                elif action.lower() == 'g':
                    try:
                        page_num = int(Prompt.ask(f"Go to page (1-{total_pages})", default=str(current_page + 2)))
                        if 1 <= page_num <= total_pages:
                            current_page = page_num - 1
                        else:
                            console.print("[red]Invalid page number[/red]")
                    except ValueError:
                        console.print("[red]Invalid page number[/red]")
                elif action.lower() == 's':
                    await self.search_transcript(call)
                    break
                else:
                    current_page += 1
            else:
                console.print("\n[green]End of transcript[/green]")
                break
    
    async def download_transcript_to_file(self, call):
        """Download transcript to a file."""
        filename = f"{call.ticker}_Q{call.quarter}_{call.year}_transcript.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"{call.company_name} Q{call.quarter} {call.year} Earnings Call Transcript\n")
                f.write(f"Date: {call.date}\n")
                f.write("=" * 80 + "\n\n")
                f.write(call.transcript)
            
            console.print(f"[green]✅ Transcript saved to: {filename}[/green]")
            console.print(f"[dim]File size: {len(call.transcript):,} characters[/dim]")
            
        except Exception as e:
            console.print(f"[red]Error saving transcript: {e}[/red]")
    
    async def search_transcript(self, call):
        """Search for specific terms in the transcript."""
        search_term = Prompt.ask("Enter search term")
        
        if not search_term:
            console.print("[yellow]No search term provided[/yellow]")
            return
        
        console.print(f"\n[bold blue]🔍 Searching for '{search_term}' in {call.company_name} Q{call.quarter} {call.year}[/bold blue]")
        
        # Search for the term (case-insensitive)
        lines = call.transcript.split('\n')
        matches = []
        
        # Use regex to find all matches, not just lines
        import re
        from .earnings_pipeline import KalshiMentionMatcher
        matcher = KalshiMentionMatcher()
        pattern = matcher.create_regex_pattern(search_term)
        
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
            
            matches.append({
                'line_number': line_num,
                'line': line_text,
                'context': context,
                'match_text': match.group(),
                'position': match.start()
            })
        
        if not matches:
            console.print(f"[yellow]No matches found for '{search_term}'[/yellow]")
            return
        
        console.print(f"[green]Found {len(matches)} matches:[/green]")
        
        # Show matches with full context and highlighted match
        for i, match in enumerate(matches[:20]):  # Show first 20 matches
            console.print(f"\n[bold cyan]Match {i + 1} (Line {match['line_number']}):[/bold cyan]")
            console.print(f"[dim]Match: \"{match['match_text']}\"[/dim]")
            
            # Highlight the match within the context
            context = match['context']
            match_text = match['match_text']
            
            # Find the match position within the context
            match_start = context.lower().find(match_text.lower())
            if match_start != -1:
                # Split context around the match and highlight it
                before_match = context[:match_start]
                after_match = context[match_start + len(match_text):]
                
                console.print(f"[dim]Context:[/dim]")
                console.print(f"[dim]{before_match}[/dim][bold red]{match_text}[/bold red][dim]{after_match}[/dim]")
            else:
                # Fallback if match not found in context
                console.print(f"[dim]Context: {context}[/dim]")
            
            if i < len(matches) - 1 and i < 19:
                action = Prompt.ask("Press Enter for next match, 'q' to quit", default="")
                if action.lower() == 'q':
                    break
        
        if len(matches) > 20:
            console.print(f"\n[yellow]... and {len(matches) - 20} more matches[/yellow]")
        
        # Ask if user wants AI summary
        console.print(f"\n[yellow]Would you like AI to give you a brief summary on how '{search_term}' relates to {call.company_name}'s strategy?[/yellow]")
        summary_choice = Prompt.ask("Generate AI summary? (y/n)", default="y")
        
        if summary_choice.lower() in ['y', 'yes']:
            await self.generate_transcript_summary(call, search_term, matches)
    
    async def generate_transcript_summary(self, call, search_term: str, matches: List[Dict]):
        """Generate AI summary of how the search term relates to the company's strategy."""
        console.print(f"\n[bold blue]🤖 Generating AI Summary for '{search_term}' in {call.company_name} Q{call.quarter} {call.year}[/bold blue]")
        
        try:
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
                context = match['context']
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

IMPORTANT: Respond in plain text format only, not JSON. Just provide the analysis paragraphs directly.
"""

            # Generate AI summary
            summary = await self.ai_analyzer.generate_summary(prompt)
            
            console.print(f"\n[bold green]📋 AI Analysis Summary:[/bold green]")
            console.print("=" * 60)
            console.print(summary)
            console.print("=" * 60)
            
            # Ask if user wants to save summary
            save_choice = Prompt.ask("\nSave this summary to a file? (y/n)", default="n")
            if save_choice.lower() in ['y', 'yes']:
                filename = f"{call.ticker}_Q{call.quarter}_{call.year}_{search_term.replace(' ', '_')}_summary.txt"
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"{call.company_name} Q{call.quarter} {call.year} - AI Analysis of '{search_term}'\n")
                        f.write(f"Date: {call.date}\n")
                        f.write(f"Total Matches: {len(matches)}\n")
                        f.write("=" * 80 + "\n\n")
                        f.write(summary)
                    
                    console.print(f"[green]✅ Summary saved to: {filename}[/green]")
                except Exception as e:
                    console.print(f"[red]Error saving summary: {e}[/red]")
            
            # Ask if user wants to ask follow-up questions
            console.print(f"\n[bold]💬 Interactive Q&A[/bold]")
            console.print("Ask questions about the transcript, search term context, or AI analysis.")
            qa_choice = Prompt.ask("Would you like to ask a question? (y/n)", default="n")
            
            if qa_choice.lower() == 'y':
                await self._transcript_qa(call, search_term, matches, summary)
                    
        except Exception as e:
            console.print(f"[red]Error generating AI summary: {e}[/red]")
    
    async def _transcript_qa(self, call, search_term: str, matches: List[Dict], previous_summary: str):
        """Interactive Q&A about the transcript and analysis."""
        if not self.ai_analyzer:
            console.print("  [yellow]AI analyzer not configured.[/yellow]")
            return
        
        while True:
            question = Prompt.ask("\n💬 Your question", default="")
            
            if not question or question.lower() == 'q':
                break
            
            try:
                # Prepare context with matches
                contexts_text = ""
                for i, match in enumerate(matches[:5], 1):
                    # Get a reasonable snippet around the match
                    context = match['context']
                    match_text = match.get('match_text', search_term)
                    match_pos = context.lower().find(match_text.lower())
                    
                    if match_pos != -1 and len(context) > 500:
                        chars_per_side = 250
                        start = max(0, match_pos - chars_per_side)
                        end = min(len(context), match_pos + len(match_text) + chars_per_side)
                        snippet = context[start:end]
                        if start > 0:
                            snippet = "..." + snippet
                        if end < len(context):
                            snippet = snippet + "..."
                    else:
                        snippet = context[:500]
                    
                    contexts_text += f"\nMatch {i} (Line {match['line_number']}): {snippet}\n"
                
                prompt = f"""
You are analyzing the transcript from {call.company_name}'s Q{call.quarter} {call.year} earnings call.

USER'S QUESTION:
{question}

CONTEXT:
{call.company_name} Q{call.quarter} {call.year}
Date: {call.date}
Search Term: "{search_term}"
Total Matches: {len(matches)}

TRANSCRIPT EXCERPTS WITH CONTEXT:
{contexts_text}

PREVIOUS AI ANALYSIS:
{previous_summary}

Please provide a clear, data-driven answer based on the transcript context and analysis above.
"""
                
                answer = await self.ai_analyzer.generate_summary(prompt)
                console.print(f"\n[bold]📊 Answer:[/bold]")
                console.print(answer)
                
            except Exception as e:
                console.print(f"  [red]Error: {e}[/red]")
    
    async def run_interactive_mode(self):
        """Run the interactive CLI mode."""
        self.display_welcome()
        
        while True:
            try:
                command = Prompt.ask("\n[kalshi-research]").strip().lower()
                
                if not command:
                    continue
                
                if command == 'exit' or command == 'quit':
                    console.print("[blue]Goodbye! 👋[/blue]")
                    break
                
                elif command == 'help':
                    self.display_help()
                
                elif command == 'clear':
                    console.clear()
                    self.display_welcome()
                
                elif command == 'config':
                    self.show_config()
                
                elif command.startswith('search '):
                    query = command[7:].strip()
                    if query:
                        await self.search_markets(query)
                    else:
                        console.print("[red]Please provide a search query.[/red]")
                
                elif command == 'trending':
                    await self.show_trending_markets()
                
                elif command.startswith('news '):
                    query = command[5:].strip()
                    if query:
                        await self.search_news(query)
                    else:
                        console.print("[red]Please provide a search query.[/red]")
                
                elif command == 'markets' or command == 'mentions':
                    await self.show_mention_markets()
                
                elif command.startswith('markets ') or command.startswith('mentions '):
                    # Parse number after "markets" or "mentions"
                    try:
                        n = int(command.split()[1])
                        await self.show_mention_markets(limit=n)
                    except (ValueError, IndexError):
                        console.print("[red]Invalid number. Use: markets <number> or mentions <number>[/red]")
                
                elif command.startswith('analyze '):
                    group_index = command[8:].strip()
                    if group_index.isdigit():
                        # Ensure markets are loaded
                        if not self.current_grouped_markets:
                            console.print("[yellow]Loading markets first...[/yellow]")
                            await self.show_mention_markets(limit=10)
                        
                        if self.current_grouped_markets:
                            await self.analyze_market_group(int(group_index), self.current_grouped_markets)
                        else:
                            console.print("[red]Please run 'markets' first to see available groups.[/red]")
                    else:
                        console.print("[red]Please provide a valid group number. Run 'markets' first to see available groups.[/red]")
                
                elif command.startswith('research '):
                    group_index = command[9:].strip()
                    if group_index.isdigit():
                        # Ensure markets are loaded
                        if not self.current_grouped_markets:
                            console.print("[yellow]Loading markets first...[/yellow]")
                            await self.show_mention_markets(limit=10)
                        
                        if self.current_grouped_markets:
                            await self.research_market_group(int(group_index), self.current_grouped_markets)
                        else:
                            console.print("[red]Please run 'markets' first to see available groups.[/red]")
                    else:
                        console.print("[red]Please provide a valid group number. Run 'markets' first to see available groups.[/red]")
                
                elif command.startswith('summary '):
                    group_index = command[8:].strip()
                    if group_index.isdigit():
                        # Ensure markets are loaded
                        if not self.current_grouped_markets:
                            console.print("[yellow]Loading markets first...[/yellow]")
                            await self.show_mention_markets(limit=10)
                        
                        if self.current_grouped_markets:
                            await self.generate_summary(int(group_index), self.current_grouped_markets)
                        else:
                            console.print("[red]Please run 'markets' first to see available groups.[/red]")
                    else:
                        console.print("[red]Please provide a valid group number. Run 'markets' first to see available groups.[/red]")
                
                elif command.startswith('deepdive '):
                    parts = command[9:].strip().split(' ', 1)
                    if len(parts) == 2 and parts[0].isdigit():
                        group_index = int(parts[0])
                        term = parts[1].strip('"\'')  # Remove surrounding quotes
                        
                        # Always ensure markets are loaded
                        if not self.current_grouped_markets:
                            console.print("[yellow]Loading markets first...[/yellow]")
                            await self.show_mention_markets(limit=10)
                        
                        if self.current_grouped_markets:
                            await self.deep_dive_analysis(group_index, term, self.current_grouped_markets, self.last_quarters_back)
                        else:
                            console.print("[red]Failed to load markets. Please try 'markets' command first.[/red]")
                    else:
                        console.print("[red]Please provide a valid group number and term. Usage: deepdive <group_number> <term>[/red]")
                        console.print("[red]Example: deepdive 1 \"AI / Artificial Intelligence\"[/red]")
                
                elif command.startswith('transcript '):
                    args = command[11:].strip()
                    await self.handle_transcript_command(args)
                
                elif command == 'kelly' or command == 'bankroll' or command.startswith('kelly ') or command.startswith('bankroll '):
                    # Parse: kelly <bankroll> <win_prob_percent> [market_price]
                    # Or: bankroll <bankroll> <win_prob_percent> [market_price]
                    parts = command.split()
                    if len(parts) >= 3:
                        try:
                            bankroll = float(parts[1])
                            win_prob = float(parts[2])
                            market_price = float(parts[3]) if len(parts) > 3 else None
                            
                            if bankroll <= 0:
                                console.print("[red]Bankroll must be greater than 0.[/red]")
                            elif win_prob < 0 or win_prob > 100:
                                console.print("[red]Win probability must be between 0 and 100.[/red]")
                            else:
                                self.calculate_kelly(bankroll, win_prob, market_price)
                        except ValueError:
                            console.print("[red]Invalid numbers. Usage: kelly <bankroll> <win_prob%> [market_price_cents][/red]")
                            console.print("[yellow]Example: kelly 1500 50[/yellow]")
                            console.print("[yellow]Example: kelly 1500 60 45[/yellow] (bankroll $1500, 60% win prob, market at 45 cents)")
                    else:
                        console.print("[bold]Kelly Criterion Betting Calculator[/bold]")
                        console.print("[yellow]Usage: kelly <bankroll> <win_prob%> [market_price_cents][/yellow]")
                        console.print("\n[cyan]Arguments:[/cyan]")
                        console.print("  • bankroll: Your total bankroll amount (e.g., 1500)")
                        console.print("  • win_prob%: Your estimated win probability as percentage (e.g., 50 for 50%)")
                        console.print("  • market_price: (Optional) Market price in cents (1-99). If omitted, assumes even odds.")
                        console.print("\n[cyan]Examples:[/cyan]")
                        console.print("  • [green]kelly 1500 50[/green] - Bankroll $1500, 50% win prob, even odds")
                        console.print("  • [green]kelly 1500 60 45[/green] - Bankroll $1500, 60% win prob, market at 45 cents")
                        console.print("  • [green]bankroll 2000 55 30[/green] - Bankroll $2000, 55% win prob, market at 30 cents")
                
                elif command == 'url':
                    url = input("Enter Kalshi market URL: ").strip()
                    if url:
                        await self.extract_from_url(url)
                    else:
                        console.print("[red]Please provide a URL.[/red]")
                
                else:
                    console.print(f"[red]Unknown command: {command}[/red]")
                    console.print("Type 'help' for available commands.")
            
            except KeyboardInterrupt:
                console.print("\n[blue]Goodbye! 👋[/blue]")
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

@click.command()
def cli():
    """Kalshi Mention Market Research Tool CLI."""
    try:
        # Load configuration
        config = load_config()
        
        # Create CLI instance
        cli_instance = KalshiResearchCLI(config)
        
        # Run interactive mode
        asyncio.run(cli_instance.run_interactive_mode())
    
    except Exception as e:
        console.print(f"[red]Failed to start CLI: {e}[/red]")
        return 1
    
    return 0
