"""LMS authentication: login and logout."""

import logging

from playwright.async_api import Page, expect

from config.settings import LMS_URL, LMS_USERNAME, LMS_PASSWORD
from app.lms.browser import get_page
from app.lms.selectors import (
    LOGIN_FORM,
    USERNAME_INPUT,
    PASSWORD_INPUT,
    LOGIN_TOKEN,
    LOGIN_BUTTON,
    LOGOUT_LINK,
)

logger = logging.getLogger(__name__)


async def login(
    username: str | None = None,
    password: str | None = None,
) -> bool:
    """Log in to the LMS. Returns True if successful."""
    username = username or LMS_USERNAME
    password = password or LMS_PASSWORD

    if not username or not password:
        raise ValueError("LMS credentials not configured. Set LMS_USERNAME and LMS_PASSWORD.")

    page = await get_page()
    await page.goto(f"{LMS_URL}/login/index.php", wait_until="networkidle")

    # Bail if already logged in (redirected away from login page)
    if not page.url.startswith(f"{LMS_URL}/login/"):
        logger.info("Already logged in")
        return True

    # Fill login form
    await page.fill(USERNAME_INPUT, username)
    await page.fill(PASSWORD_INPUT, password)

    # Submit
    async with page.expect_navigation(wait_until="networkidle", timeout=30000):
        await page.click(LOGIN_BUTTON)

    # Check success: login page should redirect to dashboard
    if page.url.startswith(f"{LMS_URL}/login/"):
        # Check for error message
        error = await page.query_selector("div.alert-danger")
        if error:
            text = await error.inner_text()
            logger.error(f"Login failed: {text}")
            return False
        logger.error("Login failed: still on login page")
        return False

    logger.info(f"Login successful, redirected to: {page.url}")
    return True


async def logout():
    """Log out from the LMS."""
    page = await get_page()
    try:
        await page.goto(f"{LMS_URL}/login/logout.php", wait_until="networkidle")
        logger.info("Logged out successfully")
    except Exception as e:
        logger.warning(f"Error during logout: {e}")


async def is_logged_in() -> bool:
    """Check if currently logged in by visiting dashboard."""
    page = await get_page()
    try:
        await page.goto(f"{LMS_URL}/my/", wait_until="networkidle", timeout=15000)
        return "login" not in page.url.lower()
    except Exception:
        return False
