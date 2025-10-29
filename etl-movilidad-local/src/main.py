"""
Main ETL Pipeline for Movilidad Medellín
Orchestrates extraction, scoring, storage, and alerts
"""
import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

# Import modules
from extractors_apify_simple import HybridApifyExtractor as NewsExtractor
from adk_scorer_v3 import ADKScorerV3
from adk_scorer import MockADKScorer  # Keep mock for testing
from alert_manager import AlertManager, ConsoleOnlyAlertManager

# Database imports - support both SQLite and Supabase
try:
    from db_supabase import SupabaseNewsDatabase
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

from db import NewsDatabase as SQLiteDatabase

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/etl_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ETLPipeline:
    """
    Complete ETL Pipeline for Movilidad Medellín news

    Flow:
    1. Extract news from multiple sources
    2. Deduplicate based on URL hash
    3. Score with ADK (Google Gemini)
    4. Filter relevant news (keep=true)
    5. Save to database
    6. Send alerts for high/critical severity
    7. Log execution statistics
    """

    def __init__(
        self,
        project_id: str = None,
        use_mock_adk: bool = False,
        enable_email_alerts: bool = False,
        use_supabase: bool = False
    ):
        """
        Initialize ETL Pipeline

        Args:
            project_id: Google Cloud project ID for Vertex AI
            use_mock_adk: Use mock ADK for testing (no API calls)
            enable_email_alerts: Enable email alerts
            use_supabase: Use Supabase instead of SQLite (default: False)
        """
        logger.info("Initializing ETL Pipeline...")

        # Initialize database
        if use_supabase:
            if not SUPABASE_AVAILABLE:
                raise ImportError(
                    "Supabase not available. Install with: pip install supabase"
                )
            logger.info("Using Supabase database")
            self.db = SupabaseNewsDatabase()
        else:
            logger.info("Using SQLite database")
            self.db = SQLiteDatabase()

        # Initialize extractor
        self.extractor = NewsExtractor()

        # Initialize ADK scorer
        if use_mock_adk:
            logger.warning("Using MockADKScorer - for testing only!")
            self.scorer = MockADKScorer()
        else:
            if not project_id:
                raise ValueError("project_id required when not using mock ADK")
            self.scorer = ADKScorerV3(
                project_id=project_id,
                location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
                model_name=os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            )

        # Initialize alert manager
        if enable_email_alerts:
            self.alert_manager = AlertManager(
                email_enabled=True,
                smtp_host=os.getenv("SMTP_HOST"),
                smtp_port=int(os.getenv("SMTP_PORT", "587")),
                smtp_user=os.getenv("SMTP_USER"),
                smtp_password=os.getenv("SMTP_PASSWORD"),
                alert_recipients=os.getenv("ALERT_RECIPIENTS", "").split(","),
                console_alerts=True,
                file_alerts=True
            )
        else:
            self.alert_manager = ConsoleOnlyAlertManager()

        logger.info("ETL Pipeline initialized successfully")

    def run(self) -> Dict:
        """
        Run complete ETL pipeline

        Returns:
            Dict with execution statistics
        """
        start_time = time.time()
        stats = {
            'extracted': 0,
            'deduplicated': 0,
            'scored': 0,
            'kept': 0,
            'discarded': 0,
            'alerted': 0,
            'errors': []
        }

        logger.info("="*60)
        logger.info("Starting ETL Pipeline execution")
        logger.info("="*60)

        try:
            # STEP 1: Extract
            logger.info("STEP 1: Extracting news from sources...")
            raw_news = self.extractor.extract_all()
            stats['extracted'] = len(raw_news)
            logger.info(f"✓ Extracted {stats['extracted']} news items")

            if stats['extracted'] == 0:
                logger.warning("No news extracted. Pipeline complete.")
                return stats

            # STEP 2: Deduplicate
            logger.info("STEP 2: Deduplicating news...")
            unique_news = []
            for news in raw_news:
                if not self.db.is_duplicate(news['url']):
                    unique_news.append(news)
                else:
                    stats['deduplicated'] += 1

            logger.info(
                f"✓ Deduplicated: {stats['deduplicated']} duplicates found, "
                f"{len(unique_news)} unique items"
            )

            if len(unique_news) == 0:
                logger.info("No new unique news. Pipeline complete.")
                return stats

            # STEP 3: Score with ADK
            logger.info("STEP 3: Scoring news with ADK...")
            scored_news = []
            for news in unique_news:
                try:
                    result = self.scorer.score(news)
                    stats['scored'] += 1

                    if result:
                        scored_news.append(result)
                        stats['kept'] += 1
                    else:
                        stats['discarded'] += 1

                except Exception as e:
                    logger.error(f"Error scoring news: {e}")
                    stats['errors'].append(str(e))

            logger.info(
                f"✓ Scored {stats['scored']} items: "
                f"{stats['kept']} kept, {stats['discarded']} discarded"
            )

            if len(scored_news) == 0:
                logger.info("No relevant news found. Pipeline complete.")
                return stats

            # STEP 4: Save to database
            logger.info("STEP 4: Saving to database...")
            saved_count = 0
            for news in scored_news:
                news_id = self.db.insert_news(news)
                if news_id:
                    saved_count += 1
                    # Add ID for alert tracking
                    news['id'] = news_id

            logger.info(f"✓ Saved {saved_count} news items to database")

            # STEP 5: Send alerts
            logger.info("STEP 5: Sending alerts for high severity news...")
            high_severity = [
                n for n in scored_news
                if n.get('severity') in ['high', 'critical']
            ]

            if high_severity:
                for news in high_severity:
                    if self.alert_manager.send_alert(news):
                        stats['alerted'] += 1
                        # Mark as alerted in DB
                        if 'id' in news:
                            self.db.mark_as_alerted(news['id'])

                logger.info(f"✓ Sent {stats['alerted']} alerts")
            else:
                logger.info("✓ No high severity news to alert")

        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            stats['errors'].append(str(e))
            raise

        finally:
            # Calculate duration
            duration = time.time() - start_time
            stats['duration'] = duration

            # Log execution stats
            self.db.log_execution(stats)

            # Print summary
            logger.info("="*60)
            logger.info("ETL Pipeline execution complete")
            logger.info(f"Duration: {duration:.2f} seconds")
            logger.info(f"Stats: {stats}")
            logger.info("="*60)

        return stats

    def get_stats(self) -> Dict:
        """Get pipeline and database statistics"""
        db_stats = self.db.get_stats()
        scorer_stats = self.scorer.get_stats()

        return {
            'database': db_stats,
            'scorer': scorer_stats
        }


