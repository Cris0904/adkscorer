"""
Database statistics viewer
Shows comprehensive stats from the ETL database
"""
import sys
import os
import json
import io

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from db import NewsDatabase


def main():
    db = NewsDatabase()

    print("="*60)
    print("DATABASE STATISTICS")
    print("="*60)

    stats = db.get_stats()

    # Total news
    print(f"\n📊 Total News Items: {stats['total_news']}")

    # By severity
    print("\n📈 By Severity:")
    for severity, count in stats['by_severity'].items():
        percentage = (count / stats['total_news'] * 100) if stats['total_news'] > 0 else 0
        print(f"  {severity:10s}: {count:4d} ({percentage:5.1f}%)")

    # By source
    print("\n📰 By Source:")
    for source, count in stats['by_source'].items():
        percentage = (count / stats['total_news'] * 100) if stats['total_news'] > 0 else 0
        print(f"  {source:30s}: {count:4d} ({percentage:5.1f}%)")

    # Recent executions
    print(f"\n🔄 Recent Executions: {stats['recent_executions']}")

    # Recent news
    print("\n📋 Recent News (last 10):")
    recent = db.get_recent_news(limit=10)

    if recent:
        for i, news in enumerate(recent, 1):
            print(f"\n  {i}. [{news.get('severity', 'N/A').upper()}] {news.get('title', 'N/A')[:60]}")
            print(f"     Source: {news.get('source', 'N/A')}")
            print(f"     Area: {news.get('area', 'N/A')}")
            print(f"     Published: {news.get('published_at', 'N/A')[:19]}")
            if news.get('tags'):
                try:
                    tags = json.loads(news['tags']) if isinstance(news['tags'], str) else news['tags']
                    print(f"     Tags: {', '.join(tags[:5])}")
                except:
                    pass
    else:
        print("  No news in database yet")

    # High severity news
    print("\n⚠️  High Severity News (last 5):")
    high_severity = db.get_high_severity_news(limit=5)

    if high_severity:
        for i, news in enumerate(high_severity, 1):
            print(f"\n  {i}. [{news.get('severity', 'N/A').upper()}] {news.get('title', 'N/A')[:60]}")
            print(f"     Area: {news.get('area', 'N/A')}")
            print(f"     Summary: {news.get('summary', 'N/A')[:100]}")
    else:
        print("  No high severity news")

    print("\n" + "="*60)


if __name__ == "__main__":
    main()
