"""
Demo of full ETL pipeline using Mock ADK
Shows complete system functionality without requiring Gemini API access
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from generate_test_news import generate_test_news
from adk_scorer import MockADKScorer
from db import NewsDatabase
from alert_manager import ConsoleOnlyAlertManager
import time

def main():
    print("="*70)
    print("DEMO: ETL MOVILIDAD MEDELLÍN - COMPLETE PIPELINE")
    print("="*70)
    print("\n📝 Using MockADKScorer (simulates Google Gemini)")
    print("   This demo shows how the complete system works\n")

    # Initialize components
    print("--- Step 1: Initializing Components ---")

    db = NewsDatabase()
    print("✓ Database initialized (SQLite)")

    scorer = MockADKScorer()
    print("✓ Mock ADK Scorer initialized (keyword-based classification)")

    alert_manager = ConsoleOnlyAlertManager()
    print("✓ Alert Manager initialized (console + JSON file)")

    # Generate test news
    print("\n--- Step 2: Extracting News ---")
    test_news = generate_test_news()
    print(f"✓ Extracted {len(test_news)} news items from sources:")
    sources = set(n['source'] for n in test_news)
    for source in sources:
        count = sum(1 for n in test_news if n['source'] == source)
        print(f"  • {source}: {count} items")

    # Deduplicate
    print("\n--- Step 3: Deduplicating ---")
    unique_news = []
    duplicates = 0
    for news in test_news:
        if not db.is_duplicate(news['url']):
            unique_news.append(news)
        else:
            duplicates += 1

    print(f"✓ Found {duplicates} duplicates")
    print(f"✓ {len(unique_news)} unique news items to process")

    # Score with Mock ADK
    print("\n--- Step 4: Scoring with Mock ADK ---")
    print("(Analyzing relevance for mobility alerts)\n")

    scored_news = []
    kept_count = 0
    discarded_count = 0

    start_time = time.time()

    for i, news in enumerate(unique_news, 1):
        print(f"[{i}/{len(unique_news)}] {news['title'][:65]}...")

        result = scorer.score(news)

        if result:
            scored_news.append(result)
            kept_count += 1
            print(f"         ✓ KEPT - Severity: {result.get('severity')}")
        else:
            discarded_count += 1
            print(f"         ✗ DISCARDED - Not mobility-relevant")

    duration = time.time() - start_time

    print("\n" + "="*70)
    print("SCORING SUMMARY")
    print("="*70)
    print(f"Total processed:  {len(unique_news)}")
    print(f"Kept:             {kept_count} ({kept_count/len(unique_news)*100:.0f}%)")
    print(f"Discarded:        {discarded_count} ({discarded_count/len(unique_news)*100:.0f}%)")
    print(f"Processing time:  {duration:.2f} seconds")
    print("="*70)

    # Save to database
    if scored_news:
        print("\n--- Step 5: Saving to Database ---")
        saved_count = 0
        for news in scored_news:
            news_id = db.insert_news(news)
            if news_id:
                saved_count += 1
                news['id'] = news_id

        print(f"✓ Saved {saved_count} news items to database")
        print(f"  Location: data/etl_movilidad.db")

        # Send alerts
        print("\n--- Step 6: Sending Alerts ---")
        high_severity = [n for n in scored_news if n.get('severity') in ['high', 'critical']]

        if high_severity:
            print(f"Found {len(high_severity)} high/critical severity news\n")
            for news in high_severity:
                alert_manager.send_alert(news)
                if 'id' in news:
                    db.mark_as_alerted(news['id'])
            print(f"\n✓ Sent {len(high_severity)} alerts")
        else:
            print("ℹ️  No high/critical severity news (all are medium/low)")

        # Show statistics
        print("\n--- Step 7: Database Statistics ---")
        stats = db.get_stats()
        print(f"\n📊 Total news in database: {stats['total_news']}")
        print(f"\n📈 By Severity:")
        for severity, count in stats['by_severity'].items():
            bars = '█' * int(count / stats['total_news'] * 20)
            print(f"  {severity:8s}: {bars} {count}")

        print(f"\n📰 By Source:")
        for source, count in stats['by_source'].items():
            bars = '█' * int(count / stats['total_news'] * 20)
            print(f"  {source:30s}: {bars} {count}")

    print("\n" + "="*70)
    print("✅ DEMO COMPLETE")
    print("="*70)
    print("\n📋 Next Steps:")
    print("  1. Run 'python db_stats.py' to see detailed statistics")
    print("  2. Run 'python view_alerts.py' to see all alerts")
    print("  3. Open 'data/etl_movilidad.db' with a SQLite browser")
    print("  4. Check 'logs/alerts.json' for alert history")
    print("\n💡 To enable Google Gemini:")
    print("  • Contact Google Cloud support to enable Gemini API")
    print("  • Or wait for general availability in your region")
    print("  • For now, Mock ADK demonstrates the complete workflow\n")


if __name__ == "__main__":
    main()
