"""
Query and explore data in Supabase
"""
import sys
import os
import io
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dotenv import load_dotenv
from db_supabase import SupabaseNewsDatabase
import json

# Load environment variables
load_dotenv()


def print_news_item(news: dict, index: int = None):
    """Pretty print a news item"""
    if index:
        print(f"\n{'='*60}")
        print(f"NEWS ITEM #{index}")
        print('='*60)

    print(f"ID:        {news.get('id')}")
    print(f"Source:    {news.get('source')}")
    print(f"Title:     {news.get('title')}")
    print(f"Severity:  {news.get('severity', 'N/A')}")
    print(f"Area:      {news.get('area', 'N/A')}")
    print(f"Score:     {news.get('relevance_score', 'N/A')}")
    print(f"Published: {news.get('published_at')}")
    print(f"URL:       {news.get('url')}")

    if news.get('tags'):
        tags = news.get('tags')
        if isinstance(tags, str):
            tags = json.loads(tags)
        print(f"Tags:      {', '.join(tags)}")

    if news.get('summary'):
        print(f"\nSummary:")
        print(f"  {news.get('summary')}")


def main():
    """Main query interface"""
    print("="*60)
    print("SUPABASE DATA QUERY TOOL")
    print("="*60)

    try:
        db = SupabaseNewsDatabase()
        print("✓ Connected to Supabase\n")

        while True:
            print("\nOptions:")
            print("1. View recent news")
            print("2. View high severity news")
            print("3. View news by source")
            print("4. View news by severity")
            print("5. Search news")
            print("6. View statistics")
            print("7. View recent executions")
            print("8. Exit")

            choice = input("\nEnter choice (1-8): ").strip()

            if choice == '1':
                limit = input("How many items? (default: 10): ").strip()
                limit = int(limit) if limit else 10

                news_list = db.get_recent_news(limit=limit)
                print(f"\n{'='*60}")
                print(f"RECENT NEWS ({len(news_list)} items)")
                print('='*60)

                for i, news in enumerate(news_list, 1):
                    print_news_item(news, i)

            elif choice == '2':
                limit = input("How many items? (default: 20): ").strip()
                limit = int(limit) if limit else 20

                news_list = db.get_high_severity_news(limit=limit)
                print(f"\n{'='*60}")
                print(f"HIGH SEVERITY NEWS ({len(news_list)} items)")
                print('='*60)

                for i, news in enumerate(news_list, 1):
                    print_news_item(news, i)

            elif choice == '3':
                source = input("Enter source name: ").strip()
                limit = input("How many items? (default: 20): ").strip()
                limit = int(limit) if limit else 20

                news_list = db.get_news_by_source(source, limit=limit)
                print(f"\n{'='*60}")
                print(f"NEWS FROM '{source}' ({len(news_list)} items)")
                print('='*60)

                for i, news in enumerate(news_list, 1):
                    print_news_item(news, i)

            elif choice == '4':
                severity = input("Enter severity (low/medium/high/critical): ").strip()
                limit = input("How many items? (default: 20): ").strip()
                limit = int(limit) if limit else 20

                news_list = db.get_news_by_severity(severity, limit=limit)
                print(f"\n{'='*60}")
                print(f"NEWS WITH SEVERITY '{severity}' ({len(news_list)} items)")
                print('='*60)

                for i, news in enumerate(news_list, 1):
                    print_news_item(news, i)

            elif choice == '5':
                query = input("Enter search query: ").strip()
                limit = input("How many items? (default: 20): ").strip()
                limit = int(limit) if limit else 20

                news_list = db.search_news(query, limit=limit)
                print(f"\n{'='*60}")
                print(f"SEARCH RESULTS for '{query}' ({len(news_list)} items)")
                print('='*60)

                for i, news in enumerate(news_list, 1):
                    print_news_item(news, i)

            elif choice == '6':
                stats = db.get_stats()
                print(f"\n{'='*60}")
                print("DATABASE STATISTICS")
                print('='*60)
                print(f"\nTotal News:        {stats.get('total_news', 0)}")

                print(f"\nBy Severity:")
                for severity, count in stats.get('by_severity', {}).items():
                    print(f"  {severity:12s} {count}")

                print(f"\nBy Source:")
                for source, count in stats.get('by_source', {}).items():
                    print(f"  {source:30s} {count}")

                print(f"\nRecent Executions: {stats.get('recent_executions', 0)}")

            elif choice == '7':
                limit = input("How many executions? (default: 5): ").strip()
                limit = int(limit) if limit else 5

                executions = db.get_recent_executions(limit=limit)
                print(f"\n{'='*60}")
                print(f"RECENT EXECUTIONS ({len(executions)} items)")
                print('='*60)

                for i, exec_log in enumerate(executions, 1):
                    print(f"\n[{i}] Execution at {exec_log.get('execution_time')}")
                    print(f"    Extracted:      {exec_log.get('news_extracted', 0)}")
                    print(f"    Deduplicated:   {exec_log.get('news_deduplicated', 0)}")
                    print(f"    Scored:         {exec_log.get('news_scored', 0)}")
                    print(f"    Kept:           {exec_log.get('news_kept', 0)}")
                    print(f"    Discarded:      {exec_log.get('news_discarded', 0)}")
                    print(f"    Duration:       {exec_log.get('duration_seconds', 0):.2f}s")

            elif choice == '8':
                print("\nGoodbye!")
                break

            else:
                print("Invalid choice. Please enter 1-8.")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nMake sure:")
        print("1. SUPABASE_URL and SUPABASE_KEY are set in .env")
        print("2. The SQL schema is created in Supabase")
        print("3. You have internet connection")
        sys.exit(1)


if __name__ == "__main__":
    main()
