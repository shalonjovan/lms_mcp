"""Playwright browser manager for LMS interaction."""

import asyncio
import re
from contextlib import asynccontextmanager
from typing import Optional, Callable, Awaitable, TypeVar

from playwright.async_api import async_playwright, Browser, Page, Playwright

T = TypeVar("T")


class BrowserManager:
    """Manages a Playwright browser instance for LMS automation."""

    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
        self._lock = asyncio.Lock()

    async def start(self, headless: bool = True) -> Page:
        """Launch browser and return a new page."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=headless,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = await self._browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )

        # Block unnecessary resources to speed things up
        await context.route(
            re.compile(r"\.(png|jpg|jpeg|gif|svg|webp|woff|woff2|ttf|eot)($|\?)"),
            lambda route: route.abort(),
        )

        self._page = await context.new_page()
        return self._page

    async def page(self) -> Page:
        """Get the current page, starting a new session if needed."""
        if self._page is None or self._page.is_closed():
            return await self.start()
        return self._page

    async def close(self):
        """Close browser and clean up."""
        if self._page and not self._page.is_closed():
            await self._page.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._page = None
        self._browser = None
        self._playwright = None

    async def screenshot(self, path: str = "debug.png"):
        """Take a screenshot for debugging."""
        page = await self.page()
        await page.screenshot(path=path, full_page=True)

    @asynccontextmanager
    async def use(self):
        """Acquire exclusive access to the browser page.

        Usage:
            mgr = await get_browser()
            async with mgr.use() as page:
                await page.goto(...)
        """
        async with self._lock:
            page = await self.page()
            yield page

    async def execute(self, fn: Callable[[Page], Awaitable[T]]) -> T:
        """Run a function with exclusive page access."""
        async with self._lock:
            page = await self.page()
            return await fn(page)


# Global singleton
_browser_manager: Optional[BrowserManager] = None


async def get_browser() -> BrowserManager:
    """Get or create the global browser manager."""
    global _browser_manager
    if _browser_manager is None:
        _browser_manager = BrowserManager()
    return _browser_manager


async def close_browser():
    """Close the global browser manager."""
    global _browser_manager
    if _browser_manager:
        await _browser_manager.close()
        _browser_manager = None


async def get_page() -> Page:
    """Convenience: get a page from the global browser."""
    mgr = await get_browser()
    return await mgr.page()


async def execute(fn: Callable[[Page], Awaitable[T]]) -> T:
    """Run a function with exclusive access to the browser page.

    This is the recommended way to interact with the browser.
    It ensures no two operations run concurrently on the same page.
    """
    mgr = await get_browser()
    return await mgr.execute(fn)
