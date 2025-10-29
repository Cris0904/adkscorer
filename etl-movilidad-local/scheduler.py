"""
Scheduler for ETL Movilidad Medellín
Runs the pipeline automatically every 20 minutes
"""
import os
import sys
import time
import logging
from datetime import datetime
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


def run_pipeline():
    """Run the ETL pipeline"""
    try:
        logger.info("="*60)
        logger.info("Starting scheduled pipeline execution")
        logger.info("="*60)

        # Add src to path for imports
        src_path = os.path.join(os.path.dirname(__file__), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        # Import and run the pipeline
        from main import main

        # Run the pipeline
        main()

        logger.info("Pipeline execution completed successfully")
        return True

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}", exc_info=True)
        return False


def main():
    """Main scheduler loop"""
    logger.info("="*60)
    logger.info("ETL MOVILIDAD SCHEDULER STARTED")
    logger.info("="*60)
    logger.info("Configuration:")
    logger.info(f"  - Interval: Every 20 minutes")
    logger.info(f"  - Database: {'Supabase' if os.getenv('USE_SUPABASE', 'false').lower() == 'true' else 'SQLite'}")
    logger.info(f"  - Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)

    # Run immediately on startup
    logger.info("\nRunning initial pipeline execution...")
    run_pipeline()

    # Then run every 20 minutes
    interval_seconds = 20 * 60  # 20 minutes
    execution_count = 1

    logger.info(f"\nScheduler active. Will run every {interval_seconds // 60} minutes.")
    logger.info("Press Ctrl+C to stop.\n")

    try:
        while True:
            # Wait for 20 minutes
            logger.info(f"Waiting {interval_seconds // 60} minutes until next execution...")
            logger.info(f"Next execution at: {datetime.fromtimestamp(time.time() + interval_seconds).strftime('%Y-%m-%d %H:%M:%S')}")

            time.sleep(interval_seconds)

            # Run the pipeline
            execution_count += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"Execution #{execution_count}")
            logger.info(f"{'='*60}")

            run_pipeline()

    except KeyboardInterrupt:
        logger.info("\n" + "="*60)
        logger.info("Scheduler stopped by user")
        logger.info(f"Total executions: {execution_count}")
        logger.info("="*60)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Create logs directory
    os.makedirs("logs", exist_ok=True)

    main()
