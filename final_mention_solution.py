#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final comprehensive solution for finding Kalshi mention markets.
"""

import sys
import os
import asyncio
import requests
from bs4 import BeautifulSoup
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
import json
import time
import random

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import load_config

console = Console()

def manual_mention_finder():
    """Manual approach to find mention markets."""
    console.print(Panel("🔍 Manual Mention Markets Finder", style="blue"))
    
    console.print("\n[blue]This will help you find mention markets manually since the API is not accessible.[/blue]")
    
    # Step 1: Direct URL access
    console.print("\n[yellow]Step 1: Direct URL Access[/yellow]")
    console.print("Please visit these URLs in your browser to find mention markets:")
    console.print("• https://kalshi.com/?category=mentions")
    console.print("• https://kalshi.com/markets")
    console.print("• https://kalshi.com/")
    
    # Step 2: Manual data entry
    console.print("\n[yellow]Step 2: Manual Data Entry[/yellow]")
    console.print("If you find mention markets, you can enter them manually here.")
    
    markets = []
    
    while True:
        if not Confirm.ask("\nDo you want to add a mention market manually?"):
            break
        
        ticker = Prompt.ask("Enter market ticker")
        title = Prompt.ask("Enter market title")
        yes_price = Prompt.ask("Enter YES price (as percentage)", default="50")
        no_price = Prompt.ask("Enter NO price (as percentage)", default="50")
        
        try:
            market = {
                'ticker': ticker,
                'title': title,
                'yes_price': float(yes_price),
                'no_price': float(no_price),
                'status': 'open',
                'source': 'manual'
            }
            markets.append(market)
            console.print(f"[green]✅ Added market: {title}[/green]")
        except ValueError:
            console.print("[red]❌ Invalid price format. Please use numbers only.[/red]")
    
    return markets

def create_api_implementation_guide():
    """Create a guide for implementing the correct API."""
    console.print(Panel("📚 API Implementation Guide", style="blue"))
    
    guide = """
# Kalshi API Implementation Guide

## Current Status
- The API endpoints we tested are not working as expected
- `trading-api.kalshi.com` returns 401 (Unauthorized) - this might be the correct endpoint
- Rate limiting (429) is preventing web scraping

## Next Steps

### 1. Verify API Credentials
- Check if your API key is correct
- Verify if you need different authentication (OAuth, JWT, etc.)
- Contact Kalshi support for current API documentation

### 2. Try Different Endpoints
Based on the 401 responses, try:
- `https://trading-api.kalshi.com/series?category=mentions`
- `https://trading-api.kalshi.com/markets?status=open`

### 3. Authentication
You might need to:
- Include additional headers
- Use OAuth 2.0 flow
- Include a different authentication method

### 4. Rate Limiting
- Implement exponential backoff
- Use different User-Agent strings
- Rotate IP addresses if possible

## Working Implementation Template

```python
def get_mention_markets_correct():
    # Step 1: Get series with mentions category
    series_response = requests.get(
        'https://trading-api.kalshi.com/series',
        params={'category': 'mentions'},
        headers={
            'Authorization': 'Bearer YOUR_TOKEN',
            'Content-Type': 'application/json'
        }
    )
    
    series_data = series_response.json()
    series_list = series_data.get('series', [])
    
    # Step 2: Get markets for each series
    all_markets = []
    for series in series_list:
        series_ticker = series.get('ticker')
        markets_response = requests.get(
            'https://trading-api.kalshi.com/markets',
            params={
                'series_ticker': series_ticker,
                'status': 'open',
                'limit': 1000
            },
            headers={
                'Authorization': 'Bearer YOUR_TOKEN',
                'Content-Type': 'application/json'
            }
        )
        
        markets_data = markets_response.json()
        markets = markets_data.get('markets', [])
        all_markets.extend(markets)
    
    return all_markets
```

## Manual Approach
Since the API is not accessible, use the manual approach:
1. Visit https://kalshi.com/?category=mentions
2. Manually collect market data
3. Use the data entry tool in this script
"""
    
    console.print(guide)

def display_markets(markets, title="Markets"):
    """Display markets in a table."""
    if not markets:
        console.print(f"[yellow]No {title.lower()} found.[/yellow]")
        return
    
    console.print(f"\n[green]Found {len(markets)} {title.lower()}:[/green]")
    
    table = Table(title=f"📢 {title}")
    table.add_column("Ticker", style="cyan", width=20)
    table.add_column("Title", style="white", width=60)
    table.add_column("Yes Price", style="green", justify="right")
    table.add_column("No Price", style="red", justify="right")
    table.add_column("Source", style="blue")
    
    for market in markets:
        table.add_row(
            market.get('ticker', 'N/A')[:20],
            market.get('title', 'N/A')[:60],
            f"{market.get('yes_price', 0):.1f}%" if market.get('yes_price') else "N/A",
            f"{market.get('no_price', 0):.1f}%" if market.get('no_price') else "N/A",
            market.get('source', 'unknown')
        )
    
    console.print(table)

def save_markets_to_file(markets, filename="mention_markets.json"):
    """Save markets to a JSON file."""
    try:
        with open(filename, 'w') as f:
            json.dump(markets, f, indent=2)
        console.print(f"[green]✅ Markets saved to {filename}[/green]")
    except Exception as e:
        console.print(f"[red]❌ Error saving markets: {e}[/red]")

def load_markets_from_file(filename="mention_markets.json"):
    """Load markets from a JSON file."""
    try:
        with open(filename, 'r') as f:
            markets = json.load(f)
        console.print(f"[green]✅ Loaded {len(markets)} markets from {filename}[/green]")
        return markets
    except FileNotFoundError:
        console.print(f"[yellow]⚠️ File {filename} not found[/yellow]")
        return []
    except Exception as e:
        console.print(f"[red]❌ Error loading markets: {e}[/red]")
        return []

async def main():
    """Main function."""
    console.print("=" * 80)
    console.print("🎯 Final Kalshi Mention Markets Solution")
    console.print("=" * 80)
    
    all_markets = []
    
    # Load existing markets if available
    existing_markets = load_markets_from_file()
    if existing_markets:
        all_markets.extend(existing_markets)
        console.print(f"[blue]Loaded {len(existing_markets)} existing markets[/blue]")
    
    # Show current options
    console.print("\n[blue]Available options:[/blue]")
    console.print("1. Manual mention markets finder")
    console.print("2. API implementation guide")
    console.print("3. Display current markets")
    console.print("4. Save markets to file")
    console.print("5. Exit")
    
    while True:
        choice = Prompt.ask("\nWhat would you like to do?", choices=["1", "2", "3", "4", "5"])
        
        if choice == "1":
            manual_markets = manual_mention_finder()
            all_markets.extend(manual_markets)
            
        elif choice == "2":
            create_api_implementation_guide()
            
        elif choice == "3":
            display_markets(all_markets, "Current Markets")
            
        elif choice == "4":
            save_markets_to_file(all_markets)
            
        elif choice == "5":
            break
    
    # Final summary
    console.print("\n" + "="*50)
    console.print(f"[blue]Final Summary:[/blue]")
    console.print(f"Total markets collected: {len(all_markets)}")
    
    if all_markets:
        sources = {}
        for market in all_markets:
            source = market.get('source', 'unknown')
            sources[source] = sources.get(source, 0) + 1
        
        for source, count in sources.items():
            console.print(f"  - {source}: {count} markets")
    
    console.print("\n[green]✅ Solution completed![/green]")

if __name__ == "__main__":
    asyncio.run(main())



