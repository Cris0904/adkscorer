"""
Database module for ETL Movilidad Medellín - Supabase implementation
Handles news storage, deduplication, and queries using Supabase PostgreSQL
"""
import hashlib
import os
from datetime import datetime
from typing import Optional, List, Dict
from dotenv import load_dotenv

try:
    from supabase import create_client, Client
except ImportError:
    raise ImportError(
        "supabase package not found. Install it with: pip install supabase"
    )

load_dotenv()


class SupabaseNewsDatabase:
    """Supabase database manager for news items"""

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None
    ):
        """
        Initialize Supabase connection

        Args:
            supabase_url: Supabase project URL (defaults to SUPABASE_URL env var)
            supabase_key: Supabase API key (defaults to SUPABASE_KEY env var)
        """
        self.url = supabase_url or os.getenv("SUPABASE_URL")
        self.key = supabase_key or os.getenv("SUPABASE_KEY")

        if not self.url or not self.key:
            raise ValueError(
                "Supabase credentials required. Set SUPABASE_URL and SUPABASE_KEY "
                "environment variables or pass them as parameters."
            )

        # Create Supabase client
        self.client: Client = create_client(self.url, self.key)

    def compute_hash(self, url: str) -> str:
        """Compute SHA256 hash for URL deduplication"""
        return hashlib.sha256(url.encode('utf-8')).hexdigest()

    def is_duplicate(self, url: str) -> bool:
        """Check if URL already exists in database"""
        hash_url = self.compute_hash(url)

        try:
            response = self.client.table('news_item').select('id').eq(
                'hash_url', hash_url
            ).limit(1).execute()

            return len(response.data) > 0
        except Exception as e:
            print(f"Error checking duplicate: {e}")
            return False

    def insert_news(self, news_item: Dict) -> Optional[int]:
        """
        Insert news item into database

        Args:
            news_item: Dictionary with news data

        Returns:
            Inserted item ID or None if duplicate/error
        """
        hash_url = self.compute_hash(news_item['url'])

        # Check for duplicates
        if self.is_duplicate(news_item['url']):
            return None

        try:
            # Prepare data for insertion
            data = {
                'source': news_item['source'],
                'url': news_item['url'],
                'hash_url': hash_url,
                'title': news_item['title'],
                'body': news_item['body'],
                'published_at': news_item['published_at'],
                'severity': news_item.get('severity'),
                'tags': news_item.get('tags', []),
                'area': news_item.get('area'),
                'entities': news_item.get('entities', []),
                'summary': news_item.get('summary'),
                'relevance_score': news_item.get('relevance_score')
            }

            # Insert into Supabase
            response = self.client.table('news_item').insert(data).execute()

            if response.data and len(response.data) > 0:
                return response.data[0]['id']
            return None

        except Exception as e:
            print(f"Error inserting news: {e}")
            return None

    def mark_as_alerted(self, news_id: int):
        """Mark news item as alerted"""
        try:
            self.client.table('news_item').update(
                {'alerted': True}
            ).eq('id', news_id).execute()
        except Exception as e:
            print(f"Error marking as alerted: {e}")

    def get_recent_news(self, limit: int = 50) -> List[Dict]:
        """
        Get recent news items

        Args:
            limit: Maximum number of items to return

        Returns:
            List of news dictionaries
        """
        try:
            response = self.client.table('news_item').select(
                '*'
            ).order('published_at', desc=True).limit(limit).execute()

            return response.data if response.data else []
        except Exception as e:
            print(f"Error getting recent news: {e}")
            return []

    def get_high_severity_news(self, limit: int = 20) -> List[Dict]:
        """
        Get high and critical severity news

        Args:
            limit: Maximum number of items to return

        Returns:
            List of news dictionaries
        """
        try:
            response = self.client.table('news_item').select(
                '*'
            ).in_('severity', ['high', 'critical']).order(
                'published_at', desc=True
            ).limit(limit).execute()

            return response.data if response.data else []
        except Exception as e:
            print(f"Error getting high severity news: {e}")
            return []

    def get_news_by_source(self, source: str, limit: int = 50) -> List[Dict]:
        """
        Get news items by source

        Args:
            source: Source name
            limit: Maximum number of items

        Returns:
            List of news dictionaries
        """
        try:
            response = self.client.table('news_item').select(
                '*'
            ).eq('source', source).order(
                'published_at', desc=True
            ).limit(limit).execute()

            return response.data if response.data else []
        except Exception as e:
            print(f"Error getting news by source: {e}")
            return []

    def get_news_by_severity(self, severity: str, limit: int = 50) -> List[Dict]:
        """
        Get news items by severity level

        Args:
            severity: Severity level (low, medium, high, critical)
            limit: Maximum number of items

        Returns:
            List of news dictionaries
        """
        try:
            response = self.client.table('news_item').select(
                '*'
            ).eq('severity', severity).order(
                'published_at', desc=True
            ).limit(limit).execute()

            return response.data if response.data else []
        except Exception as e:
            print(f"Error getting news by severity: {e}")
            return []

    def search_news(
        self,
        query: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search news items by text query (searches in title and body)

        Args:
            query: Search query
            limit: Maximum number of items

        Returns:
            List of news dictionaries
        """
        try:
            # Use ilike for case-insensitive search
            response = self.client.table('news_item').select(
                '*'
            ).or_(
                f'title.ilike.%{query}%,body.ilike.%{query}%'
            ).order('published_at', desc=True).limit(limit).execute()

            return response.data if response.data else []
        except Exception as e:
            print(f"Error searching news: {e}")
            return []

    def log_execution(self, stats: Dict):
        """
        Log pipeline execution statistics

        Args:
            stats: Dictionary with execution statistics
        """
        try:
            data = {
                'execution_time': datetime.now().isoformat(),
                'news_extracted': stats.get('extracted', 0),
                'news_deduplicated': stats.get('deduplicated', 0),
                'news_scored': stats.get('scored', 0),
                'news_kept': stats.get('kept', 0),
                'news_discarded': stats.get('discarded', 0),
                'errors': stats.get('errors', []),
                'duration_seconds': stats.get('duration', 0)
            }

            self.client.table('execution_log').insert(data).execute()
        except Exception as e:
            print(f"Error logging execution: {e}")

    def get_stats(self) -> Dict:
        """
        Get database statistics

        Returns:
            Dictionary with statistics
        """
        try:
            # Use the stored function created in the schema
            response = self.client.rpc('get_news_stats').execute()

            if response.data:
                return response.data
            else:
                # Fallback to manual queries if function doesn't exist
                return self._get_stats_manual()

        except Exception as e:
            print(f"Error getting stats (trying manual method): {e}")
            return self._get_stats_manual()

    def _get_stats_manual(self) -> Dict:
        """Get statistics manually if stored function doesn't work"""
        try:
            # Total news
            total_response = self.client.table('news_item').select(
                'id', count='exact'
            ).execute()
            total = total_response.count if hasattr(total_response, 'count') else 0

            # By severity - we'll fetch all and count manually
            severity_response = self.client.table('news_item').select(
                'severity'
            ).execute()
            by_severity = {}
            for item in severity_response.data:
                sev = item.get('severity') or 'unknown'
                by_severity[sev] = by_severity.get(sev, 0) + 1

            # By source
            source_response = self.client.table('news_item').select(
                'source'
            ).execute()
            by_source = {}
            for item in source_response.data:
                src = item.get('source')
                by_source[src] = by_source.get(src, 0) + 1

            # Recent executions
            exec_response = self.client.table('execution_log').select(
                'id', count='exact'
            ).limit(5).order('created_at', desc=True).execute()
            recent_executions = exec_response.count if hasattr(
                exec_response, 'count'
            ) else 0

            return {
                'total_news': total,
                'by_severity': by_severity,
                'by_source': by_source,
                'recent_executions': recent_executions
            }
        except Exception as e:
            print(f"Error getting manual stats: {e}")
            return {
                'total_news': 0,
                'by_severity': {},
                'by_source': {},
                'recent_executions': 0
            }

    def get_recent_executions(self, limit: int = 10) -> List[Dict]:
        """
        Get recent pipeline executions

        Args:
            limit: Maximum number of executions

        Returns:
            List of execution log dictionaries
        """
        try:
            response = self.client.table('execution_log').select(
                '*'
            ).order('created_at', desc=True).limit(limit).execute()

            return response.data if response.data else []
        except Exception as e:
            print(f"Error getting recent executions: {e}")
            return []


# Backward compatibility alias
NewsDatabase = SupabaseNewsDatabase
