#!/usr/bin/env python3
"""
Kalshi Mention Market Research Tool
A comprehensive terminal-based research tool for Kalshi mention markets.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.cli import cli
from src.config import load_config
from src.database import init_database

console = Console()

@click.command()
@click.option('--config', '-c', default='config.yaml', help='Configuration file path')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
def main(config, verbose):
    """Kalshi Mention Market Research Tool"""
    
    # Display welcome banner
    welcome_text = Text("Kalshi Mention Market Research Tool", style="bold blue")
    console.print(Panel(welcome_text, title="Welcome", border_style="blue"))
    
    # Load configuration
    try:
        cfg = load_config(config)
        console.print(f"[green]✓[/green] Configuration loaded from {config}")
    except Exception as e:
        console.print(f"[red]✗[/red] Failed to load configuration: {e}")
        return
    
    # Initialize database
    try:
        init_database()
        console.print("[green]✓[/green] Database initialized")
    except Exception as e:
        console.print(f"[red]✗[/red] Database initialization failed: {e}")
        return
    
    # Start the CLI
    cli()

if __name__ == "__main__":
    main()



