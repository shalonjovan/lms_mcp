"""FastAPI routes for the web dashboard."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from jinja2 import Environment, FileSystemLoader

from app.database.repository import (
    get_all_assignments,
    get_assignment,
    get_all_courses,
    get_history,
)
from app.lms.assignments import list_assignments, get_assignment as lms_get_assignment
from app.lms.auth import login, logout, is_logged_in
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


@router.get("/api/assignments")
async def api_list_assignments(live: bool = False):
    if live:
        try:
            await login()
            lms_assignments = await list_assignments()
            return {"assignments": lms_assignments}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    return {"assignments": get_all_assignments()}


@router.get("/api/assignments/{assignment_id}")
async def api_get_assignment(assignment_id: str, live: bool = False):
    if live:
        try:
            await login()
            details = await lms_get_assignment(assignment_id)
            return {"assignment": details}
        except Exception as e:
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
    a_type = classify_assignment(assign["title"], assign["description"] or "")
    from app.database.repository import update_assignment_type
    update_assignment_type(assignment_id, a_type)
    return {"assignment_id": assignment_id, "type": a_type}


@router.post("/api/assignments/{assignment_id}/solve")
async def api_solve(assignment_id: str):
    assign = get_assignment(assignment_id)
    if not assign:
        raise HTTPException(status_code=404, detail="Assignment not found")
    solution = solve_assignment(assign["title"], assign["description"] or "")
    return {"assignment_id": assignment_id, "solution": solution}


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
    return {"path": str(path), "filename": path.name}


@router.get("/api/submissions/{assignment_id}/download")
async def api_download(assignment_id: str, fmt: str = "docx"):
    from config.settings import GENERATED_DIR
    from pathlib import Path
    # Find most recent generated file for this assignment
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
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/history")
async def api_history(assignment_id: str | None = None):
    return {"history": get_history(assignment_id)}


@router.get("/api/status")
async def api_status():
    return {
        "status": "running",
        "logged_in": False,  # Will be checked in real implementation
    }
