"""
Test simplified Apify extractor
Uses Website Content Crawler instead of Web Scraper
"""
import sys
import os
import io

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from extractors_apify_simple import SimpleApifyExtractor, HybridApifyExtractor
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


def main():
    """Test simplified Apify extractor"""
    print("="*70)
    print("TESTING SIMPLIFIED APIFY EXTRACTOR")
    print("="*70)

    # Check API token
    api_token = os.getenv("APIFY_API_TOKEN")

    if not api_token or api_token.startswith("your-"):
        print("\n⚠️  APIFY_API_TOKEN not configured")
        print("\nPlease add your API token to .env file")
        return

    print(f"\n✓ API Token configured: {api_token[:20]}...")

    try:
        # Initialize extractor
        print("\n--- Initializing Simplified Apify Extractor ---")
        extractor = SimpleApifyExtractor(api_token)
        print("✓ Extractor initialized")

        # Extract news
        print("\n--- Extracting News ---")
        print("(Using Apify Website Content Crawler)\n")

        start_time = time.time()
        news_items = extractor.extract_all()
        duration = time.time() - start_time

        # Display results
        print("\n" + "="*70)
        print("EXTRACTION RESULTS")
        print("="*70)
        print(f"Total news extracted: {len(news_items)}")
        print(f"Duration: {duration:.2f} seconds")
        print("="*70)

        if news_items:
            print("\n📰 Sample news items:\n")

            # Group by source
            by_source = {}
            for item in news_items:
                source = item.get('source', 'Unknown')
                if source not in by_source:
                    by_source[source] = []
                by_source[source].append(item)

            # Display by source
            for source, items in by_source.items():
                print(f"\n🔹 {source} ({len(items)} items)")
                print("-" * 70)

                for i, item in enumerate(items[:5], 1):  # Show first 5
                    print(f"\n  [{i}] {item['title'][:70]}...")
                    print(f"      URL: {item['url'][:60]}...")
                    if item.get('body'):
                        print(f"      Body: {item['body'][:100]}...")

                if len(items) > 5:
                    print(f"\n  ... and {len(items) - 5} more items")

        else:
            print("\n⚠️  No news items extracted")
            print("\nPossible reasons:")
            print("  • Content extraction pattern needs adjustment")
            print("  • Websites have anti-scraping measures")
            print("  • Try different URLs or sources")

        print("\n" + "="*70)
        print("TEST COMPLETE")
        print("="*70)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
