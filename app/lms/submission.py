"""Assignment upload and submission."""

import logging
from pathlib import Path

from config.settings import LMS_URL
from app.lms.browser import execute

logger = logging.getLogger(__name__)


async def upload_submission(assignment_id: str, file_path: str | Path) -> bool:
    """Upload a file to the assignment submission page."""
    async def _upload(page):
        url = f"{LMS_URL}/mod/assign/view.php?id={assignment_id}&action=editsubmission"
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)

        # Check for file picker area
        file_picker = await page.query_selector("div[data-fieldtype='filepicker']")
        if file_picker:
            add_btn = await page.query_selector("input[value='Add']")
            if add_btn:
                await add_btn.click()
                await page.wait_for_timeout(1000)

        # Use file input to upload directly
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
