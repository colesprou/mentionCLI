#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to find all mention markets from Kalshi.
"""

import sys
import os
import asyncio
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import load_config
from src.kalshi_api import KalshiAPI

console = Console()

async def find_all_mention_markets():
    """Find all mention markets using multiple methods."""
    console.print(Panel("🔍 Finding All Mention Markets", style="blue"))
    
    try:
        # Load configuration
        config = load_config()
        
        if not config.kalshi_api_key:
            console.print("[red]❌ Kalshi API key not configured[/red]")
            return []
        
        # Initialize API
        api = KalshiAPI(config.kalshi_api_key, config.kalshi_api_url)
        
        all_mention_markets = []
        
        # Method 1: Try API with category filter
        console.print("\n[blue]Method 1: Trying API with category filter...[/blue]")
        try:
            api_markets = api.get_mention_markets(limit=100)
            if api_markets:
                all_mention_markets.extend(api_markets)
                console.print(f"[green]✅ Found {len(api_markets)} markets via API[/green]")
            else:
                console.print("[yellow]⚠️ No markets found via API[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ API method failed: {e}[/red]")
        
        # Method 2: Web scraping
        console.print("\n[blue]Method 2: Trying web scraping...[/blue]")
        try:
            scraped_markets = await api.scrape_mention_markets(limit=100)
            if scraped_markets:
                # Filter out duplicates
                existing_titles = {m.get('title', '') for m in all_mention_markets}
                new_markets = [m for m in scraped_markets if m.get('title', '') not in existing_titles]
                all_mention_markets.extend(new_markets)
                console.print(f"[green]✅ Found {len(new_markets)} new markets via scraping[/green]")
            else:
                console.print("[yellow]⚠️ No markets found via scraping[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ Scraping method failed: {e}[/red]")
        
        # Method 3: Search for mention-related terms
        console.print("\n[blue]Method 3: Searching for mention-related terms...[/blue]")
        search_terms = ['mention', 'will mention', 'discuss', 'talk about', 'speak about']
        
        for term in search_terms:
            try:
                search_results = api.search_markets(term, limit=50)
                if search_results:
                    # Filter out duplicates
                    existing_titles = {m.get('title', '') for m in all_mention_markets}
                    new_markets = [m for m in search_results if m.get('title', '') not in existing_titles]
                    all_mention_markets.extend(new_markets)
                    console.print(f"[green]✅ Found {len(new_markets)} new markets for term '{term}'[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️ Search for '{term}' failed: {e}[/yellow]")
        
        return all_mention_markets
        
    except Exception as e:
        console.print(f"[red]❌ Error finding mention markets: {e}[/red]")
        return []

def display_mention_markets(markets):
    """Display mention markets in a nice table."""
    if not markets:
        console.print("[yellow]No mention markets found.[/yellow]")
        return
    
    console.print(f"\n[green]Found {len(markets)} mention markets:[/green]")
    
    table = Table(title="📢 Mention Markets")
    table.add_column("ID", style="cyan", width=15)
    table.add_column("Title", style="white", width=60)
    table.add_column("Yes Price", style="green", justify="right")
    table.add_column("No Price", style="red", justify="right")
    table.add_column("Source", style="blue")
    
    for market in markets:
        table.add_row(
            market.get('id', 'N/A')[:15],
            market.get('title', 'N/A')[:60],
            f"{market.get('yes_price', 0):.1f}%" if market.get('yes_price') else "N/A",
            f"{market.get('no_price', 0):.1f}%" if market.get('no_price') else "N/A",
            market.get('source', 'unknown')
        )
    
    console.print(table)

async def main():
    """Main function."""
    console.print("=" * 80)
    console.print("🎯 Kalshi Mention Markets Finder")
    console.print("=" * 80)
    
    # Find all mention markets
    mention_markets = await find_all_mention_markets()
    
    # Display results
    display_mention_markets(mention_markets)
    
    # Summary
    console.print(f"\n[blue]Summary:[/blue]")
    console.print(f"Total mention markets found: {len(mention_markets)}")
    
    if mention_markets:
        sources = {}
        for market in mention_markets:
            source = market.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        
        for source, count in sources.items():
            console.print(f"  - {source}: {count} markets")
    
    console.print("\n[green]✅ Search completed![/green]")

if __name__ == "__main__":
    asyncio.run(main())



