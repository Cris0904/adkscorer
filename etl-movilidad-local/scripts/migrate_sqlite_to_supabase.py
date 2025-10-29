"""
Migrate existing data from SQLite to Supabase
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

import sqlite3
import json
from dotenv import load_dotenv
from db_supabase import SupabaseNewsDatabase

# Load environment variables
load_dotenv()

def migrate_data(sqlite_path: str = "data/etl_movilidad.db"):
    """Migrate data from SQLite to Supabase"""
    print("="*60)
    print("MIGRATING DATA: SQLite → Supabase")
    print("="*60)

    # Check if SQLite database exists
    if not os.path.exists(sqlite_path):
        print(f"\n❌ SQLite database not found: {sqlite_path}")
        print("No data to migrate.")
        return

    try:
        # Connect to SQLite
        print(f"\n1. Reading from SQLite: {sqlite_path}")
        conn = sqlite3.connect(sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Count records
        cursor.execute("SELECT COUNT(*) FROM news_item")
        total_count = cursor.fetchone()[0]
        print(f"   ✓ Found {total_count} news items")

        if total_count == 0:
            print("   No data to migrate.")
            conn.close()
            return

        # Read all news items
        cursor.execute("SELECT * FROM news_item")
        rows = cursor.fetchall()
        conn.close()

        # Connect to Supabase
        print("\n2. Connecting to Supabase...")
        supabase_db = SupabaseNewsDatabase()
        print("   ✓ Connected")

        # Migrate data
        print(f"\n3. Migrating {len(rows)} news items...")
        migrated = 0
        duplicates = 0
        errors = 0

        for i, row in enumerate(rows, 1):
            try:
                # Convert SQLite row to dictionary
                news_item = {
                    'source': row['source'],
                    'url': row['url'],
                    'title': row['title'],
                    'body': row['body'],
                    'published_at': row['published_at'],
                    'severity': row['severity'],
                    'tags': json.loads(row['tags']) if row['tags'] else [],
                    'area': row['area'],
                    'entities': json.loads(row['entities']) if row['entities'] else [],
                    'summary': row['summary'],
                    'relevance_score': row['relevance_score']
                }

                # Insert into Supabase
                news_id = supabase_db.insert_news(news_item)

                if news_id:
                    migrated += 1
                    if i % 10 == 0 or i == len(rows):
                        print(f"   Progress: {i}/{len(rows)} ({migrated} migrated, {duplicates} duplicates)")
                else:
                    duplicates += 1

            except Exception as e:
                errors += 1
                print(f"   ⚠ Error migrating item {i}: {e}")

        # Migrate execution logs
        print("\n4. Migrating execution logs...")
        conn = sqlite3.connect(sqlite_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM execution_log")
        log_rows = cursor.fetchall()
        conn.close()

        logs_migrated = 0
        for log_row in log_rows:
            try:
                stats = {
                    'extracted': log_row['news_extracted'],
                    'deduplicated': log_row['news_deduplicated'],
                    'scored': log_row['news_scored'],
                    'kept': log_row['news_kept'],
                    'discarded': log_row['news_discarded'],
                    'errors': json.loads(log_row['errors']) if log_row['errors'] else [],
                    'duration': log_row['duration_seconds']
                }
                supabase_db.log_execution(stats)
                logs_migrated += 1
            except Exception as e:
                print(f"   ⚠ Error migrating log: {e}")

        print(f"   ✓ Migrated {logs_migrated} execution logs")

        # Print summary
        print("\n" + "="*60)
        print("MIGRATION COMPLETE")
        print("="*60)
        print(f"\nNews Items:")
        print(f"  - Total in SQLite:  {total_count}")
        print(f"  - Migrated:         {migrated}")
        print(f"  - Duplicates:       {duplicates}")
        print(f"  - Errors:           {errors}")
        print(f"\nExecution Logs:")
        print(f"  - Migrated:         {logs_migrated}")

        if errors > 0:
            print(f"\n⚠ {errors} errors occurred during migration")
        else:
            print("\n✓ Migration completed successfully!")

        print("\nNext steps:")
        print("1. Verify data in Supabase dashboard")
        print("2. Update your pipeline to use Supabase (already configured)")
        print("3. Consider backing up and archiving the SQLite database")

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your Supabase credentials in .env")
        print("2. Verify the SQL schema is created in Supabase")
        print("3. Check your internet connection")
        sys.exit(1)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Migrate data from SQLite to Supabase')
    parser.add_argument(
        '--sqlite-path',
        default='data/etl_movilidad.db',
        help='Path to SQLite database (default: data/etl_movilidad.db)'
    )
    args = parser.parse_args()

    migrate_data(args.sqlite_path)
