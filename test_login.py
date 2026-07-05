"""Quick login test script — runs a headed browser so you can see what happens."""

import asyncio
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    stream=sys.stderr,
)


async def main():
    from dotenv import load_dotenv
    load_dotenv()

    from app.lms.browser import get_browser, close_browser
    from app.lms.auth import login, logout

    print("=" * 60)
    print("LMS LOGIN TEST")
    print("=" * 60)

    browser = await get_browser()
    page = await browser.start(headless=False)  # headed so you can see it

    try:
        print("\n[1/3] Navigating to LMS and logging in...")
        success = await login()
        print(f"  Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
        print(f"  Current URL: {page.url}")

        if success:
            print("\n[2/3] Taking screenshot...")
            await page.screenshot(path="test_login_success.png", full_page=True)
            print("  Saved to test_login_success.png")

            print("\n[3/3] Logging out...")
            await logout()
            print("  Done")
        else:
            # Take screenshot for debugging
            await page.screenshot(path="test_login_failed.png", full_page=True)
            print("  Saved debug screenshot to test_login_failed.png")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_browser()
        print("\nBrowser closed.")


asyncio.run(main())
