"""
News extractors for ETL Movilidad Medellín
Supports multiple sources: RSS feeds and web scraping
"""
import requests
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser as date_parser
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsExtractor:
    """Multi-source news extractor for Medellín mobility news"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def extract_all(self) -> List[Dict]:
        """Extract from all sources"""
        all_news = []

        # Source 1: Metro de Medellín RSS
        try:
            metro_news = self.extract_metro_rss()
            all_news.extend(metro_news)
            logger.info(f"Extracted {len(metro_news)} news from Metro RSS")
        except Exception as e:
            logger.error(f"Error extracting Metro RSS: {e}")

        # Source 2: Alcaldía de Medellín
        try:
            alcaldia_news = self.extract_alcaldia_web()
            all_news.extend(alcaldia_news)
            logger.info(f"Extracted {len(alcaldia_news)} news from Alcaldía")
        except Exception as e:
            logger.error(f"Error extracting Alcaldía: {e}")

        # Source 3: AMVA (Área Metropolitana del Valle de Aburrá)
        try:
            amva_news = self.extract_amva_web()
            all_news.extend(amva_news)
            logger.info(f"Extracted {len(amva_news)} news from AMVA")
        except Exception as e:
            logger.error(f"Error extracting AMVA: {e}")

        return all_news

    def extract_metro_rss(self) -> List[Dict]:
        """Extract news from Metro de Medellín RSS feed"""
        url = "https://www.metrodemedellin.gov.co/al-dia/noticias"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            feed = feedparser.parse(response.content)
            news_items = []

            for entry in feed.entries[:20]:  # Limit to 20 most recent
                try:
                    news_items.append(self._normalize_news({
                        'source': 'Metro de Medellín',
                        'url': entry.link,
                        'title': entry.title,
                        'body': self._clean_html(entry.get('summary', entry.get('description', ''))),
                        'published_at': self._parse_date(entry.get('published', entry.get('updated')))
                    }))
                except Exception as e:
                    logger.warning(f"Error parsing Metro entry: {e}")
                    continue

            return news_items
        except Exception as e:
            logger.error(f"Error fetching Metro RSS: {e}")
            return []

    def extract_alcaldia_web(self) -> List[Dict]:
        """Extract news from Alcaldía de Medellín website"""
        # Note: This is a simplified version. Adjust selectors based on actual website structure
        url = "https://www.medellin.gov.co/es/sala-de-prensa/noticias/?_sft_category=secretaria-de-movilidad"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            news_items = []

            # Example selectors - adjust to actual website structure
            articles = soup.select('article.noticia, div.news-item')[:15]

            for article in articles:
                try:
                    title_elem = article.select_one('h2, h3, .title')
                    link_elem = article.select_one('a')
                    summary_elem = article.select_one('.summary, .excerpt, p')
                    date_elem = article.select_one('.date, time')

                    if not title_elem or not link_elem:
                        continue

                    url_full = link_elem.get('href', '')
                    if not url_full.startswith('http'):
                        url_full = f"https://www.medellin.gov.co{url_full}"

                    news_items.append(self._normalize_news({
                        'source': 'Alcaldía de Medellín',
                        'url': url_full,
                        'title': title_elem.get_text(strip=True),
                        'body': summary_elem.get_text(strip=True) if summary_elem else '',
                        'published_at': self._parse_date(date_elem.get_text() if date_elem else None)
                    }))
                except Exception as e:
                    logger.warning(f"Error parsing Alcaldía article: {e}")
                    continue

            return news_items
        except Exception as e:
            logger.error(f"Error fetching Alcaldía website: {e}")
            return []

    def extract_amva_web(self) -> List[Dict]:
        """Extract news from AMVA website"""
        url = "https://www.metropol.gov.co/Paginas/Noticias.aspx"

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            news_items = []

            # Example selectors - adjust to actual website structure
            articles = soup.select('div.noticia, article')[:15]

            for article in articles:
                try:
                    title_elem = article.select_one('h2, h3, .titulo')
                    link_elem = article.select_one('a')
                    summary_elem = article.select_one('.resumen, p')
                    date_elem = article.select_one('.fecha, time')

                    if not title_elem or not link_elem:
                        continue

                    url_full = link_elem.get('href', '')
                    if not url_full.startswith('http'):
                        url_full = f"https://www.metropol.gov.co{url_full}"

                    news_items.append(self._normalize_news({
                        'source': 'AMVA',
                        'url': url_full,
                        'title': title_elem.get_text(strip=True),
                        'body': summary_elem.get_text(strip=True) if summary_elem else '',
                        'published_at': self._parse_date(date_elem.get_text() if date_elem else None)
                    }))
                except Exception as e:
                    logger.warning(f"Error parsing AMVA article: {e}")
                    continue

            return news_items
        except Exception as e:
            logger.error(f"Error fetching AMVA website: {e}")
            return []

    def _normalize_news(self, news: Dict) -> Dict:
        """Normalize news item structure"""
        return {
            'source': news['source'],
            'url': news['url'],
            'title': news['title'][:500],  # Limit title length
            'body': news['body'][:2000],   # Limit body length
            'published_at': news['published_at']
        }

    def _clean_html(self, html_text: str) -> str:
        """Remove HTML tags and clean text"""
        soup = BeautifulSoup(html_text, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        return text[:2000]  # Limit length

    def _parse_date(self, date_str: Optional[str]) -> str:
        """Parse date string to ISO format"""
        if not date_str:
            return datetime.now().isoformat()

        try:
            dt = date_parser.parse(date_str)
            return dt.isoformat()
        except:
            return datetime.now().isoformat()


class CustomSourceExtractor:
    """
    Template for adding custom news sources
    Copy this class and implement extract() method
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def extract(self) -> List[Dict]:
        """
        Extract news from custom source

        Returns:
            List of news items with structure:
            {
                'source': str,
                'url': str,
                'title': str,
                'body': str,
                'published_at': str (ISO format)
            }
        """
        # TODO: Implement your extraction logic
        return []
