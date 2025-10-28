"""
Configuration management for the Kalshi research tool.
"""

import os
import yaml
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration class for the Kalshi research tool."""
    
    def __init__(self, config_dict: Dict[str, Any]):
        self.kalshi_api_key = config_dict.get('kalshi', {}).get('api_key') or os.getenv('KALSHI_API_KEY')
        self.kalshi_api_url = config_dict.get('kalshi', {}).get('api_url') or os.getenv('KALSHI_API_URL', 'https://api.elections.kalshi.com')
        
        self.openai_api_key = config_dict.get('openai', {}).get('api_key') or os.getenv('OPENAI_API_KEY')
        self.openai_model = config_dict.get('openai', {}).get('model') or os.getenv('AI_MODEL', 'gpt-4')
        self.openai_max_tokens = config_dict.get('openai', {}).get('max_tokens') or int(os.getenv('MAX_TOKENS', '2000'))
        self.openai_temperature = config_dict.get('openai', {}).get('temperature') or float(os.getenv('TEMPERATURE', '0.3'))
        
        self.database_url = config_dict.get('database', {}).get('url') or os.getenv('DATABASE_URL', 'sqlite:///kalshi_research.db')
        
        self.web_scraping = {
            'user_agent': config_dict.get('web_scraping', {}).get('user_agent') or os.getenv('USER_AGENT', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'),
            'request_delay': config_dict.get('web_scraping', {}).get('request_delay') or float(os.getenv('REQUEST_DELAY', '1.0')),
            'max_concurrent_requests': config_dict.get('web_scraping', {}).get('max_concurrent_requests') or int(os.getenv('MAX_CONCURRENT_REQUESTS', '5'))
        }
        
        self.twitter = {
            'api_key': config_dict.get('twitter', {}).get('api_key') or os.getenv('TWITTER_API_KEY'),
            'api_secret': config_dict.get('twitter', {}).get('api_secret') or os.getenv('TWITTER_API_SECRET'),
            'access_token': config_dict.get('twitter', {}).get('access_token') or os.getenv('TWITTER_ACCESS_TOKEN'),
            'access_token_secret': config_dict.get('twitter', {}).get('access_token_secret') or os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        }
        
        # API Ninjas configuration for earnings calls
        self.api_ninjas_key = config_dict.get('api_ninjas', {}).get('api_key') or os.getenv('API_NINJAS_KEY')

def load_config(config_file: str = 'config.yaml') -> Config:
    """Load configuration from YAML file and environment variables."""
    
    # Default configuration
    default_config = {
        'kalshi': {
            'api_key': None,
            'api_url': 'https://trading-api.kalshi.com/trade-api/v2'
        },
        'openai': {
            'api_key': None,
            'model': 'gpt-4',
            'max_tokens': 2000,
            'temperature': 0.3
        },
        'database': {
            'url': 'sqlite:///kalshi_research.db'
        },
        'web_scraping': {
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'request_delay': 1.0,
            'max_concurrent_requests': 5
        },
        'twitter': {
            'api_key': None,
            'api_secret': None,
            'access_token': None,
            'access_token_secret': None
        }
    }
    
    # Load from file if it exists
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            file_config = yaml.safe_load(f) or {}
            # Merge with defaults
            for key, value in file_config.items():
                if key in default_config and isinstance(value, dict):
                    default_config[key].update(value)
                else:
                    default_config[key] = value
    
    return Config(default_config)
