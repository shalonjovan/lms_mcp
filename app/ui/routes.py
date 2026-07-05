"""FastAPI routes for the web dashboard."""

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)

from app.database.repository import (
    get_all_assignments,
    get_assignment,
    get_all_courses,
    get_history,
    save_assignment,
    save_submission,
    update_assignment_status,
    update_assignment_type,
    log_history,
)
from app.lms.assignments import list_assignments, get_assignment as lms_get_assignment
from app.lms.auth import login, logout, is_logged_in
from app.lms.submission import upload_submission, submit_assignment, get_submission_status
from app.ai.classifier import classify_assignment
from app.ai.solver import solve_assignment
from app.documents.generator import generate_docx, generate_pdf
from app.scheduler.monitor import check_now

router = APIRouter()
_jinja_env = Environment(
    loader=FileSystemLoader("app/ui/templates"),
    autoescape=True,
)
_dash_template = _jinja_env.get_template("dashboard.html")


@router.get("/", response_class=HTMLResponse)
async def dashboard():
    assignments = get_all_assignments()
    courses = get_all_courses()
    new_count = sum(1 for a in assignments if a.get("status") == "new")
    solved_count = sum(1 for a in assignments if a.get("status") == "solved")
    html = _dash_template.render(
        assignments=assignments,
        courses=courses,
        new_count=new_count,
        solved_count=solved_count,
    )
    return HTMLResponse(html)


@router.post("/api/login")
async def api_login():
    try:
        result = await login()
        return {"success": result}
    except Exception as e:
        logger.exception("Login failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/logout")
async def api_logout():
    try:
        await logout()
        return {"success": True}
    except Exception as e:
        logger.exception("Logout failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/login-status")
async def api_login_status():
    try:
        logged_in = await is_logged_in()
        return {"logged_in": logged_in}
    except Exception:
        return {"logged_in": False}


@router.get("/api/assignments")
async def api_list_assignments(live: bool = False):
    if live:
        try:
            await login()
            lms_assignments = await list_assignments()
            for a in lms_assignments:
                save_assignment(a["id"], a)
            return {"assignments": lms_assignments}
        except Exception as e:
            logger.exception("Failed to fetch live assignments via query param")
            raise HTTPException(status_code=500, detail=str(e))
    return {"assignments": get_all_assignments()}


@router.get("/api/assignments/live")
async def api_list_assignments_live():
    try:
        await login()
        assignments = await list_assignments()
        for a in assignments:
            save_assignment(a["id"], a)
        return {"assignments": assignments}
    except Exception as e:
        logger.exception("Failed to fetch live assignments")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/assignments/unsubmitted")
async def api_unsubmitted():
    try:
        await login()
        assignments = get_all_assignments()
        unsubmitted = []
        for a in assignments:
            try:
                status = await get_submission_status(a["assignment_id"])
                if "submitted" not in status.lower():
                    unsubmitted.append({**a, "submission_status": status})
            except Exception as e2:
                logger.warning(f"Failed to check submission for {a['assignment_id']}: {e2}")
                unsubmitted.append({**a, "submission_status": "unknown"})
        return {"assignments": unsubmitted}
    except Exception as e:
        logger.exception("Failed to check unsubmitted assignments")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/assignments/{assignment_id}")
async def api_get_assignment(assignment_id: str, live: bool = False):
    if live:
        try:
            await login()
            details = await lms_get_assignment(assignment_id)
            return {"assignment": details}
        except Exception as e:
            logger.exception(f"Failed to fetch live assignment {assignment_id}")
            raise HTTPException(status_code=500, detail=str(e))
    db_assign = get_assignment(assignment_id)
    if not db_assign:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return {"assignment": db_assign}


