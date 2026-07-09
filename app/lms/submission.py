"""Assignment upload and submission."""

import logging
from pathlib import Path

from config.settings import LMS_URL
from app.lms.browser import execute

logger = logging.getLogger(__name__)


async def check_submission_open(assignment_id: str) -> dict:
    """Check if the submission window for an assignment is currently open.

    Navigates to the read-only assignment view and inspects action buttons,
    submission status, and time remaining indicators.

    Returns:
        dict with keys: open (bool), status (str), time_remaining (str),
        has_action_buttons (bool), available_actions (list), details (str)
    """
    async def _check(page):
        url = f"{LMS_URL}/mod/assign/view.php?id={assignment_id}"
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)

        result = {
            "assignment_id": assignment_id,
            "open": False,
            "status": "",
            "time_remaining": "",
            "has_action_buttons": False,
            "available_actions": [],
            "details": "",
        }

        status_table = await page.query_selector("div.submissionstatustable")
        if status_table:
            rows = await status_table.query_selector_all("tr")
            for row in rows:
                th = await row.query_selector("th")
                td = await row.query_selector("td")
                if th and td:
                    key = (await th.inner_text()).strip().lower()
                    val = (await td.inner_text()).strip()
                    if "status" in key and "grade" not in key:
                        result["status"] = val
                    elif "time" in key or "remaining" in key:
                        result["time_remaining"] = val

        dates_el = await page.query_selector("div[data-region='activity-dates']")
        if dates_el:
            result["details"] = (await dates_el.inner_text()).strip()

        container = await page.query_selector("div.container-fluid.mb-4")
        if container:
            row = await container.query_selector("div.row")
            if row:
                buttons = await row.query_selector_all("button, a.btn")
                if buttons:
                    result["has_action_buttons"] = True
                    for btn in buttons:
                        text = (await btn.inner_text()).strip()
                        if text:
                            result["available_actions"].append(text)

        closed_keywords = ["closed", "overdue", "past due", "not open", "not accepting"]
        time_remaining_lower = result["time_remaining"].lower()

        if result["has_action_buttons"]:
            result["open"] = True
        elif any(k in time_remaining_lower for k in closed_keywords):
            result["open"] = False
        elif "opens:" in result["details"].lower():
            result["open"] = False
        elif not result["status"]:
            result["open"] = False
        elif "no submissions" in result["status"].lower() and "remaining" in time_remaining_lower:
            result["open"] = True

        return result

    return await execute(_check)


async def upload_submission(assignment_id: str, file_path: str | Path) -> bool:
    """Upload a file to the assignment submission page."""
    status = await check_submission_open(assignment_id)
    if not status["open"]:
        logger.warning(
            f"Cannot upload to assignment {assignment_id}: "
            f"submission window closed. Status: {status['status']}"
        )
        return False

    async def _upload(page):
        url = f"{LMS_URL}/mod/assign/view.php?id={assignment_id}&action=editsubmission"
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)

        file_picker = await page.query_selector("div[data-fieldtype='filepicker']")
        if file_picker:
            add_btn = await page.query_selector("input[value='Add']")
            if add_btn:
                await add_btn.click()
                await page.wait_for_timeout(1000)

        file_input = await page.query_selector("input[type='file']")
        if not file_input:
            logger.error("No file input found on submission page")
            return False

        await file_input.set_input_files(str(file_path))
        await page.wait_for_timeout(2000)

        logger.info(f"Uploaded {file_path} to assignment {assignment_id}")
        return True

    return await execute(_upload)


async def submit_assignment(assignment_id: str) -> bool:
    """Submit the assignment after upload."""
    status = await check_submission_open(assignment_id)
    if not status["open"]:
        logger.warning(
            f"Cannot submit assignment {assignment_id}: "
            f"submission window closed. Status: {status['status']}"
        )
        return False

    async def _submit(page):
        url = f"{LMS_URL}/mod/assign/view.php?id={assignment_id}&action=editsubmission"
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)

        submit_btn = await page.query_selector("button#id-submitbutton")
        if not submit_btn:
            logger.warning(f"No submit button found for assignment {assignment_id}")
            return False

        async with page.expect_navigation(wait_until="domcontentloaded", timeout=30000):
            await submit_btn.click()

        logger.info(f"Assignment {assignment_id} submitted successfully")
        return True

    return await execute(_submit)


async def get_submission_status(assignment_id: str) -> str:
    """Check the submission status of an assignment."""
    async def _check(page):
        url = f"{LMS_URL}/mod/assign/view.php?id={assignment_id}"
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)

        status_table = await page.query_selector("div.submissionstatustable")
        if status_table:
            status_cell = await status_table.query_selector("td[class*='submissionstatus']")
            if status_cell:
                return (await status_cell.inner_text()).strip()

        status_el = await page.query_selector("div[data-region='submission-status']")
        if status_el:
            return (await status_el.inner_text()).strip()

        return "unknown"

    return await execute(_check)
