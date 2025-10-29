"""
Test Apify web scraping
This script tests the Apify extractor before integrating it into the main pipeline
"""
import sys
import os
import io

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from extractors_apify import ApifyNewsExtractor, HybridNewsExtractor
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


def test_apify_extractor():
    """Test Apify extractor directly"""
    print("="*70)
    print("TESTING APIFY NEWS EXTRACTOR")
    print("="*70)

    # Check if API token is set
    api_token = os.getenv("APIFY_API_TOKEN")

    if not api_token or api_token == "your-apify-api-token-here":
        print("\n⚠️  APIFY_API_TOKEN not configured in .env")
        print("\n📋 Steps to get your API token:")
        print("  1. Go to: https://console.apify.com/sign-up")
        print("  2. Sign up (FREE - no credit card required)")
        print("  3. Go to: https://console.apify.com/account/integrations")
        print("  4. Copy your 'Personal API token'")
        print("  5. Add to .env file: APIFY_API_TOKEN=apify_api_XXX...")
        print("\n💰 Free tier includes:")
        print("  • $5/month credit (renews automatically)")
        print("  • No credit card required")
        print("  • Access to all Apify actors")
        print("\n")
        return

    print(f"\n✓ API Token found: {api_token[:20]}...")

    try:
        # Initialize extractor
        print("\n--- Initializing Apify Extractor ---")
        extractor = ApifyNewsExtractor(api_token)
        print("✓ Apify extractor initialized")

        # Test extraction
        print("\n--- Extracting News from All Sources ---")
        print("(This will use Apify Web Scraper and may take 30-60 seconds)\n")

        start_time = time.time()

        # Extract all news
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

                for i, item in enumerate(items[:3], 1):  # Show first 3 from each source
                    print(f"\n  [{i}] {item['title'][:70]}...")
                    print(f"      URL: {item['url'][:60]}...")
                    print(f"      Published: {item['published_at'][:10]}")
                    if item.get('body'):
                        print(f"      Summary: {item['body'][:100]}...")

                if len(items) > 3:
                    print(f"\n  ... and {len(items) - 3} more items")

        else:
            print("\n⚠️  No news items extracted")
            print("\nPossible reasons:")
            print("  • Website structure may have changed")
            print("  • Selectors need to be updated")
            print("  • Websites may be blocking scraping")

        print("\n" + "="*70)
        print("TEST COMPLETE")
        print("="*70)

    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()


def test_hybrid_extractor():
    """Test hybrid extractor (Apify + fallback)"""
    print("\n\n")
    print("="*70)
    print("TESTING HYBRID EXTRACTOR (Apify + Fallback)")
    print("="*70)

    try:
        # Initialize hybrid extractor
        print("\n--- Initializing Hybrid Extractor ---")
        extractor = HybridNewsExtractor()
        print("✓ Hybrid extractor initialized")

        # Extract news
        print("\n--- Extracting News ---\n")

        start_time = time.time()
        news_items = extractor.extract_all()
        duration = time.time() - start_time

        # Display results
        print("\n" + "="*70)
        print("EXTRACTION RESULTS")
        print("="*70)
        print(f"Total news extracted: {len(news_items)}")
        print(f"Duration: {duration:.2f} seconds")

        if news_items:
            print(f"\n✓ Successfully extracted {len(news_items)} news items")

            # Group by source
            by_source = {}
            for item in news_items:
                source = item.get('source', 'Unknown')
                by_source[source] = by_source.get(source, 0) + 1

            print("\n📊 By Source:")
            for source, count in by_source.items():
                print(f"  • {source}: {count} items")

        print("\n" + "="*70)
        print("TEST COMPLETE")
        print("="*70)

    except Exception as e:
        print(f"\n✗ Error during test: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main test function"""
    print("\n🧪 APIFY SCRAPING TEST SUITE\n")

    # Test 1: Direct Apify extractor
    test_apify_extractor()

    # Test 2: Hybrid extractor
    # test_hybrid_extractor()  # Uncomment to test


if __name__ == "__main__":
    main()
