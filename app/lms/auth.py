"""LMS authentication: login and logout."""

import logging

from playwright.async_api import TimeoutError as PlaywrightTimeout

from config.settings import LMS_URL, LMS_USERNAME, LMS_PASSWORD
from app.lms.browser import execute
from app.lms.selectors import (
    USERNAME_INPUT,
    PASSWORD_INPUT,
    LOGIN_BUTTON,
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

    async def _do_login(page):
        # Navigate to login page
        try:
            await page.goto(
                f"{LMS_URL}/login/index.php",
                wait_until="domcontentloaded",
                timeout=15000,
            )
        except PlaywrightTimeout:
            logger.warning("Timeout navigating to login page")
            await page.goto(
                f"{LMS_URL}/login/index.php",
                wait_until="domcontentloaded",
                timeout=30000,
            )

        # Wait for potential JS redirects (Moodle redirects already-logged-in users)
        await page.wait_for_timeout(3000)

        # If we're no longer on the login page, we're already logged in
        current = page.url
        if not current.startswith(f"{LMS_URL}/login/"):
            logger.info(f"Already logged in (at {current})")
            return True

        # Check if the actual login form is present (not a redirect interstitial)
        try:
            await page.wait_for_selector(USERNAME_INPUT, timeout=15000)
        except PlaywrightTimeout:
            # After waiting, check URL again in case a delayed redirect happened
            current = page.url
            if not current.startswith(f"{LMS_URL}/login/"):
                logger.info(f"Already logged in after delayed redirect (at {current})")
                return True
            logger.error("Login form not found — page structure may have changed")
            return False

        # Fill and submit
        try:
            await page.fill(USERNAME_INPUT, username, timeout=10000)
            await page.fill(PASSWORD_INPUT, password, timeout=10000)
        except Exception as e:
            logger.error(f"Failed to fill login form: {e}")
            return False

        try:
            async with page.expect_navigation(wait_until="domcontentloaded", timeout=30000):
                await page.click(LOGIN_BUTTON)
        except PlaywrightTimeout:
            logger.warning("Navigation timeout after login click")

        # Check result
        if page.url.startswith(f"{LMS_URL}/login/"):
            try:
                error_el = await page.query_selector("div.alert-danger")
                if error_el:
                    logger.error(f"Login failed: {await error_el.inner_text()}")
                else:
                    logger.error("Login failed: still on login page")
            except Exception:
                logger.error("Login failed: still on login page")
            return False

        logger.info(f"Login successful, redirected to: {page.url}")
        return True

    return await execute(_do_login)


async def logout():
    """Log out from the LMS."""
    async def _do_logout(page):
        try:
            await page.goto(
                f"{LMS_URL}/login/logout.php",
                wait_until="domcontentloaded",
                timeout=15000,
            )
            await page.wait_for_timeout(2000)
            logger.info("Logged out successfully")
        except Exception as e:
            logger.warning(f"Error during logout: {e}")

    try:
        await execute(_do_logout)
    except Exception as e:
        logger.warning(f"Logout execution error: {e}")


async def is_logged_in() -> bool:
    """Check if currently logged in."""
    async def _check(page):
        try:
            await page.goto(
                f"{LMS_URL}/my/",
                wait_until="domcontentloaded",
                timeout=15000,
            )
            await page.wait_for_timeout(2000)
            return "login" not in page.url.lower()
        except Exception:
            return False

    try:
        return await execute(_check)
    except Exception:
        return False