@router.post("/api/assignments/{assignment_id}/classify")
async def api_classify(assignment_id: str):
    assign = get_assignment(assignment_id)
    if not assign:
        raise HTTPException(status_code=404, detail="Assignment not found")
    a_type = classify_assignment(assign["title"], assign.get("description") or "")
    update_assignment_type(assignment_id, a_type)
    log_history(assignment_id, "classify", f"Type: {a_type}")
    return {"assignment_id": assignment_id, "type": a_type}


@router.post("/api/assignments/{assignment_id}/solve")
async def api_solve(assignment_id: str):
    assign = get_assignment(assignment_id)
    if not assign:
        raise HTTPException(status_code=404, detail="Assignment not found")
    a_type = assign.get("assignment_type")
    if not a_type:
        a_type = classify_assignment(assign["title"], assign.get("description") or "")
        update_assignment_type(assignment_id, a_type)
    solution = solve_assignment(assign["title"], assign.get("description") or "", a_type)
    update_assignment_status(assignment_id, "solved")
    log_history(assignment_id, "solve", "AI solution generated")
    return {"assignment_id": assignment_id, "solution": solution, "type": a_type}


@router.post("/api/assignments/{assignment_id}/document")
async def api_generate_document(assignment_id: str, fmt: str = "docx"):
    assign = get_assignment(assignment_id)
    if not assign:
        raise HTTPException(status_code=404, detail="Assignment not found")
    solution = assign.get("description", "")
    if fmt == "pdf":
        path = generate_pdf(assignment_id, assign["title"], assign.get("course_name", ""), solution)
    else:
        path = generate_docx(assignment_id, assign["title"], assign.get("course_name", ""), solution)
    log_history(assignment_id, "generate_doc", f"Generated {fmt}: {path.name}")
    return {"path": str(path), "filename": path.name}


@router.post("/api/assignments/{assignment_id}/submit")
async def api_submit(assignment_id: str, fmt: str = "docx"):
    assign = get_assignment(assignment_id)
    if not assign:
        raise HTTPException(status_code=404, detail="Assignment not found")

    try:
        # 1. Classify
        a_type = assign.get("assignment_type")
        if not a_type:
            a_type = classify_assignment(assign["title"], assign.get("description") or "")
            update_assignment_type(assignment_id, a_type)

        # 2. Solve
        solution = solve_assignment(assign["title"], assign.get("description") or "", a_type)
        update_assignment_status(assignment_id, "solved")

        # 3. Generate document
        doc_path = generate_docx(assignment_id, assign["title"], assign.get("course_name", ""), solution)

        # 4. Upload to LMS
        await login()
        uploaded = await upload_submission(assignment_id, doc_path)
        if not uploaded:
            raise HTTPException(status_code=500, detail="Upload to LMS failed")

        # 5. Submit
        submitted = await submit_assignment(assignment_id)

        # Save to DB
        save_submission(
            assignment_id, solution, str(doc_path), "docx",
            "submitted" if submitted else "uploaded",
        )
        update_assignment_status(assignment_id, "submitted")
        log_history(assignment_id, "submit", f"Document submitted: {doc_path.name}")

        return {
            "success": submitted,
            "assignment_id": assignment_id,
            "document": str(doc_path),
            "submitted": submitted,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Submit failed for {assignment_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/submissions/{assignment_id}/download")
async def api_download(assignment_id: str, fmt: str = "docx"):
    from config.settings import GENERATED_DIR
    files = list(GENERATED_DIR.glob(f"{assignment_id}_*.{fmt}"))
    if not files:
        raise HTTPException(status_code=404, detail="No generated document found")
    latest = max(files, key=lambda p: p.stat().st_mtime)
    return FileResponse(str(latest), filename=latest.name)


@router.post("/api/check-now")
async def api_check_now():
    try:
        await login()
        await check_now()
        return {"status": "completed"}
    except Exception as e:
        logger.exception("check-now failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/history")
async def api_history(assignment_id: str | None = None):
    return {"history": get_history(assignment_id)}


@router.get("/api/status")
async def api_status():
    return {
        "status": "running",
        "logged_in": False,
    }