def main():
    """Main entry point"""
    # Load environment variables
    load_dotenv()

    # Get configuration from environment
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    use_mock = os.getenv("USE_MOCK_ADK", "false").lower() == "true"
    enable_email = os.getenv("ENABLE_EMAIL_ALERTS", "false").lower() == "true"
    use_supabase = os.getenv("USE_SUPABASE", "false").lower() == "true"

    # Validate configuration
    if not use_mock and not project_id:
        logger.error(
            "GOOGLE_CLOUD_PROJECT environment variable required. "
            "Set USE_MOCK_ADK=true for testing without credentials."
        )
        sys.exit(1)

    # Create logs directory
    os.makedirs("logs", exist_ok=True)

    # Log database choice
    if use_supabase:
        logger.info("Database: Supabase (cloud)")
    else:
        logger.info("Database: SQLite (local)")

    # Initialize and run pipeline
    try:
        pipeline = ETLPipeline(
            project_id=project_id,
            use_mock_adk=use_mock,
            enable_email_alerts=enable_email,
            use_supabase=use_supabase
        )

        stats = pipeline.run()

        # Print summary
        print("\n" + "="*60)
        print("PIPELINE EXECUTION SUMMARY")
        print("="*60)
        print(f"Extracted:      {stats['extracted']}")
        print(f"Deduplicated:   {stats['deduplicated']}")
        print(f"Scored:         {stats['scored']}")
        print(f"Kept:           {stats['kept']}")
        print(f"Discarded:      {stats['discarded']}")
        print(f"Alerted:        {stats['alerted']}")
        print(f"Duration:       {stats['duration']:.2f}s")
        if stats['errors']:
            print(f"Errors:         {len(stats['errors'])}")
        print("="*60 + "\n")

    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
