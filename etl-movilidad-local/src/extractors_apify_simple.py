"""
Simplified Apify news extractor using Website Content Crawler
More reliable than Web Scraper with custom pageFunction
"""
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
from apify_client import ApifyClient
from dateutil import parser as date_parser
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleApifyExtractor:
    """
    Simplified news extractor using Apify's Website Content Crawler
    This is more reliable for news extraction
    """

    def __init__(self, api_token: Optional[str] = None):
        """Initialize Apify extractor"""
        self.api_token = api_token or os.getenv("APIFY_API_TOKEN")

        if not self.api_token:
            raise ValueError("APIFY_API_TOKEN not found")

        self.client = ApifyClient(self.api_token)
        logger.info("✓ Apify client initialized")

    def extract_all(self) -> List[Dict]:
        """Extract from all sources"""
        all_news = []

        sources = [
            {
                "name": "Metro de Medellín",
                "url": "https://www.metrodemedellin.gov.co/al-dia/noticias",
                "selectors": {
                    "article": "article, .noticia, .news-item",
                    "title": "h2, h3, .title",
                    "link": "a",
                    "summary": "p, .summary",
                    "date": "time, .date"
                }
            },
            {
                "name": "Alcaldía de Medellín",
                "url": "https://www.medellin.gov.co/es/sala-de-prensa/noticias/",
                "selectors": {
                    "article": "article, .news-item",
                    "title": "h2, h3",
                    "link": "a",
                    "summary": "p",
                    "date": "time, .date"
                }
            },
            {
                "name": "El Colombiano - Movilidad",
                "url": "https://www.elcolombiano.com/antioquia/movilidad",
                "selectors": {
                    "article": "article, .article",
                    "title": "h2, h3, .headline",
                    "link": "a",
                    "summary": "p, .description",
                    "date": "time, .date"
                }
            },
            {
                "name": "Minuto30 - Medellín",
                "url": "https://www.minuto30.com/categoria/medellin/",
                "selectors": {
                    "article": "article, .post",
                    "title": "h2, h3, .entry-title",
                    "link": "a",
                    "summary": "p, .excerpt",
                    "date": "time, .published"
                }
            }
        ]

        for source_config in sources:
            try:
                news = self.extract_source(source_config)
                all_news.extend(news)
                logger.info(f"✓ Extracted {len(news)} from {source_config['name']}")
            except Exception as e:
                logger.error(f"✗ Error extracting {source_config['name']}: {e}")

        return all_news

    def extract_source(self, source_config: Dict) -> List[Dict]:
        """
        Extract news from a source using Apify Website Content Crawler

        Args:
            source_config: Configuration with url, name, and selectors

        Returns:
            List of news items
        """
        try:
            logger.info(f"🔄 Crawling {source_config['name']}...")

            # Use Website Content Crawler - simpler and more reliable
            run_input = {
                "startUrls": [{"url": source_config['url']}],
                "crawlerType": "cheerio",  # Use Cheerio (faster, works for static pages)
                "maxCrawlDepth": 0,  # Only crawl the start URL
                "maxCrawlPages": 1,
                "proxyConfiguration": {"useApifyProxy": True},
            }

            # Run the Website Content Crawler
            run = self.client.actor("apify/website-content-crawler").call(run_input=run_input)

            # Get results
            items = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                items.append(item)

            logger.info(f"✓ Crawled {len(items)} pages from {source_config['name']}")

            # Extract news from the crawled content
            news_items = []
            for item in items:
                extracted = self._extract_news_from_html(
                    item.get('text', ''),
                    item.get('url', source_config['url']),
                    source_config
                )
                news_items.extend(extracted)

            return news_items

        except Exception as e:
            logger.error(f"Error crawling {source_config['name']}: {e}")
            return []

    def _extract_news_from_html(self, text: str, url: str, source_config: Dict) -> List[Dict]:
        """
        Extract news items from crawled text content

        Args:
            text: The text content from the page
            url: The URL of the page
            source_config: Source configuration

        Returns:
            List of news items
        """
        news_items = []

        # Split text into potential news sections
        # Look for patterns like headlines followed by content
        lines = text.split('\n')

        current_title = None
        current_body = []
        item_index = 0

        for line in lines:
            line = line.strip()

            if not line:
                continue

            # Heuristic: Lines that look like titles
            # More flexible: 15-300 chars, starts uppercase
            if len(line) >= 15 and len(line) <= 300:
                # Check if it looks like a title (starts uppercase)
                if line[0].isupper():
                    # Save previous item if we have one
                    if current_title:
                        # More lenient: accept items with minimal or no body
                        body_text = ' '.join(current_body) if current_body else current_title

                        # Generate unique URL for each news item
                        # Use base URL + title slug to make it unique
                        title_slug = re.sub(r'[^a-z0-9]+', '-', current_title.lower())[:50]
                        unique_url = f"{url}#{title_slug}-{item_index}"
                        item_index += 1

                        news_items.append({
                            'source': source_config['name'],
                            'url': unique_url,  # ← Ahora cada noticia tiene URL única
                            'title': current_title[:500],
                            'body': body_text[:2000],
                            'published_at': datetime.now().isoformat()
                        })

                    current_title = line
                    current_body = []
                elif current_title and len(line) > 10:
                    # Collect body text (more lenient threshold)
                    current_body.append(line)
            elif current_title and len(line) > 10:
                current_body.append(line)

        # Add the last item
        if current_title:
            body_text = ' '.join(current_body) if current_body else current_title

            # Generate unique URL for the last item
            title_slug = re.sub(r'[^a-z0-9]+', '-', current_title.lower())[:50]
            unique_url = f"{url}#{title_slug}-{item_index}"

            news_items.append({
                'source': source_config['name'],
                'url': unique_url,
                'title': current_title[:500],
                'body': body_text[:2000],
                'published_at': datetime.now().isoformat()
            })

        # More lenient filter: only require minimal content
        news_items = [item for item in news_items if len(item['body']) >= 15]

        return news_items[:15]  # Limit to 15 items per source


class HybridApifyExtractor:
    """
    Hybrid extractor that tries Apify, falls back to direct scraping
    """

    def __init__(self):
        """Initialize hybrid extractor"""
        apify_token = os.getenv("APIFY_API_TOKEN")

        if apify_token:
            try:
                self.apify_extractor = SimpleApifyExtractor(apify_token)
                self.use_apify = True
                logger.info("✓ Using Apify for extraction")
            except Exception as e:
                logger.warning(f"Could not initialize Apify: {e}")
                self.use_apify = False
        else:
            logger.info("ℹ️  APIFY_API_TOKEN not set, using direct scraping")
            self.use_apify = False

        if not self.use_apify:
            from extractors import NewsExtractor
            self.fallback_extractor = NewsExtractor()

    def extract_all(self) -> List[Dict]:
        """Extract using Apify or fallback"""
        if self.use_apify:
            try:
                return self.apify_extractor.extract_all()
            except Exception as e:
                logger.error(f"Apify extraction failed: {e}")
                logger.info("Falling back to direct scraping...")
                if hasattr(self, 'fallback_extractor'):
                    return self.fallback_extractor.extract_all()
                return []
        else:
            return self.fallback_extractor.extract_all()
