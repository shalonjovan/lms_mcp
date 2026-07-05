"""Assignment upload and submission."""

import logging
from pathlib import Path

from config.settings import LMS_URL
from app.lms.browser import get_page

logger = logging.getLogger(__name__)


async def upload_submission(assignment_id: str, file_path: str | Path) -> bool:
    """Upload a file to the assignment submission page.

    Navigates to the edit-submission page and uses the file picker to upload.

    Returns:
        True if upload was successful.
    """
    page = await get_page()
    url = f"{LMS_URL}/mod/assign/view.php?id={assignment_id}&action=editsubmission"
    await page.goto(url, wait_until="networkidle")

    # Check if there's a file picker area
    file_picker = await page.query_selector("div[data-fieldtype='filepicker']")
    if file_picker:
        # Click "Add" button in the file picker
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
    await page.wait_for_timeout(2000)  # Wait for upload to process

    logger.info(f"Uploaded {file_path} to assignment {assignment_id}")
    return True


async def submit_assignment(assignment_id: str) -> bool:
    """Submit the assignment after upload.

    Returns:
        True if submission was confirmed.
    """
    page = await get_page()
    url = f"{LMS_URL}/mod/assign/view.php?id={assignment_id}&action=editsubmission"
    await page.goto(url, wait_until="networkidle")

    # Look for the submit button
    submit_btn = await page.query_selector("button#id-submitbutton")
    if not submit_btn:
        logger.warning(f"No submit button found for assignment {assignment_id}")
        return False

    # Click submit
    async with page.expect_navigation(wait_until="networkidle", timeout=30000):
        await submit_btn.click()

    logger.info(f"Assignment {assignment_id} submitted successfully")
    return True


async def get_submission_status(assignment_id: str) -> str:
    """Check the submission status of an assignment.

    Returns:
        Status string: 'submitted', 'not submitted', 'graded', or the raw text.
    """
    page = await get_page()
    url = f"{LMS_URL}/mod/assign/view.php?id={assignment_id}"
    await page.goto(url, wait_until="networkidle")

    status_el = await page.query_selector("div[data-region='submission-status']")
    if status_el:
        return (await status_el.inner_text()).strip()

    return "unknown"
