"""
Clear all data from Supabase (fresh start)
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

def clear_supabase():
    """Clear all data from Supabase"""
    print("="*60)
    print("CLEARING SUPABASE DATABASE")
    print("="*60)

    try:
        db = SupabaseNewsDatabase()
        print("\n✓ Connected to Supabase")

        # Get current counts
        stats = db.get_stats()
        total_news = stats.get('total_news', 0)

        print(f"\nCurrent data:")
        print(f"  - News items: {total_news}")
        print(f"  - Execution logs: {stats.get('recent_executions', 0)}")

        if total_news == 0:
            print("\n✓ Database is already empty")
            return

        # Confirm deletion
        print(f"\n⚠️  WARNING: This will delete all {total_news} news items and execution logs!")
        response = input("Are you sure? (yes/no): ").strip().lower()

        if response != 'yes':
            print("\n✗ Cancelled")
            return

        print("\nDeleting data...")

        # Delete all news items
        # Note: We need to use the Supabase client directly for deletion
        try:
            # Delete all news
            db.client.table('news_item').delete().neq('id', 0).execute()
            print("  ✓ Deleted all news items")
        except Exception as e:
            print(f"  ⚠️  Error deleting news: {e}")

        try:
            # Delete all execution logs
            db.client.table('execution_log').delete().neq('id', 0).execute()
            print("  ✓ Deleted all execution logs")
        except Exception as e:
            print(f"  ⚠️  Error deleting logs: {e}")

        # Verify
        stats = db.get_stats()
        print(f"\nAfter clearing:")
        print(f"  - News items: {stats.get('total_news', 0)}")
        print(f"  - Execution logs: {stats.get('recent_executions', 0)}")

        print("\n" + "="*60)
        print("✓ SUPABASE DATABASE CLEARED")
        print("="*60)
        print("\nYou can now run the pipeline to populate with fresh data:")
        print("  python src/main.py")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    clear_supabase()
