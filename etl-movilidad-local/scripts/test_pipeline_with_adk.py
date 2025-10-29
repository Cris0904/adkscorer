"""
Test pipeline with ADK using sample news
This will test the complete pipeline with Google ADK (Gemini 2.0 Flash)
"""
import sys
import os
import io

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from generate_test_news import generate_test_news
from adk_scorer_v3 import ADKScorerV3
from db import NewsDatabase
from alert_manager import ConsoleOnlyAlertManager
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def main():
    print("="*60)
    print("TESTING ETL PIPELINE WITH ADK (Google Gemini)")
    print("="*60)

    # Get project ID from environment
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

    if not project_id:
        print("ERROR: GOOGLE_CLOUD_PROJECT not set in .env file")
        return

    print(f"\n✓ Project ID: {project_id}")
    print(f"✓ Using Google ADK with Gemini 2.0 Flash")

    # Initialize components
    print("\n--- Initializing components ---")

    try:
        db = NewsDatabase()
        print("✓ Database initialized")

        scorer = ADKScorerV3(project_id=project_id)
        print("✓ ADKScorerV3 initialized (Google ADK)")

        alert_manager = ConsoleOnlyAlertManager()
        print("✓ Alert Manager initialized")
    except Exception as e:
        print(f"✗ Error initializing components: {e}")
        return

    # Generate test news
    print("\n--- Generating test news ---")
    test_news = generate_test_news()
    print(f"✓ Generated {len(test_news)} test news items")

    # Score with ADK
    print("\n--- Scoring news with Google Gemini ---")
    print("(This will make API calls to Vertex AI)\n")

    scored_news = []
    kept_count = 0
    discarded_count = 0

    start_time = time.time()

    for i, news in enumerate(test_news, 1):
        print(f"[{i}/{len(test_news)}] Scoring: {news['title'][:60]}...")

        try:
            result = scorer.score(news)

            if result:
                scored_news.append(result)
                kept_count += 1
                print(f"    ✓ KEPT - Severity: {result.get('severity')} | Score: {result.get('relevance_score')}")
                print(f"    Tags: {', '.join(result.get('tags', [])[:3])}")
                print(f"    Area: {result.get('area')}")
            else:
                discarded_count += 1
                print(f"    ✗ DISCARDED - Not relevant for mobility alerts")
        except Exception as e:
            print(f"    ✗ ERROR: {e}")
            discarded_count += 1

        print()

    duration = time.time() - start_time

    # Summary
    print("="*60)
    print("SCORING SUMMARY")
    print("="*60)
    print(f"Total news:      {len(test_news)}")
    print(f"Kept:            {kept_count} ({kept_count/len(test_news)*100:.1f}%)")
    print(f"Discarded:       {discarded_count} ({discarded_count/len(test_news)*100:.1f}%)")
    print(f"Duration:        {duration:.2f} seconds")
    print(f"Avg per item:    {duration/len(test_news):.2f} seconds")
    print("="*60)

    # Save to database
    if scored_news:
        print("\n--- Saving to database ---")
        saved_count = 0
        for news in scored_news:
            news_id = db.insert_news(news)
            if news_id:
                saved_count += 1
                news['id'] = news_id

        print(f"✓ Saved {saved_count} news items to database")

        # Send alerts
        print("\n--- Sending alerts for high severity ---")
        high_severity = [n for n in scored_news if n.get('severity') in ['high', 'critical']]

        if high_severity:
            print(f"Found {len(high_severity)} high/critical severity news\n")
            for news in high_severity:
                alert_manager.send_alert(news)
                if 'id' in news:
                    db.mark_as_alerted(news['id'])
        else:
            print("No high severity news to alert")

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. Run 'python db_stats.py' to see database statistics")
    print("2. Run 'python view_alerts.py' to see generated alerts")
    print("3. Check 'data/etl_movilidad.db' to explore the database")
    print("\n")


if __name__ == "__main__":
    main()
