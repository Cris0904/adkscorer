"""
Advanced Scheduler for ETL Movilidad Medellín
Uses the 'schedule' library for more flexible scheduling
"""
import os
import sys
import time
import logging
import schedule
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

# Execution counter
execution_count = 0


def run_pipeline():
    """Run the ETL pipeline"""
    global execution_count
    execution_count += 1

    try:
        logger.info("="*60)
        logger.info(f"Pipeline Execution #{execution_count}")
        logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*60)

        # Add src to path for imports
        src_path = os.path.join(os.path.dirname(__file__), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        # Import and run the pipeline
        from main import main

        # Run the pipeline
        main()

        logger.info(f"Execution #{execution_count} completed successfully")
        logger.info(f"Next run scheduled in 20 minutes")
        logger.info("")

        return True

    except Exception as e:
        logger.error(f"Execution #{execution_count} failed: {e}", exc_info=True)
        logger.info("Will retry in 20 minutes")
        logger.info("")
        return False


def main():
    """Main scheduler"""
    logger.info("="*60)
    logger.info("ETL MOVILIDAD ADVANCED SCHEDULER")
    logger.info("="*60)
    logger.info("Configuration:")
    logger.info(f"  - Interval: Every 20 minutes")
    logger.info(f"  - Database: {'Supabase' if os.getenv('USE_SUPABASE', 'false').lower() == 'true' else 'SQLite'}")
    logger.info(f"  - Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*60)
    logger.info("")

    # Schedule the job
    schedule.every(20).minutes.do(run_pipeline)

    # Run immediately on startup
    logger.info("Running initial execution...")
    run_pipeline()

    logger.info("Scheduler is now active. Press Ctrl+C to stop.")
    logger.info("")

    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)  # Check every second

    except KeyboardInterrupt:
        logger.info("")
        logger.info("="*60)
        logger.info("Scheduler stopped by user")
        logger.info(f"Total executions: {execution_count}")
        logger.info(f"Stopped at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*60)
        sys.exit(0)
    except Exception as e:
        logger.error(f"Scheduler error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Create logs directory
    os.makedirs("logs", exist_ok=True)

    main()
