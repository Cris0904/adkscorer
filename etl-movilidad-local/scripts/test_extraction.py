"""
Test script for news extraction
Tests all extractors without saving to database or scoring with ADK
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from extractors import NewsExtractor
import json


def main():
    print("="*60)
    print("Testing News Extraction")
    print("="*60)

    extractor = NewsExtractor()

    # Test each source individually
    sources = [
        ('Metro de Medellín RSS', extractor.extract_metro_rss),
        ('Alcaldía de Medellín', extractor.extract_alcaldia_web),
        ('AMVA', extractor.extract_amva_web)
    ]

    total_extracted = 0

    for source_name, extract_func in sources:
        print(f"\n--- Testing {source_name} ---")
        try:
            news = extract_func()
            count = len(news)
            total_extracted += count

            print(f"✓ Extracted {count} news items")

            if news:
                print(f"\nSample (first item):")
                print(json.dumps(news[0], indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"✗ Error: {e}")

    print("\n" + "="*60)
    print(f"Total extracted: {total_extracted} news items")
    print("="*60)

    # Test extract_all
    print("\n--- Testing extract_all() ---")
    try:
        all_news = extractor.extract_all()
        print(f"✓ Total from extract_all(): {len(all_news)} news items")
    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    main()
