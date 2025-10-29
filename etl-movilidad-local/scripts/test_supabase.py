"""
Test Supabase connection and basic operations
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

# Load environment variables
load_dotenv()

def test_connection():
    """Test basic Supabase connection"""
    print("="*60)
    print("TESTING SUPABASE CONNECTION")
    print("="*60)

    try:
        # Initialize database
        print("\n1. Initializing Supabase connection...")
        db = SupabaseNewsDatabase()
        print("   ✓ Connection established")

        # Test duplicate check (should work even with empty DB)
        print("\n2. Testing duplicate check...")
        is_dup = db.is_duplicate("https://test.com/news/1")
        print(f"   ✓ Duplicate check works: {is_dup}")

        # Test stats
        print("\n3. Getting database stats...")
        stats = db.get_stats()
        print(f"   ✓ Stats retrieved:")
        print(f"      - Total news: {stats.get('total_news', 0)}")
        print(f"      - By severity: {stats.get('by_severity', {})}")
        print(f"      - By source: {stats.get('by_source', {})}")

        # Test insert (if not duplicate)
        print("\n4. Testing news insertion...")
        test_news = {
            'source': 'Test Source',
            'url': 'https://test.com/news/test-' + str(os.getpid()),
            'title': 'Test News Item',
            'body': 'This is a test news item to verify Supabase is working correctly.',
            'published_at': '2025-10-29T12:00:00Z',
            'severity': 'low',
            'tags': ['test', 'demo'],
            'area': 'Test Area',
            'entities': ['Test Entity'],
            'summary': 'Test summary',
            'relevance_score': 0.75
        }

        news_id = db.insert_news(test_news)
        if news_id:
            print(f"   ✓ News inserted with ID: {news_id}")

            # Test retrieval
            print("\n5. Testing news retrieval...")
            recent = db.get_recent_news(limit=5)
            print(f"   ✓ Retrieved {len(recent)} recent news items")

            if recent:
                print(f"\n   Sample news:")
                print(f"      ID: {recent[0].get('id')}")
                print(f"      Title: {recent[0].get('title')}")
                print(f"      Source: {recent[0].get('source')}")
                print(f"      Severity: {recent[0].get('severity')}")
        else:
            print("   ⚠ News was a duplicate or insertion failed")

        # Test execution logging
        print("\n6. Testing execution logging...")
        test_stats = {
            'extracted': 10,
            'deduplicated': 2,
            'scored': 8,
            'kept': 6,
            'discarded': 2,
            'errors': [],
            'duration': 15.5
        }
        db.log_execution(test_stats)
        print("   ✓ Execution logged successfully")

        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)
        print("\nSupabase is configured correctly and ready to use!")
        print("\nNext steps:")
        print("1. Run the ETL pipeline: python src/main.py")
        print("2. View data in Supabase dashboard")
        print("3. Query via API or Python client")

    except ImportError as e:
        print(f"\n❌ ERROR: Missing dependency")
        print(f"   {e}")
        print("\n   Install with: pip install supabase")
        sys.exit(1)

    except ValueError as e:
        print(f"\n❌ ERROR: Configuration issue")
        print(f"   {e}")
        print("\n   Make sure SUPABASE_URL and SUPABASE_KEY are set in .env")
        print("   Get them from: https://app.supabase.com/project/_/settings/api")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nTroubleshooting:")
        print("1. Check your .env file has correct SUPABASE_URL and SUPABASE_KEY")
        print("2. Verify you ran the SQL schema in Supabase SQL Editor")
        print("3. Check your internet connection")
        print("4. Review Supabase dashboard for errors")
        sys.exit(1)


if __name__ == "__main__":
    test_connection()
