"""Pipeline: download → extract text → solve → generate document for assignment 130712."""
import asyncio
import logging
import os
import sys
import shutil
import time
from pathlib import Path
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    stream=sys.stderr,
)

TESTING_DIR = Path("testing")
TESTING_DIR.mkdir(exist_ok=True)

ASSIGNMENT_ID = "130712"


def _load_env():
    from dotenv import load_dotenv
    load_dotenv()
    try:
        with open(".env") as f:
            for line in f:
                line = line.strip()
                if line.startswith("LMS_PASSWORD=") and not line.startswith("#"):
                    raw_val = line.split("=", 1)[1]
                    if len(raw_val) >= 2 and raw_val[0] == raw_val[-1] and raw_val[0] in ('"', "'"):
                        raw_val = raw_val[1:-1]
                    raw_val = raw_val.replace("$$", "$").replace("\\$", "$")
                    if "$" in raw_val and "$" not in (os.getenv("LMS_PASSWORD") or ""):
                        os.environ["LMS_PASSWORD"] = raw_val
                    break
    except FileNotFoundError:
        pass


def extract_pdf_text(pdf_path: str) -> str:
    """Extract text from a PDF file using pypdf."""
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf_path)
        text = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text.append(t)
        return "\n".join(text)
    except Exception as e:
        print(f"  ⚠️  PDF extraction failed: {e}")
        return ""


async def main():
    _load_env()

    from app.lms.browser import get_browser, close_browser
    from app.lms.auth import login
    from app.lms.assignments import get_assignment, download_attachment
    from app.ai.solver import solve_assignment
    from app.documents.generator import generate_docx

    print("=" * 70)
    print(f"SOLVE PIPELINE — Assignment {ASSIGNMENT_ID}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    browser = await get_browser()
    await browser.start(headless=True)

    try:
        # Step 1: Login
        print("\n[1/5] Logging into LMS...")
        success = await login()
        if not success:
            print("  ❌ Login failed")
            return
        print("  ✅ Logged in")

        # Step 2: Get assignment details
        print(f"\n[2/5] Fetching details for assignment {ASSIGNMENT_ID}...")
        details = await get_assignment(ASSIGNMENT_ID)
        title = details.get("title") or "sdgfsdfsdf"
        course = details.get("course") or "UCS3411-DL-CSE-C-26"
        intro = details.get("intro") or ""
        attachments = details.get("attachments") or []

        print(f"  Title: {title}")
        print(f"  Course: {course}")
        print(f"  Description: {len(intro)} chars")
        if intro:
            print(f"  Description preview: {intro[:200]}...")
        print(f"  Attachments: {len(attachments)}")

        # Step 3: Download attachment(s)
        assignment_context = intro  # start with LMS description text
        print(f"\n[3/5] Downloading attachment(s)...")
        downloaded_paths = []
        for i, att in enumerate(attachments):
            url = att.get("url", "")
            name = att.get("name", f"attachment_{i}")
            print(f"  [{i+1}] {name}")
            try:
                path = await download_attachment(ASSIGNMENT_ID, url)
                downloaded_paths.append(path)
                testing_att = TESTING_DIR / path.name
                shutil.copy2(str(path), str(testing_att))
                print(f"      ✅ Downloaded → {testing_att}")

                # Try to extract text if it's a PDF
                if path.suffix.lower() == ".pdf":
                    print(f"      📖 Extracting text from PDF...")
                    pdf_text = extract_pdf_text(str(path))
                    if pdf_text:
                        print(f"         Extracted {len(pdf_text)} chars")
                        assignment_context += f"\n\n--- Assignment PDF Content ---\n{pdf_text}"
                    else:
                        print(f"         No text extracted (scanned PDF?)")

            except Exception as e:
                print(f"      ⚠️  Failed: {e}")

        # Step 4: Solve using AI
        print(f"\n[4/5] Solving assignment with AI...")
        print(f"  Context length: {len(assignment_context)} chars")

        if not assignment_context.strip():
            print("  ⚠️  No description or PDF text available. Using title only.")
            assignment_context = title

        # Try solving with retry on quota error
        solution = None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                solution = solve_assignment(
                    title=title,
                    description=assignment_context[:10000],  # limit context
                    assignment_type="document",
                )
                break
            except Exception as e:
                err_str = str(e)
                if "RESOURCE_EXHAUSTED" in err_str or "429" in err_str:
                    wait = 60 * (attempt + 1)
                    print(f"  ⏳ Quota exceeded. Waiting {wait}s (attempt {attempt+1}/{max_retries})...")
                    time.sleep(wait)
                else:
                    print(f"  ❌ AI error: {e}")
                    raise

        if solution is None:
            print("  ❌ Failed to generate solution after retries")
            return

        print(f"  ✅ Solution generated ({len(solution)} chars)")

        # Preview
        lines = solution.split("\n")
        print(f"\n  ── Preview (first 15 lines) ──")
        for line in lines[:15]:
            truncated = line[:100]
            print(f"  {truncated}")
        if len(lines) > 15:
            print(f"  ... ({len(lines) - 15} more lines)")
        print(f"  ────────────────────────────")

        # Step 5: Generate DOCX
        print(f"\n[5/5] Generating DOCX document...")
        docx_path = generate_docx(ASSIGNMENT_ID, title, course, solution)

        testing_name = f"Ex1_DDL_{ASSIGNMENT_ID}.docx"
        testing_path = TESTING_DIR / testing_name
        shutil.copy2(str(docx_path), str(testing_path))
        print(f"  ✅ DOCX → {testing_path}")

        # Also save solution markdown
        md_path = TESTING_DIR / f"Ex1_DDL_{ASSIGNMENT_ID}_solution.md"
        md_path.write_text(
            f"# {title}\n\n"
            f"**Course:** {course}\n"
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            f"---\n\n{solution}"
        )
        print(f"  ✅ Markdown → {md_path}")

        print("\n" + "=" * 70)
        print("DONE — All files saved to testing/ folder")
        print("=" * 70)
        print(f"  📄 {testing_path}")
        print(f"  📄 {md_path}")
        for p in downloaded_paths:
            f = TESTING_DIR / p.name
            if f.exists():
                print(f"  📎 {f}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await close_browser()
        print("\nBrowser closed.")


asyncio.run(main())
