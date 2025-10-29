"""
Scheduler for ETL Movilidad Medellín
Runs pipeline automatically at specified intervals
"""
import os
import sys
import time
import signal
import logging
import schedule
from datetime import datetime
from dotenv import load_dotenv
from main import ETLPipeline

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ETLScheduler:
    """
    Automated scheduler for ETL pipeline
    Runs pipeline at configurable intervals
    """

    def __init__(
        self,
        project_id: str = None,
        interval_minutes: int = 5,
        use_mock_adk: bool = False,
        enable_email_alerts: bool = False
    ):
        """
        Initialize ETL Scheduler

        Args:
            project_id: Google Cloud project ID
            interval_minutes: Run interval in minutes (default: 5)
            use_mock_adk: Use mock ADK for testing
            enable_email_alerts: Enable email alerts
        """
        self.project_id = project_id
        self.interval_minutes = interval_minutes
        self.use_mock_adk = use_mock_adk
        self.enable_email_alerts = enable_email_alerts
        self.running = True

        # Initialize pipeline
        self.pipeline = ETLPipeline(
            project_id=project_id,
            use_mock_adk=use_mock_adk,
            enable_email_alerts=enable_email_alerts
        )

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        logger.info(f"Scheduler initialized: interval={interval_minutes} minutes")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}. Shutting down gracefully...")
        self.running = False

    def run_pipeline_job(self):
        """Job to run pipeline (called by scheduler)"""
        logger.info("="*60)
        logger.info(f"Scheduled pipeline execution started at {datetime.now()}")
        logger.info("="*60)

        try:
            stats = self.pipeline.run()

            # Log summary
            logger.info("Scheduled execution complete")
            logger.info(f"Summary: {stats}")

        except Exception as e:
            logger.error(f"Error in scheduled execution: {e}")

        logger.info(f"Next execution in {self.interval_minutes} minutes")

    def start(self):
        """Start the scheduler"""
        logger.info("="*60)
        logger.info("ETL Scheduler Starting")
        logger.info("="*60)
        logger.info(f"Interval: Every {self.interval_minutes} minutes")
        logger.info(f"Mock ADK: {self.use_mock_adk}")
        logger.info(f"Email Alerts: {self.enable_email_alerts}")
        logger.info("Press Ctrl+C to stop")
        logger.info("="*60)

        # Schedule the job
        schedule.every(self.interval_minutes).minutes.do(self.run_pipeline_job)

        # Run immediately on start
        logger.info("Running initial pipeline execution...")
        self.run_pipeline_job()

        # Main scheduler loop
        logger.info("\nScheduler running. Waiting for next execution...")
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(5)

        logger.info("Scheduler stopped")

    def run_once_now(self):
        """Run pipeline once immediately (for testing)"""
        logger.info("Running pipeline once (manual trigger)")
        self.run_pipeline_job()


def main():
    """Main entry point for scheduler"""
    # Load environment variables
    load_dotenv()

    # Get configuration
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    interval_minutes = int(os.getenv("SCHEDULE_INTERVAL_MINUTES", "5"))
    use_mock = os.getenv("USE_MOCK_ADK", "false").lower() == "true"
    enable_email = os.getenv("ENABLE_EMAIL_ALERTS", "false").lower() == "true"

    # Validate configuration
    if not use_mock and not project_id:
        logger.error(
            "GOOGLE_CLOUD_PROJECT environment variable required. "
            "Set USE_MOCK_ADK=true for testing without credentials."
        )
        sys.exit(1)

    # Create logs directory
    os.makedirs("logs", exist_ok=True)

    # Initialize and start scheduler
    try:
        scheduler = ETLScheduler(
            project_id=project_id,
            interval_minutes=interval_minutes,
            use_mock_adk=use_mock,
            enable_email_alerts=enable_email
        )

        scheduler.start()

    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
