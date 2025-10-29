"""
News extractors using Apify Web Scraper
Provides reliable scraping for Medellín mobility news sources
"""
import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
from apify_client import ApifyClient
from dateutil import parser as date_parser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ApifyNewsExtractor:
    """
    News extractor using Apify Web Scraper
    Uses Apify's Web Scraper actor for reliable content extraction
    """

    def __init__(self, api_token: Optional[str] = None):
        """
        Initialize Apify extractor

        Args:
            api_token: Apify API token (if None, reads from APIFY_API_TOKEN env var)
        """
        self.api_token = api_token or os.getenv("APIFY_API_TOKEN")

        if not self.api_token:
            raise ValueError(
                "APIFY_API_TOKEN not found. "
                "Set it in .env or pass it to constructor"
            )

        self.client = ApifyClient(self.api_token)
        logger.info("✓ Apify client initialized")

    def extract_all(self) -> List[Dict]:
        """Extract from all configured sources"""
        all_news = []

        # Source 1: Metro de Medellín
        try:
            metro_news = self.extract_metro()
            all_news.extend(metro_news)
            logger.info(f"✓ Extracted {len(metro_news)} news from Metro")
        except Exception as e:
            logger.error(f"✗ Error extracting Metro: {e}")

        # Source 2: Alcaldía de Medellín
        try:
            alcaldia_news = self.extract_alcaldia()
            all_news.extend(alcaldia_news)
            logger.info(f"✓ Extracted {len(alcaldia_news)} news from Alcaldía")
        except Exception as e:
            logger.error(f"✗ Error extracting Alcaldía: {e}")

        # Source 3: AMVA
        try:
            amva_news = self.extract_amva()
            all_news.extend(amva_news)
            logger.info(f"✓ Extracted {len(amva_news)} news from AMVA")
        except Exception as e:
            logger.error(f"✗ Error extracting AMVA: {e}")

        return all_news

    def extract_metro(self) -> List[Dict]:
        """Extract news from Metro de Medellín"""
        # Metro news page
        url = "https://www.metrodemedellin.gov.co/al-dia/noticias"

        run_input = {
            "startUrls": [{"url": url}],
            "pseudoUrls": [],
            "linkSelector": "a.noticia-link, article a",
            "pageFunction": """
                async function pageFunction(context) {
                    const { $, request } = context;

                    // Extract news items
                    const articles = [];

                    $('article, .noticia-item, .news-item').each(function() {
                        const article = $(this);
                        const title = article.find('h2, h3, .title').first().text().trim();
                        const link = article.find('a').first().attr('href');
                        const summary = article.find('p, .summary, .excerpt').first().text().trim();
                        const date = article.find('time, .date').first().text().trim();

                        if (title && link) {
                            articles.push({
                                title: title,
                                url: link.startsWith('http') ? link : 'https://www.metrodemedellin.gov.co' + link,
                                body: summary || title,
                                published_at: date || new Date().toISOString(),
                                source: 'Metro de Medellín'
                            });
                        }
                    });

                    return articles.length > 0 ? articles : null;
                }
            """,
            "maxRequestsPerCrawl": 20,
            "maxConcurrency": 5,
        }

        return self._run_scraper(run_input, "Metro de Medellín")

    def extract_alcaldia(self) -> List[Dict]:
        """Extract news from Alcaldía de Medellín"""
        # Updated URL for Alcaldía news
        url = "https://www.medellin.gov.co/es/sala-de-prensa/noticias/"

        run_input = {
            "startUrls": [{"url": url}],
            "pseudoUrls": [],
            "linkSelector": "a.news-link, article a",
            "pageFunction": """
                async function pageFunction(context) {
                    const { $, request } = context;

                    const articles = [];

                    $('article, .news-item, .noticia').each(function() {
                        const article = $(this);
                        const title = article.find('h2, h3, .title').first().text().trim();
                        const link = article.find('a').first().attr('href');
                        const summary = article.find('p, .summary').first().text().trim();
                        const date = article.find('time, .date, .fecha').first().text().trim();

                        if (title && link) {
                            articles.push({
                                title: title,
                                url: link.startsWith('http') ? link : 'https://www.medellin.gov.co' + link,
                                body: summary || title,
                                published_at: date || new Date().toISOString(),
                                source: 'Alcaldía de Medellín'
                            });
                        }
                    });

                    return articles.length > 0 ? articles : null;
                }
            """,
            "maxRequestsPerCrawl": 20,
            "maxConcurrency": 5,
        }

        return self._run_scraper(run_input, "Alcaldía de Medellín")

    def extract_amva(self) -> List[Dict]:
        """Extract news from AMVA"""
        url = "minuto30.com/categoria/medellin/"

        run_input = {
            "startUrls": [{"url": url}],
            "pseudoUrls": [],
            "linkSelector": "a.news-link",
            "pageFunction": """
                async function pageFunction(context) {
                    const { $, request } = context;

                    const articles = [];

                    $('article, .noticia, .news-item, div[class*="noticia"]').each(function() {
                        const article = $(this);
                        const title = article.find('h2, h3, .title, .titulo').first().text().trim();
                        const link = article.find('a').first().attr('href');
                        const summary = article.find('p, .summary, .resumen').first().text().trim();
                        const date = article.find('time, .date, .fecha').first().text().trim();

                        if (title && link) {
                            articles.push({
                                title: title,
                                url: link.startsWith('http') ? link : 'https://www.metropol.gov.co' + link,
                                body: summary || title,
                                published_at: date || new Date().toISOString(),
                                source: 'AMVA'
                            });
                        }
                    });

                    return articles.length > 0 ? articles : null;
                }
            """,
            "maxRequestsPerCrawl": 20,
            "maxConcurrency": 5,
        }

        return self._run_scraper(run_input, "AMVA")

    def _run_scraper(self, run_input: Dict, source_name: str) -> List[Dict]:
        """
        Run Apify Web Scraper actor

        Args:
            run_input: Input configuration for the scraper
            source_name: Name of the news source

        Returns:
            List of extracted news items
        """
        try:
            logger.info(f"🔄 Running Apify scraper for {source_name}...")

            # Run the Apify Web Scraper actor
            run = self.client.actor("apify/web-scraper").call(run_input=run_input)

            # Get results from dataset
            items = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                if item and isinstance(item, list):
                    # If pageFunction returns an array
                    items.extend(item)
                elif item:
                    items.append(item)

            logger.info(f"✓ Apify scraped {len(items)} items from {source_name}")

            # Normalize items
            normalized_items = []
            for item in items:
                try:
                    normalized = self._normalize_news(item)
                    if normalized:
                        normalized_items.append(normalized)
                except Exception as e:
                    logger.warning(f"Error normalizing item: {e}")
                    continue

            return normalized_items

        except Exception as e:
            logger.error(f"Error running Apify scraper for {source_name}: {e}")
            return []

    def _normalize_news(self, item: Dict) -> Optional[Dict]:
        """
        Normalize news item to standard format

        Args:
            item: Raw item from Apify

        Returns:
            Normalized news dict or None if invalid
        """
        try:
            # Extract fields
            title = item.get('title', '').strip()
            url = item.get('url', '').strip()
            body = item.get('body', '').strip()
            source = item.get('source', 'Unknown').strip()
            published_at = item.get('published_at', '')

            # Validate required fields
            if not title or not url:
                return None

            # Parse date
            if published_at:
                try:
                    dt = date_parser.parse(published_at)
                    published_at = dt.isoformat()
                except:
                    published_at = datetime.now().isoformat()
            else:
                published_at = datetime.now().isoformat()

            return {
                'source': source,
                'url': url,
                'title': title[:500],  # Limit length
                'body': body[:2000] if body else title,  # Use title if no body
                'published_at': published_at
            }

        except Exception as e:
            logger.warning(f"Error normalizing news item: {e}")
            return None


class HybridNewsExtractor:
    """
    Hybrid extractor that tries Apify first, falls back to direct scraping
    """

    def __init__(self):
        """Initialize hybrid extractor"""
        # Try to initialize Apify
        apify_token = os.getenv("APIFY_API_TOKEN")

        if apify_token:
            try:
                self.apify_extractor = ApifyNewsExtractor(apify_token)
                self.use_apify = True
                logger.info("✓ Using Apify for extraction")
            except Exception as e:
                logger.warning(f"Could not initialize Apify: {e}")
                self.use_apify = False
        else:
            logger.info("ℹ️  APIFY_API_TOKEN not set, using direct scraping")
            self.use_apify = False

        # Always have fallback extractor ready
        if not self.use_apify:
            from extractors import NewsExtractor
            self.fallback_extractor = NewsExtractor()

    def extract_all(self) -> List[Dict]:
        """Extract using Apify or fallback to direct scraping"""
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
