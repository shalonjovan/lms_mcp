"""Periodic assignment monitoring using APScheduler."""

import asyncio
import logging
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from config.settings import POLL_INTERVAL_MINUTES
from app.lms.auth import login
from app.lms.assignments import list_assignments, get_assignment
from app.database.repository import save_assignment, get_all_assignments
from app.notifications.notifier import notify_new_assignment

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None
_new_assignment_callbacks = []


def on_new_assignment(callback):
    """Register a callback to be called when a new assignment is detected."""
    _new_assignment_callbacks.append(callback)


async def _check_for_new_assignments():
    """Poll the LMS dashboard and save any new assignments."""
    try:
        await login()
        assignments = await list_assignments()
        for assign in assignments:
            is_new = save_assignment(assign["id"], assign)
            if is_new:
                logger.info(f"New assignment detected: {assign['title']}")
                # Fetch full details
                try:
                    details = await get_assignment(assign["id"])
                    save_assignment(assign["id"], details)
                    notify_new_assignment(details)
                except Exception as e:
                    logger.warning(f"Could not fetch details for {assign['id']}: {e}")
                    notify_new_assignment(assign)

                for cb in _new_assignment_callbacks:
                    try:
                        cb(assign)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
    except Exception as e:
        logger.error(f"Error checking assignments: {e}")


async def start_monitoring():
    """Start the periodic assignment monitor."""
    global _scheduler
    if _scheduler and _scheduler.running:
        return

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        _check_for_new_assignments,
        "interval",
        minutes=POLL_INTERVAL_MINUTES,
        id="check_assignments",
        next_run_time=datetime.now(),  # Run immediately on start
    )
    _scheduler.start()
    logger.info(f"Assignment monitoring started (every {POLL_INTERVAL_MINUTES} min)")


async def stop_monitoring():
    """Stop the assignment monitor."""
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Assignment monitoring stopped")


async def check_now():
    """Manually trigger a check."""
    await _check_for_new_assignments()
