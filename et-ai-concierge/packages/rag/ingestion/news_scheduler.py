"""
News Scheduler - Schedule periodic ET article scraping without blocking main app
Uses APScheduler to run scraping jobs in background
"""
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

logger = logging.getLogger(__name__)

# Global state
_scheduler: Optional[BackgroundScheduler] = None
_last_run_info: Dict[str, Any] = {
    "status": "never",
    "articles_count": 0,
    "errors": [],
    "started_at": None,
    "completed_at": None,
    "duration_seconds": None,
}
_last_triggered_at: Optional[datetime] = None  # Track when job was last triggered
_scheduled_hour: int = 20
_scheduled_minute: int = 0


def init_scheduler(hour: int = 20, minute: int = 0) -> BackgroundScheduler:
    """
    Initialize the background scheduler for ET scraping.
    Runs daily at specified time in IST timezone.
    Includes fallback trigger within 15 minutes grace period.
    """
    global _scheduler, _scheduled_hour, _scheduled_minute
    
    _scheduled_hour = hour
    _scheduled_minute = minute
    
    if _scheduler and _scheduler.running:
        logger.warning("⚠️ Scheduler already running. Returning existing instance.")
        return _scheduler

    _scheduler = BackgroundScheduler()

    # Use IST timezone explicitly (Asia/Kolkata is IST)
    ist = pytz.timezone('Asia/Kolkata')

    # Primary: Daily scheduled job at exact time
    _scheduler.add_job(
        run_scrape_job,
        trigger=CronTrigger(hour=hour, minute=minute, timezone=ist),
        id="et_daily_scrape",
        name="ET Daily Article Scrape",
        replace_existing=True,
    )

    # Fallback: Check every minute if we're in the 15-minute grace window and job hasn't run
    _scheduler.add_job(
        _check_and_trigger_if_missed,
        trigger=CronTrigger(minute='*', timezone=ist),  # Every minute
        id="et_scrape_grace_check",
        name="ET Scrape Grace Period Check",
        replace_existing=True,
    )

    logger.info(
        f"📅 Scheduled daily ET scrape at {hour:02d}:{minute:02d} IST (Asia/Kolkata timezone)"
    )
    logger.info(f"⏱️ Grace period: 15 minutes (will trigger between {hour:02d}:{minute:02d} - {(hour if minute + 15 < 60 else hour + 1) % 24:02d}:{(minute + 15) % 60:02d} IST)")

    _scheduler.start()
    logger.info("✅ News scheduler started with grace period fallback")

    return _scheduler


def _check_and_trigger_if_missed():
    """
    Check if we're within 15 minutes of scheduled time and job hasn't run yet.
    If so, trigger the scrape job.
    """
    global _last_triggered_at
    
    ist = pytz.timezone('Asia/Kolkata')
    now_ist = datetime.now(ist)
    current_hour = now_ist.hour
    current_minute = now_ist.minute
    
    # Calculate scheduled time in IST
    scheduled_time = now_ist.replace(hour=_scheduled_hour, minute=_scheduled_minute, second=0, microsecond=0)
    
    # Check if within 15 minute grace window
    time_diff = (now_ist - scheduled_time).total_seconds() / 60  # Difference in minutes
    
    # If within 15 minutes AFTER scheduled time and job hasn't been triggered in this window
    if 0 <= time_diff <= 15:
        if _last_triggered_at is None or (now_ist - _last_triggered_at).total_seconds() / 60 > 16:
            logger.info(f"⏰ Grace period trigger activated (within {time_diff:.1f} min of scheduled time)")
            _last_triggered_at = now_ist
            run_scrape_job()  # Trigger the scrape job


def stop_scheduler():
    """Stop the scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown()
        _scheduler = None
        logger.info("🛑 News scheduler stopped")


def run_scrape_job():
    """
    Execute the scraping pipeline:
    1. Scrape ET articles
    2. Check for duplicates
    3. Generate embeddings
    4. Store in Qdrant
    """
    import time
    from et_scraper import scrape_et_articles
    from ingest import ingest_et_articles, check_duplicate

    global _last_run_info, _last_triggered_at
    
    # Set timestamp to prevent grace period from triggering again
    ist = pytz.timezone('Asia/Kolkata')
    _last_triggered_at = datetime.now(ist)

    _last_run_info["started_at"] = datetime.utcnow().isoformat()
    _last_run_info["status"] = "in_progress"

    start_time = time.time()
    errors = []

    try:
        logger.info("=" * 60)
        logger.info("🔄 [SCHEDULED JOB] Starting ET article scrape...")

        # Scrape articles
        articles = scrape_et_articles(max_articles=100)
        logger.info(f"📦 Scraped {len(articles)} articles")

        if not articles:
            logger.warning("⚠️ No articles scraped")
            _last_run_info["status"] = "completed_no_articles"
            _last_run_info["articles_count"] = 0
            return

        # Check for duplicates
        new_articles = []
        duplicates_count = 0

        for article in articles:
            if not check_duplicate(article["content_hash"]):
                new_articles.append(article)
            else:
                duplicates_count += 1

        logger.info(f"✅ Deduplication: {len(new_articles)} new, {duplicates_count} duplicates")

        # Ingest new articles
        if new_articles:
            ingest_et_articles(new_articles)
            logger.info(f"✅ Ingested {len(new_articles)} articles to RAG")
        else:
            logger.info("ℹ️ No new articles to ingest")

        _last_run_info["articles_count"] = len(new_articles)
        _last_run_info["status"] = "completed_success"

    except Exception as e:
        error_msg = f"❌ Scrape job failed: {str(e)}"
        logger.exception(error_msg)
        errors.append(error_msg)
        _last_run_info["status"] = "completed_error"

    finally:
        duration = time.time() - start_time
        _last_run_info["duration_seconds"] = round(duration, 2)
        _last_run_info["completed_at"] = datetime.utcnow().isoformat()
        _last_run_info["errors"] = errors

        logger.info(f"✅ Job completed in {duration:.2f}s")
        logger.info("=" * 60)


def trigger_scrape_now() -> Dict[str, Any]:
    """
    Manually trigger a scrape job (for admin API).
    Returns job ID and status.
    """
    global _scheduler

    if not _scheduler or not _scheduler.running:
        return {
            "status": "error",
            "message": "Scheduler is not running",
            "job_id": None,
        }

    try:
        job = _scheduler.add_job(
            run_scrape_job,
            id=f"et_manual_scrape_{datetime.utcnow().timestamp()}",
            replace_existing=False,
        )
        logger.info(f"✅ Manual scrape triggered (Job ID: {job.id})")
        return {
            "status": "queued",
            "message": "Scrape job queued for immediate execution",
            "job_id": job.id,
        }
    except Exception as e:
        logger.error(f"❌ Failed to trigger scrape: {e}")
        return {
            "status": "error",
            "message": str(e),
            "job_id": None,
        }


def get_scrape_status() -> Dict[str, Any]:
    """Get status of last scrape run (for admin API)."""
    return {
        "last_run": _last_run_info.copy(),
        "scheduler_running": _scheduler.running if _scheduler else False,
    }

