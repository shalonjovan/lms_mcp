"""Assignment listing, detail retrieval, and attachment downloads."""

import logging
import re
from pathlib import Path

from config.settings import LMS_URL, GENERATED_DIR
from app.lms.browser import execute
from app.lms.selectors import (
    ASSIGNMENT_CARD,
    ASSIGNMENT_TITLE,
    ASSIGNMENT_INTRO,
    ATTACHMENT_LINKS,
    TIMELINE_EVENT_LINK,
)

logger = logging.getLogger(__name__)


async def list_assignments() -> list[dict]:
    """List all visible assignments from the dashboard timeline."""
    async def _list(page):
        await page.goto(
            f"{LMS_URL}/my/",
            wait_until="networkidle",
            timeout=30000,
        )

        # Wait for lazy-loaded dashboard cards to render
        try:
            await page.wait_for_selector(ASSIGNMENT_CARD, timeout=10000)
        except Exception:
            pass

        # Also give JS-rendered timeline a moment
        await page.wait_for_timeout(2000)

        assignments = []
        seen_ids = set()

        # Get assignments from dashboard cards
        try:
            cards = await page.query_selector_all(ASSIGNMENT_CARD)
        except Exception:
            cards = []

        for card in cards:
            href = await card.get_attribute("href") or ""
            if not href:
                continue

            match = re.search(r"id=(\d+)", href)
            if not match:
                continue
            assign_id = match.group(1)
            if assign_id in seen_ids:
                continue
            seen_ids.add(assign_id)

            title = (await card.get_attribute("title")) or ""
            if not title:
                title = (await card.inner_text()).strip()

            course = ""
            try:
                small_el = await card.query_selector("small.text-truncate")
                if small_el:
                    course = (await small_el.inner_text()).strip()
            except Exception:
                pass

            assignments.append({
                "id": assign_id,
                "title": title,
                "url": href if href.startswith("http") else f"{LMS_URL}{href}",
                "course": course,
                "due_date": "",
                "status": "unknown",
            })

        # Check timeline events for upcoming assignments
        try:
            timeline_links = await page.query_selector_all(TIMELINE_EVENT_LINK)
        except Exception:
            timeline_links = []

        for link in timeline_links:
            href = await link.get_attribute("href") or ""
            match = re.search(r"id=(\d+)", href)
            if not match:
                continue
            assign_id = match.group(1)
            if assign_id in seen_ids:
                continue
            seen_ids.add(assign_id)

            title = (await link.get_attribute("title") or "").replace(" is due", "")
            if not title:
                title = (await link.inner_text()).strip()

            assignments.append({
                "id": assign_id,
                "title": title,
                "url": href if href.startswith("http") else f"{LMS_URL}{href}",
                "course": "",
                "due_date": "",
                "status": "unknown",
            })

        return assignments

    return await execute(_list)


async def get_assignment(assignment_id: str) -> dict:
    """Get full details of a specific assignment."""
    async def _get(page):
        url = f"{LMS_URL}/mod/assign/view.php?id={assignment_id}"
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)

        result = {
            "id": assignment_id,
            "url": url,
            "title": "",
            "course": "",
            "intro": "",
            "intro_html": "",
            "due_date": "",
            "allowed_file_types": "",
            "attachments": [],
            "submission_status": "",
        }

        # Title
        try:
            title_el = await page.query_selector(ASSIGNMENT_TITLE)
            if title_el:
                result["title"] = (await title_el.inner_text()).strip()
        except Exception:
            pass

        # Introduction
        try:
            intro_el = await page.query_selector(ASSIGNMENT_INTRO)
            if intro_el:
                result["intro_html"] = await intro_el.inner_html()
                result["intro"] = await intro_el.inner_text()
        except Exception:
            pass

        # Course name from breadcrumb
        try:
            breadcrumb = await page.query_selector("ol.breadcrumb")
            if breadcrumb:
                crumbs = await breadcrumb.inner_text()
                lines = [l.strip() for l in crumbs.split("\n") if l.strip()]
                if len(lines) >= 2:
                    result["course"] = lines[-2]
        except Exception:
            pass

        # Attachments
        try:
            attachment_links = await page.query_selector_all(ATTACHMENT_LINKS)
            for att in attachment_links:
                href = await att.get_attribute("href") or ""
                text = (await att.inner_text()).strip() or href.split("/")[-1]
                full_url = href if href.startswith("http") else f"{LMS_URL}{href}"
                result["attachments"].append({"name": text, "url": full_url})
        except Exception:
            pass

        # Due date
        try:
            date_section = await page.query_selector("div[data-region='activity-dates']")
            if date_section:
                result["due_date"] = (await date_section.inner_text()).strip()
        except Exception:
            pass

        # Submission status
        try:
            status_table = await page.query_selector("div.submissionstatustable")
            if status_table:
                status_cell = await status_table.query_selector("td[class*='submissionstatus']")
                if status_cell:
                    result["submission_status"] = (await status_cell.inner_text()).strip()
            else:
                status_section = await page.query_selector("div[data-region='submission-status']")
                if status_section:
                    result["submission_status"] = (await status_section.inner_text()).strip()
        except Exception:
            pass

        return result

    return await execute(_get)


async def download_attachment(assignment_id: str, attachment_url: str, filename: str | None = None) -> Path:
    """Download an assignment attachment."""
    async def _download(page):
        out_dir = GENERATED_DIR / "assignments" / assignment_id
        out_dir.mkdir(parents=True, exist_ok=True)

        async with page.expect_download(timeout=30000) as download_info:
            await page.evaluate(
                """(url) => {
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = '';
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                }""",
                attachment_url,
            )

        download = await download_info.value
        suggested = download.suggested_filename
        save_path = out_dir / (filename or suggested)
        await download.save_as(str(save_path))

        logger.info(f"Downloaded attachment to {save_path}")
        return save_path

    return await execute(_download)
