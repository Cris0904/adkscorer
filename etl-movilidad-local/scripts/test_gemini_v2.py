"""
Test Google Gemini with modern SDK (google-generativeai)
This should work without deprecation warnings
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from generate_test_news import generate_test_news
from adk_scorer_v2 import ADKScorerV2
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

def main():
    print("="*70)
    print("TESTING GEMINI WITH MODERN SDK (October 2025)")
    print("="*70)

    # Get project ID from environment
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

    if not project_id:
        print("ERROR: GOOGLE_CLOUD_PROJECT not set in .env file")
        return

    print(f"\n✓ Project ID: {project_id}")
    print(f"✓ Using modern google-generativeai SDK")
    print(f"✓ No deprecation warnings expected\n")

    # Initialize scorer
    print("--- Initializing ADK Scorer V2 ---")
    try:
        scorer = ADKScorerV2(project_id=project_id)
        print("✓ ADK Scorer V2 initialized successfully")
    except Exception as e:
        print(f"✗ Error initializing scorer: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you've run: gcloud auth application-default login")
        print("2. Or set GOOGLE_API_KEY in .env")
        print("3. Check that Gemini API is available in your region")
        return

    # Generate test news
    print("\n--- Generating test news ---")
    test_news = generate_test_news()[:3]  # Only test with 3 news
    print(f"✓ Generated {len(test_news)} test news items\n")

    # Test scoring
    print("--- Testing Gemini Scoring ---\n")

    for i, news in enumerate(test_news, 1):
        print(f"[{i}/{len(test_news)}] {news['title'][:60]}...")

        try:
            result = scorer.score(news)

            if result:
                print(f"    ✓ KEPT")
                print(f"      Severity: {result.get('severity')}")
                print(f"      Score: {result.get('relevance_score')}")
                print(f"      Area: {result.get('area')}")
                print(f"      Tags: {', '.join(result.get('tags', [])[:3])}")
                print(f"      Summary: {result.get('summary', '')[:80]}...")
            else:
                print(f"    ✗ DISCARDED - Not relevant")

        except Exception as e:
            print(f"    ✗ ERROR: {e}")

        print()

    print("="*70)
    print("TEST COMPLETE")
    print("="*70)
    print("\n✅ If you see scored results above, Gemini is working!")
    print("❌ If you see errors, check the troubleshooting tips above\n")


if __name__ == "__main__":
    main()
