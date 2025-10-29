"""
Test Google ADK Agent with structured output_schema
True ADK implementation (October 2025+)

This replaces test_gemini_v2.py which incorrectly used google-generativeai SDK
Now using Google ADK (Agent Development Kit) with Pydantic output validation
"""
import sys
import os

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from generate_test_news import generate_test_news
from adk_scorer_v3 import ADKScorerV3
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


def main():
    print("=" * 70)
    print("TESTING GOOGLE ADK WITH OUTPUT_SCHEMA (October 2025)")
    print("=" * 70)

    # Get project ID from environment
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

    if not project_id:
        print("\n❌ ERROR: GOOGLE_CLOUD_PROJECT not set in .env file")
        print("\nSetup instructions:")
        print("1. Create/edit .env file in project root")
        print("2. Add: GOOGLE_CLOUD_PROJECT=your-project-id")
        return

    print(f"\n✅ Project ID: {project_id}")
    print(f"✅ Using Google ADK (Agent Development Kit)")
    print(f"✅ With Pydantic output_schema for automatic validation")
    print(f"✅ Framework: google-adk v0.2+\n")

    # Initialize scorer
    print("--- Initializing ADK Scorer V3 (True ADK Implementation) ---")
    try:
        scorer = ADKScorerV3(project_id=project_id)
        print("✅ ADK Agent initialized successfully\n")

        # Show stats
        stats = scorer.get_stats()
        print("Agent Configuration:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        print()

    except Exception as e:
        print(f"❌ Error initializing scorer: {e}")
        print("\nTroubleshooting:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Authenticate: gcloud auth application-default login")
        print("3. Verify google-adk is installed: pip show google-adk")
        print("4. Check that Vertex AI API is enabled in your project")
        return

    # Generate test news
    print("--- Generating test news ---")
    test_news = generate_test_news()[:3]  # Only test with 3 news
    print(f"✅ Generated {len(test_news)} test news items\n")

    # Test scoring
    print("--- Testing ADK Agent Scoring with Structured Output ---\n")

    for i, news in enumerate(test_news, 1):
        print(f"[{i}/{len(test_news)}] {news['title'][:60]}...")

        try:
            result = scorer.score(news)

            if result:
                print(f"    ✅ KEPT (Validated by Pydantic schema)")
                print(f"       Severity: {result.get('severity')}")
                print(f"       Score: {result.get('relevance_score'):.2f}")
                print(f"       Area: {result.get('area')}")
                print(f"       Tags: {', '.join(result.get('tags', [])[:3])}")
                print(f"       Entities: {', '.join(result.get('entities', [])[:2])}")
                print(f"       Summary: {result.get('summary', '')[:80]}...")
                print(f"       Reasoning: {result.get('reasoning', '')[:80]}...")
            else:
                print(f"    ❌ DISCARDED - Not relevant for mobility alerts")

        except Exception as e:
            print(f"    ❌ ERROR: {e}")

        print()

    print("=" * 70)
    print("TEST COMPLETE - Google ADK with output_schema")
    print("=" * 70)
    print("\n✅ Success indicators:")
    print("   - Agent initialized without errors")
    print("   - Structured responses validated by Pydantic")
    print("   - All required fields present in responses")
    print("\n📊 Key differences from V2 (SDK):")
    print("   - Using google.adk.agents.LlmAgent (not google.generativeai)")
    print("   - Automatic JSON validation via output_schema")
    print("   - No manual JSON parsing or error handling needed")
    print("   - Production-ready with guaranteed schema compliance\n")


if __name__ == "__main__":
    main()
