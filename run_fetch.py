"""Fetch all pending assignments from the LMS dashboard."""
import asyncio
import logging
import os
import sys
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    stream=sys.stderr,
)

def _load_env_manual():
    """Load env vars but handle password $ escaping that dotenv mangled."""
    from dotenv import load_dotenv
    load_dotenv()

    # Re-read password from .env directly since dotenv eats the $
    try:
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if line.startswith("LMS_PASSWORD=") and not line.startswith("#"):
                    raw_val = line.split("=", 1)[1]
                    # Strip any surrounding quotes
                    if len(raw_val) >= 2 and raw_val[0] == raw_val[-1] and raw_val[0] in ('"', "'"):
                        raw_val = raw_val[1:-1]
                    # Replace $$ and \$ with $ (in case dotenv's $$ escaping was used)
                    raw_val = raw_val.replace("$$", "$").replace("\\$", "$")
                    if "$" in raw_val and "$" not in (os.getenv("LMS_PASSWORD") or ""):
                        os.environ["LMS_PASSWORD"] = raw_val
                        print(f"  [fix] Applied password from manual parse ({len(raw_val)} chars)")
                    break
    except FileNotFoundError:
        pass

async def main():
    _load_env_manual()

    from app.lms.browser import get_browser, close_browser
    from app.lms.auth import login
    from app.lms.assignments import list_assignments, get_assignment

    import os
    print(f"LMS_URL: {os.getenv('LMS_URL')}")
    print(f"LMS_USERNAME: {os.getenv('LMS_USERNAME')}")
    print(f"LMS_PASSWORD set: {'yes' if os.getenv('LMS_PASSWORD') else 'no'}")
    pwd = os.getenv('LMS_PASSWORD', '')
    print(f"LMS_PASSWORD length: {len(pwd)}")
    print()

    print("=" * 70)
    print("LMS ASSIGNMENT FETCHER")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    browser = await get_browser()
    page = await browser.start(headless=True)

    try:
        print("\n[1/3] Logging into LMS...")
        success = await login()
        if not success:
            print("  ❌ Login failed")
            await page.screenshot(path="debug_login_fail.png", full_page=True)
            print(f"  Current URL: {page.url}")
            return
        print("  ✅ Logged in successfully")

        print("\n[2/3] Fetching assignments from dashboard...")
        assignments = await list_assignments()
        print(f"  Found {len(assignments)} assignment(s) on dashboard\n")

        if not assignments:
            print("  No assignments found on the dashboard.")
            await page.screenshot(path="debug_dashboard.png", full_page=True)
            return

        print("[3/3] Fetching details for each assignment...")
        pending = []
        submitted = []

        for i, a in enumerate(assignments, 1):
            print(f"\n  [{i}/{len(assignments)}] ID: {a['id']} — {a['title']}")
            try:
                details = await get_assignment(a['id'])
                status = details.get('submission_status', 'unknown').strip()
                due = details.get('due_date', 'N/A').strip()[:80] if details.get('due_date') else 'N/A'
                course = details.get('course', 'N/A')
                attachments = details.get('attachments', [])
                has_attachments = f"{len(attachments)} file(s)" if attachments else "None"

                print(f"      Course: {course}")
                print(f"      Due: {due}")
                print(f"      Status: {status}")
                print(f"      Attachments: {has_attachments}")

                if 'submitted' in status.lower() or 'submitted for grading' in status.lower():
                    submitted.append(a)
                else:
                    pending.append({**a, "details": details})
            except Exception as e:
                print(f"      ⚠️  Error: {e}")

        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"\n📌 PENDING ASSIGNMENTS (not yet submitted): {len(pending)}")
        for p in pending:
            d = p.get("details", {})
            print(f"    • [{p['id']}] {p['title']}")
            print(f"      Course: {d.get('course', 'N/A')}")
            print(f"      Due: {str(d.get('due_date', 'N/A'))[:80]}")
            print()

        print(f"✅ Already submitted: {len(submitted)}")
        for s in submitted:
            print(f"    • [{s['id']}] {s['title']}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_browser()
        print("\nBrowser closed.")

asyncio.run(main())
