"""
ADK Scorer V3 - Using Google ADK (Agent Development Kit)
True ADK implementation with output_schema for structured responses
Replaces V2 which incorrectly used google-generativeai SDK
"""
import logging
import asyncio
import os
from typing import Dict, Optional
from google import genai
from google.adk.agents import LlmAgent
from google.adk.models import Gemini
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from schemas.scoring_schema import ScoringResponse
from prompts.system_prompt import SYSTEM_PROMPT, build_user_prompt

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ADKScorerV3:
    """
    True ADK-based news scorer using Google Agent Development Kit

    Key features:
    - Uses google.adk.agents.LlmAgent (NOT google.generativeai)
    - Enforces structured output via output_schema with Pydantic
    - Automatic JSON validation and error handling
    - Production-ready for mobility news classification
    """

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        model_name: str = "gemini-2.0-flash"
    ):
        """
        Initialize ADK Scorer V3 with Google ADK Agent

        Args:
            project_id: Google Cloud project ID
            location: Vertex AI location (default: us-central1)
            model_name: Gemini model to use (default: gemini-2.0-flash)
        """
        self.project_id = project_id
        self.location = location
        self.model_name = model_name

        # Create ADK components
        try:
            logger.info(f"Initializing Google ADK Agent...")

            # Create GenAI client configured for Vertex AI
            self.genai_client = genai.Client(
                vertexai=True,
                project=project_id,
                location=location
            )
            logger.info(f"   GenAI Client created for Vertex AI")

            # Create Gemini model configuration with the client
            model = Gemini(
                model=model_name,
                client=self.genai_client,  # Pass the configured client
                temperature=0.2,
                top_p=0.95,
                max_output_tokens=2048
            )

            # Create LLM Agent with output schema
            self.agent = LlmAgent(
                name="mobility_news_scorer",
                model=model,
                instruction=SYSTEM_PROMPT,
                output_schema=ScoringResponse,
                output_key="scoring_result"
            )

            # Create session service for ADK Runner
            self.session_service = InMemorySessionService()

            # Create Runner to execute the agent
            self.runner = Runner(
                agent=self.agent,
                app_name="mobility_scorer",
                session_service=self.session_service
            )

            logger.info(f"✅ ADK Agent initialized successfully")
            logger.info(f"   Model: {model_name}")
            logger.info(f"   Project: {project_id}")
            logger.info(f"   Location: {location}")
            logger.info(f"   Output schema: ScoringResponse (Pydantic validated)")

        except Exception as e:
            logger.error(f"❌ Error initializing ADK Agent: {e}")
            logger.error(f"   Make sure you have:")
            logger.error(f"   1. Installed google-adk: pip install google-adk")
            logger.error(f"   2. Set GOOGLE_CLOUD_PROJECT in .env")
            logger.error(f"   3. Authenticated: gcloud auth application-default login")
            raise

    async def _score_async(self, news_item: Dict, session_id: str) -> Optional[Dict]:
        """
        Internal async method to score news item

        Args:
            news_item: Dict with keys: source, title, body, published_at, url
            session_id: Session ID for the runner

        Returns:
            Enriched news item or None
        """
        # Create session first
        await self.session_service.create_session(
            app_name="mobility_scorer",
            user_id="scorer_user",
            session_id=session_id
        )

        # Build user prompt from news item
        user_prompt_text = build_user_prompt(news_item)

        logger.debug(f"Scoring: {news_item.get('title', 'Unknown')[:50]}...")

        # Create Content object for the message
        message_content = types.Content(
            role='user',
            parts=[types.Part(text=user_prompt_text)]
        )

        # Run the agent using Runner (returns async generator)
        response_generator = self.runner.run_async(
            user_id="scorer_user",
            session_id=session_id,
            new_message=message_content
        )

        # Iterate through the generator to get the final response
        final_response = None
        async for response in response_generator:
            final_response = response

        # Extract the agent response
        if not final_response:
            logger.warning(f"No response from ADK for: {news_item.get('title', 'Unknown')}")
            return None

        # Extract JSON from Event object's content
        if hasattr(final_response, 'content') and final_response.content:
            if hasattr(final_response.content, 'parts') and final_response.content.parts:
                # Get the text from the first part
                response_text = final_response.content.parts[0].text
                logger.debug(f"Extracted response text: {response_text[:200]}...")

                # Parse JSON and validate with Pydantic
                try:
                    import json
                    result_dict = json.loads(response_text)

                    # Validate with Pydantic model
                    scoring_result = ScoringResponse.model_validate(result_dict)

                    # Convert to dict
                    result = scoring_result.model_dump()

                    # Check if news should be kept
                    if not result.get('keep', False):
                        logger.debug(
                            f"News discarded: {news_item.get('title', 'Unknown')[:50]} "
                            f"| Reason: {result.get('reasoning', 'N/A')}"
                        )
                        return None

                    # Merge ADK enrichment with original news item
                    enriched = {**news_item, **result}

                    logger.info(
                        f"✅ News kept: {news_item.get('title', 'Unknown')[:50]}... "
                        f"| Severity: {result.get('severity')} "
                        f"| Score: {result.get('relevance_score'):.2f}"
                    )

                    return enriched

                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    logger.error(f"Response text: {response_text}")
                    return None
                except Exception as e:
                    logger.error(f"Validation error: {e}")
                    return None

        logger.warning(f"No scoring result in response for: {news_item.get('title', 'Unknown')}")
        return None

    def score(self, news_item: Dict) -> Optional[Dict]:
        """
        Score a news item using ADK Agent with structured output

        Args:
            news_item: Dict with keys: source, title, body, published_at, url

        Returns:
            Enriched news item with ADK scoring fields, or None if not relevant
        """
        try:
            # Generate unique session ID for this scoring request
            import uuid
            session_id = f"score_{uuid.uuid4().hex[:8]}"

            # Get or create event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Run async scoring in event loop
            return loop.run_until_complete(self._score_async(news_item, session_id))

        except Exception as e:
            logger.error(f"❌ Error scoring news with ADK Agent: {e}")
            logger.error(f"   News title: {news_item.get('title', 'Unknown')}")
            return None

    def score_batch(self, news_items: list[Dict]) -> list[Dict]:
        """
        Score multiple news items using ADK Agent

        Args:
            news_items: List of news items to score

        Returns:
            List of enriched news items (only items with keep=true)
        """
        logger.info(f"Starting batch scoring of {len(news_items)} news items...")

        enriched_items = []

        for i, item in enumerate(news_items, 1):
            logger.debug(f"Processing {i}/{len(news_items)}...")
            result = self.score(item)
            if result:
                enriched_items.append(result)

        kept_percentage = len(enriched_items) / len(news_items) * 100 if news_items else 0

        logger.info(
            f"✅ Batch scoring complete: "
            f"{len(news_items)} input → {len(enriched_items)} kept ({kept_percentage:.1f}%)"
        )

        return enriched_items

    def get_stats(self) -> Dict:
        """
        Get scorer statistics and configuration

        Returns:
            Dict with model info, configuration, and SDK version
        """
        return {
            'model': self.model_name,
            'project': self.project_id,
            'location': self.location,
            'sdk_version': 'google-adk (Agent Development Kit)',
            'agent_name': self.agent.name,
            'output_schema': 'ScoringResponse (Pydantic)',
            'framework': 'Google ADK v0.2+'
        }
