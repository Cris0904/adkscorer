"""
ADK Scorer module using Google Vertex AI (Gemini 1.5 Flash)
Analyzes news items and provides relevance scoring, tagging, and classification

⚠️  DEPRECATED: This module uses the old Vertex AI SDK directly.
    Please use adk_scorer_v3.ADKScorerV3 instead, which uses the proper Google ADK framework.
    See README_ADK.md for migration instructions.
"""
import json
import os
from typing import Dict, Optional
import logging
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig
from prompts.system_prompt import SYSTEM_PROMPT, build_user_prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ADKScorer:
    """
    ADK-based news scorer using Google Gemini 1.5 Flash
    Handles intelligent classification and enrichment of news items
    """

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        model_name: str = "gemini-1.5-flash-001"
    ):
        """
        Initialize ADK Scorer

        Args:
            project_id: Google Cloud project ID
            location: Vertex AI location (default: us-central1)
            model_name: Gemini model to use (default: gemini-1.5-flash-001)
        """
        self.project_id = project_id
        self.location = location
        self.model_name = model_name

        # Initialize Vertex AI
        try:
            vertexai.init(project=project_id, location=location)
            logger.info(f"Initialized Vertex AI: {project_id} in {location}")
        except Exception as e:
            logger.error(f"Error initializing Vertex AI: {e}")
            raise

        # Initialize model - try different model names
        try:
            # Try with publishers prefix first
            self.model = GenerativeModel("gemini-1.5-flash-001")
            logger.info(f"Using model: gemini-1.5-flash-001")
        except:
            try:
                # Fallback to simpler name
                self.model = GenerativeModel("gemini-pro")
                self.model_name = "gemini-pro"
                logger.info(f"Fallback to model: gemini-pro")
            except Exception as e:
                logger.error(f"Could not initialize any Gemini model: {e}")
                raise

        # Generation config for JSON output
        self.generation_config = GenerationConfig(
            temperature=0.1,  # Low temperature for consistent output
            top_p=0.95,
            top_k=40,
            max_output_tokens=1024,
            response_mime_type="application/json"
        )

    def score(self, news_item: Dict) -> Optional[Dict]:
        """
        Score a news item using ADK

        Args:
            news_item: Dict with keys: source, title, body, published_at, url

        Returns:
            Enriched news item with ADK fields, or None if scoring fails
        """
        try:
            # Build prompt
            user_prompt = build_user_prompt(news_item)

            # Call Gemini API
            response = self.model.generate_content(
                [SYSTEM_PROMPT, user_prompt],
                generation_config=self.generation_config
            )

            # Parse JSON response
            result = json.loads(response.text)

            # Validate response structure
            if not self._validate_response(result):
                logger.warning(f"Invalid ADK response structure for: {news_item.get('title', 'Unknown')}")
                return None

            # Merge ADK enrichment with original news
            enriched = {**news_item, **result}

            # If not kept, return None
            if not result.get('keep', False):
                logger.debug(f"News discarded by ADK: {news_item.get('title', 'Unknown')}")
                return None

            logger.info(
                f"News scored: {news_item.get('title', 'Unknown')[:50]}... "
                f"| Severity: {result.get('severity')} | Score: {result.get('relevance_score')}"
            )

            return enriched

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in ADK response: {e}")
            logger.debug(f"Response text: {response.text if 'response' in locals() else 'N/A'}")
            return None
        except Exception as e:
            logger.error(f"Error scoring news with ADK: {e}")
            return None

    def score_batch(self, news_items: list[Dict]) -> list[Dict]:
        """
        Score multiple news items

        Args:
            news_items: List of news items

        Returns:
            List of enriched news items (only kept items)
        """
        enriched_items = []

        for item in news_items:
            result = self.score(item)
            if result:
                enriched_items.append(result)

        logger.info(
            f"Batch scoring complete: {len(news_items)} input, "
            f"{len(enriched_items)} kept ({len(enriched_items)/len(news_items)*100:.1f}%)"
        )

        return enriched_items

    def _validate_response(self, response: Dict) -> bool:
        """
        Validate ADK response structure

        Args:
            response: ADK response dict

        Returns:
            True if valid, False otherwise
        """
        required_fields = ['keep', 'tags', 'area', 'summary', 'relevance_score']

        for field in required_fields:
            if field not in response:
                logger.warning(f"Missing required field in ADK response: {field}")
                return False

        # If keep=true, severity must be present
        if response.get('keep') and 'severity' not in response:
            logger.warning("keep=true but severity is missing")
            return False

        # Validate severity values
        if response.get('severity'):
            valid_severities = ['low', 'medium', 'high', 'critical']
            if response['severity'] not in valid_severities:
                logger.warning(f"Invalid severity value: {response['severity']}")
                return False

        # Validate score range
        score = response.get('relevance_score', 0)
        if not (0 <= score <= 1):
            logger.warning(f"Invalid relevance_score: {score} (must be 0-1)")
            return False

        return True

    def get_stats(self) -> Dict:
        """Get scorer statistics"""
        return {
            'model': self.model_name,
            'project': self.project_id,
            'location': self.location
        }


class MockADKScorer:
    """
    Mock ADK Scorer for testing without Vertex AI credentials
    Always returns sample classification results
    """

    def __init__(self, *args, **kwargs):
        logger.warning("Using MockADKScorer - for testing only!")

    def score(self, news_item: Dict) -> Optional[Dict]:
        """Mock scoring - returns sample data"""
        # Simple heuristic for mock: check if title contains mobility keywords
        title_lower = news_item.get('title', '').lower()
        body_lower = news_item.get('body', '').lower()

        mobility_keywords = [
            'metro', 'bus', 'tranvía', 'cable', 'tráfico', 'vía', 'cierre',
            'desvío', 'accidente', 'movilidad', 'transporte', 'pico y placa'
        ]

        is_relevant = any(keyword in title_lower or keyword in body_lower
                         for keyword in mobility_keywords)

        if not is_relevant:
            return None

        # Return mock enrichment
        return {
            **news_item,
            'keep': True,
            'severity': 'medium',
            'tags': ['mock', 'test'],
            'area': 'Mock Area',
            'entities': ['Mock Entity'],
            'summary': 'Mock summary for testing',
            'relevance_score': 0.75,
            'reasoning': 'Mock reasoning (testing mode)'
        }

    def score_batch(self, news_items: list[Dict]) -> list[Dict]:
        """Mock batch scoring"""
        return [result for result in (self.score(item) for item in news_items) if result]

    def get_stats(self) -> Dict:
        return {'model': 'mock', 'mode': 'testing'}
