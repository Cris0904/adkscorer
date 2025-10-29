"""
ADK Scorer v2 - Using modern Google Generative AI SDK (October 2025+)
Replaces deprecated vertexai SDK with google-generativeai
"""
import json
import os
from typing import Dict, Optional
import logging
import google.generativeai as genai
from prompts.system_prompt import SYSTEM_PROMPT, build_user_prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ADKScorerV2:
    """
    Modern ADK-based news scorer using Google Generative AI SDK
    Compatible with October 2025+ API
    """

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        model_name: str = "models/gemini-2.5-flash"
    ):
        """
        Initialize ADK Scorer V2

        Args:
            project_id: Google Cloud project ID
            location: Vertex AI location (default: us-central1)
            model_name: Gemini model to use (default: gemini-1.5-flash)
        """
        self.project_id = project_id
        self.location = location
        self.model_name = model_name

        # Configure Generative AI SDK
        try:
            # Set API key from environment or use application default credentials
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                logger.info(f"Configured with API key")
            else:
                # Use application default credentials (gcloud auth)
                genai.configure()
                logger.info(f"Configured with application default credentials")

            # Initialize model with safer settings
            from google.generativeai.types import HarmCategory, HarmBlockThreshold

            self.model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={
                    "temperature": 0.2,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 2048
                },
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            )
            logger.info(f"Initialized Generative AI model: {model_name}")

        except Exception as e:
            logger.error(f"Error initializing Generative AI: {e}")
            raise

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

            # Combine system and user prompts - Add explicit JSON instruction
            full_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}\n\nResponde ÚNICAMENTE con un objeto JSON válido, sin texto adicional antes o después."

            # Call Gemini API
            response = self.model.generate_content(full_prompt)

            # Check if response was blocked
            if not response.candidates or not response.candidates[0].content.parts:
                logger.warning(f"Response blocked or empty for: {news_item.get('title', 'Unknown')}")
                return None

            # Get response text
            response_text = response.text.strip()

            # Try to extract JSON if wrapped in markdown
            if response_text.startswith('```'):
                # Remove markdown code blocks
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            # Parse JSON response
            result = json.loads(response_text)

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
            'location': self.location,
            'sdk_version': 'google-generativeai (modern)'
        }
