"""
Caching system for the Kalshi research tool.
"""

import json
import pickle
import hashlib
import os
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List
from pathlib import Path
import sqlite3
from rich.console import Console

console = Console()

class CacheManager:
    """Manages caching for API responses and analysis results."""
    
    def __init__(self, cache_dir: str = "cache", max_age_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_age = timedelta(hours=max_age_hours)
        
        # Initialize cache database
        self.cache_db_path = self.cache_dir / "cache.db"
        self._init_cache_db()
    
    def _init_cache_db(self):
        """Initialize the cache database."""
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_entries (
                key TEXT PRIMARY KEY,
                data_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP NOT NULL,
                file_path TEXT,
                metadata TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _generate_key(self, data_type: str, identifier: str, **kwargs) -> str:
        """Generate a cache key for the given data."""
        key_data = {
            'type': data_type,
            'id': identifier,
            **kwargs
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _is_expired(self, expires_at: str) -> bool:
        """Check if a cache entry is expired."""
        try:
            expires = datetime.fromisoformat(expires_at)
            return datetime.now() > expires
        except ValueError:
            return True
    
    def get(self, data_type: str, identifier: str, **kwargs) -> Optional[Any]:
        """Get cached data."""
        key = self._generate_key(data_type, identifier, **kwargs)
        
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT file_path, expires_at, metadata FROM cache_entries 
            WHERE key = ? AND data_type = ?
        """, (key, data_type))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return None
        
        file_path, expires_at, metadata = result
        
        if self._is_expired(expires_at):
            self.delete(data_type, identifier, **kwargs)
            return None
        
        try:
            with open(file_path, 'rb') as f:
                data = pickle.load(f)
            
            # Add metadata
            if metadata:
                data['_cache_metadata'] = json.loads(metadata)
            
            return data
        except (FileNotFoundError, pickle.PickleError, json.JSONDecodeError):
            # File doesn't exist or is corrupted, remove from database
            self.delete(data_type, identifier, **kwargs)
            return None
    
    def set(self, data_type: str, identifier: str, data: Any, ttl_hours: int = None, **kwargs) -> bool:
        """Cache data."""
        if ttl_hours is None:
            ttl_hours = self.max_age.total_seconds() / 3600
        
        key = self._generate_key(data_type, identifier, **kwargs)
        expires_at = datetime.now() + timedelta(hours=ttl_hours)
        
        # Create filename based on key
        filename = f"{key}.pkl"
        file_path = self.cache_dir / filename
        
        try:
            # Save data to file
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
            
            # Update database
            conn = sqlite3.connect(self.cache_db_path)
            cursor = conn.cursor()
            
            # Remove old entry if exists
            cursor.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
            
            # Insert new entry
            cursor.execute("""
                INSERT INTO cache_entries (key, data_type, expires_at, file_path, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (key, data_type, expires_at.isoformat(), str(file_path), json.dumps(kwargs)))
            
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            console.print(f"[yellow]Cache error: {e}[/yellow]")
            return False
    
    def delete(self, data_type: str, identifier: str, **kwargs) -> bool:
        """Delete cached data."""
        key = self._generate_key(data_type, identifier, **kwargs)
        
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        # Get file path
        cursor.execute("SELECT file_path FROM cache_entries WHERE key = ?", (key,))
        result = cursor.fetchone()
        
        if result:
            file_path = result[0]
            # Remove from database
            cursor.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
            conn.commit()
            
            # Remove file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except OSError:
                pass
        
        conn.close()
        return True
    
    def clear_expired(self) -> int:
        """Clear expired cache entries."""
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        # Find expired entries
        cursor.execute("""
            SELECT key, file_path FROM cache_entries 
            WHERE expires_at < ?
        """, (datetime.now().isoformat(),))
        
        expired_entries = cursor.fetchall()
        removed_count = 0
        
        for key, file_path in expired_entries:
            # Remove from database
            cursor.execute("DELETE FROM cache_entries WHERE key = ?", (key,))
            
            # Remove file
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                removed_count += 1
            except OSError:
                pass
        
        conn.commit()
        conn.close()
        
        if removed_count > 0:
            console.print(f"[green]Cleared {removed_count} expired cache entries[/green]")
        
        return removed_count
    
    def clear_all(self) -> int:
        """Clear all cache entries."""
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        # Get all file paths
        cursor.execute("SELECT file_path FROM cache_entries")
        file_paths = [row[0] for row in cursor.fetchall()]
        
        # Clear database
        cursor.execute("DELETE FROM cache_entries")
        conn.commit()
        conn.close()
        
        # Remove all files
        removed_count = 0
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                removed_count += 1
            except OSError:
                pass
        
        console.print(f"[green]Cleared all {removed_count} cache entries[/green]")
        return removed_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        conn = sqlite3.connect(self.cache_db_path)
        cursor = conn.cursor()
        
        # Total entries
        cursor.execute("SELECT COUNT(*) FROM cache_entries")
        total_entries = cursor.fetchone()[0]
        
        # Expired entries
        cursor.execute("""
            SELECT COUNT(*) FROM cache_entries 
            WHERE expires_at < ?
        """, (datetime.now().isoformat(),))
        expired_entries = cursor.fetchone()[0]
        
        # Entries by type
        cursor.execute("""
            SELECT data_type, COUNT(*) FROM cache_entries 
            GROUP BY data_type
        """)
        entries_by_type = dict(cursor.fetchall())
        
        # Cache size
        cache_size = 0
        for file_path in self.cache_dir.glob("*.pkl"):
            try:
                cache_size += file_path.stat().st_size
            except OSError:
                pass
        
        conn.close()
        
        return {
            'total_entries': total_entries,
            'expired_entries': expired_entries,
            'active_entries': total_entries - expired_entries,
            'entries_by_type': entries_by_type,
            'cache_size_mb': cache_size / (1024 * 1024),
            'cache_dir': str(self.cache_dir)
        }

class DataStore:
    """Enhanced data storage with caching."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
    
    def store_market_data(self, market: Dict[str, Any], ttl_hours: int = 6) -> bool:
        """Store market data with caching."""
        market_id = market.get('id')
        if not market_id:
            return False
        
        return self.cache.set('market', market_id, market, ttl_hours)
    
    def get_market_data(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Get cached market data."""
        return self.cache.get('market', market_id)
    
    def store_research_data(self, market_id: str, research_data: Dict[str, Any], ttl_hours: int = 12) -> bool:
        """Store research data with caching."""
        return self.cache.set('research', market_id, research_data, ttl_hours)
    
    def get_research_data(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Get cached research data."""
        return self.cache.get('research', market_id)
    
    def store_ai_analysis(self, market_id: str, analysis: Dict[str, Any], ttl_hours: int = 24) -> bool:
        """Store AI analysis with caching."""
        return self.cache.set('ai_analysis', market_id, analysis, ttl_hours)
    
    def get_ai_analysis(self, market_id: str) -> Optional[Dict[str, Any]]:
        """Get cached AI analysis."""
        return self.cache.get('ai_analysis', market_id)
    
    def store_news_data(self, query: str, news_data: List[Dict[str, Any]], ttl_hours: int = 2) -> bool:
        """Store news data with caching."""
        return self.cache.set('news', query, news_data, ttl_hours)
    
    def get_news_data(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached news data."""
        return self.cache.get('news', query)
    
    def store_transcript_data(self, query: str, transcript_data: List[Dict[str, Any]], ttl_hours: int = 6) -> bool:
        """Store transcript data with caching."""
        return self.cache.set('transcripts', query, transcript_data, ttl_hours)
    
    def get_transcript_data(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached transcript data."""
        return self.cache.get('transcripts', query)
    
    def store_social_data(self, query: str, social_data: List[Dict[str, Any]], ttl_hours: int = 1) -> bool:
        """Store social media data with caching."""
        return self.cache.set('social', query, social_data, ttl_hours)
    
    def get_social_data(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached social media data."""
        return self.cache.get('social', query)



