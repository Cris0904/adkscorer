"""
Database module for ETL Movilidad Medellín - SQLite implementation
Handles news storage, deduplication, and queries
"""
import sqlite3
import hashlib
import json
from datetime import datetime
from typing import Optional, List, Dict
from pathlib import Path


class NewsDatabase:
    """SQLite database manager for news items"""

    def __init__(self, db_path: str = "data/etl_movilidad.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_database()

    def init_database(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Main news table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_item (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                url TEXT NOT NULL,
                hash_url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                published_at TEXT NOT NULL,

                -- ADK enrichment fields
                severity TEXT CHECK(severity IN ('low', 'medium', 'high', 'critical')),
                tags TEXT,  -- JSON array as string
                area TEXT,
                entities TEXT,  -- JSON array as string
                summary TEXT,
                relevance_score REAL,

                -- Status and metadata
                status TEXT DEFAULT 'active',
                alerted INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Execution log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS execution_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_time TEXT NOT NULL,
                news_extracted INTEGER DEFAULT 0,
                news_deduplicated INTEGER DEFAULT 0,
                news_scored INTEGER DEFAULT 0,
                news_kept INTEGER DEFAULT 0,
                news_discarded INTEGER DEFAULT 0,
                errors TEXT,
                duration_seconds REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hash_url ON news_item(hash_url)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_published_at ON news_item(published_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_severity ON news_item(severity)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON news_item(source)')

        conn.commit()
        conn.close()

    def compute_hash(self, url: str) -> str:
        """Compute SHA256 hash for URL deduplication"""
        return hashlib.sha256(url.encode('utf-8')).hexdigest()

    def is_duplicate(self, url: str) -> bool:
        """Check if URL already exists in database"""
        hash_url = self.compute_hash(url)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM news_item WHERE hash_url = ?', (hash_url,))
        result = cursor.fetchone()
        conn.close()

        return result is not None

    def insert_news(self, news_item: Dict) -> Optional[int]:
        """Insert news item into database"""
        hash_url = self.compute_hash(news_item['url'])

        # Check for duplicates
        if self.is_duplicate(news_item['url']):
            return None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO news_item (
                    source, url, hash_url, title, body, published_at,
                    severity, tags, area, entities, summary, relevance_score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                news_item['source'],
                news_item['url'],
                hash_url,
                news_item['title'],
                news_item['body'],
                news_item['published_at'],
                news_item.get('severity'),
                json.dumps(news_item.get('tags', [])),
                news_item.get('area'),
                json.dumps(news_item.get('entities', [])),
                news_item.get('summary'),
                news_item.get('relevance_score')
            ))

            conn.commit()
            news_id = cursor.lastrowid
            conn.close()
            return news_id
        except sqlite3.IntegrityError:
            conn.close()
            return None

    def mark_as_alerted(self, news_id: int):
        """Mark news item as alerted"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE news_item SET alerted = 1 WHERE id = ?', (news_id,))
        conn.commit()
        conn.close()

    def get_recent_news(self, limit: int = 50) -> List[Dict]:
        """Get recent news items"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM news_item
            ORDER BY published_at DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_high_severity_news(self, limit: int = 20) -> List[Dict]:
        """Get high and critical severity news"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM news_item
            WHERE severity IN ('high', 'critical')
            ORDER BY published_at DESC
            LIMIT ?
        ''', (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def log_execution(self, stats: Dict):
        """Log pipeline execution statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO execution_log (
                execution_time, news_extracted, news_deduplicated,
                news_scored, news_kept, news_discarded,
                errors, duration_seconds
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            stats.get('extracted', 0),
            stats.get('deduplicated', 0),
            stats.get('scored', 0),
            stats.get('kept', 0),
            stats.get('discarded', 0),
            json.dumps(stats.get('errors', [])),
            stats.get('duration', 0)
        ))

        conn.commit()
        conn.close()

    def get_stats(self) -> Dict:
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total news
        cursor.execute('SELECT COUNT(*) FROM news_item')
        total = cursor.fetchone()[0]

        # By severity
        cursor.execute('''
            SELECT severity, COUNT(*) as count
            FROM news_item
            GROUP BY severity
        ''')
        by_severity = {row[0] or 'unknown': row[1] for row in cursor.fetchall()}

        # By source
        cursor.execute('''
            SELECT source, COUNT(*) as count
            FROM news_item
            GROUP BY source
        ''')
        by_source = {row[0]: row[1] for row in cursor.fetchall()}

        # Recent executions
        cursor.execute('''
            SELECT * FROM execution_log
            ORDER BY created_at DESC
            LIMIT 5
        ''')
        recent_executions = cursor.fetchall()

        conn.close()

        return {
            'total_news': total,
            'by_severity': by_severity,
            'by_source': by_source,
            'recent_executions': len(recent_executions)
        }
