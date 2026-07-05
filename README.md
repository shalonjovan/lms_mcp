# LMS MCP Assistant

AI-powered LMS assistant that monitors assignments, generates solutions, creates formatted submission documents, and submits with user approval.

Built for **SSN College of Engineering LMS** (Moodle-based).

## Architecture

```
LMS (Moodle)  ←→  Playwright  ←→  MCP Server  ←→  AI Agent
                                      ↕
                          FastAPI Web Dashboard
                                      ↕
                              SQLite Database
```

## Quick Start

```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Install Playwright browser
playwright install chromium

# Configure credentials
cp .env .env.local   # Edit with your LMS credentials & AI API keys
```

## Commands

| Command | What it does |
|---|---|
| `python -m app.main mcp` | Run MCP server (stdio) — connect AI agent |
| `python -m app.main web` | Run web dashboard at http://127.0.0.1:8080 |
| `python -m app.main all` | Run MCP server + web UI + scheduler |
| `python -m app.main init-db` | Initialize/reset the database |

## MCP Tools (12 tools)

| Tool | Description |
|---|---|
| `login()` | Log in to LMS |
| `logout()` | Log out |
| `list_assignments()` | List all visible assignments |
| `get_assignment(id)` | Get full assignment details |
| `download_attachment(id, url, filename?)` | Download attachment file |
| `classify_assignment(id)` | AI classify (doc/programming/handwritten/etc) |
| `solve_assignment(id)` | AI generate solution |
| `generate_document(id, fmt='docx')` | Create formatted DOCX/PDF |
| `upload_submission(id, file_path)` | Upload file to LMS |
| `submit_assignment(id)` | Submit assignment |
| `get_submission_status(id)` | Check submission status |

## Project Structure

```
lms_mcp/
├── app/
│   ├── mcp/           # MCP server + tool registrations
│   │   ├── server.py  # FastMCP setup, tool decorators
│   │   └── tools.py   # Tool implementations
│   ├── lms/           # Playwright LMS automation
│   │   ├── auth.py    # Login/logout
│   │   ├── browser.py # Browser lifecycle management
│   │   ├── assignments.py  # List, get, download
│   │   ├── submission.py   # Upload, submit, status
│   │   └── selectors.py    # Moodle CSS selectors
│   ├── ai/            # LLM integration
│   │   ├── client.py      # Anthropic/OpenAI abstraction
│   │   ├── classifier.py  # Assignment type classification
│   │   └── solver.py      # Solution generation
│   ├── documents/     # Document generation
│   │   ├── generator.py   # DOCX and PDF generation
│   │   └── templates.py   # Document templates
│   ├── database/      # SQLite persistence
│   │   ├── models.py      # Schema
│   │   └── repository.py  # CRUD operations
│   ├── notifications/ # User notifications
│   │   └── notifier.py
│   ├── scheduler/     # Periodic monitoring
│   │   └── monitor.py     # APScheduler
│   ├── ui/            # Web dashboard
│   │   ├── app.py         # FastAPI app
│   │   ├── routes.py      # API endpoints
│   │   └── templates/     # Jinja2 templates
│   └── main.py        # Entry point
├── config/
│   └── settings.py    # Configuration
├── data/              # SQLite database
├── generated/         # Output documents
└── site_files/        # Reference HTML snapshots
```

## Workflow

1. **Monitor** → Scheduler polls LMS for new assignments
2. **Notify** → New assignments are detected and saved
3. **Classify** → AI determines assignment type
4. **Solve** → AI generates solution content
5. **Document** → Generate formatted DOCX/PDF with student info
6. **Review** → User previews/edits/regenerates (via tools)
7. **Submit** → Upload + submit on LMS (user-approved only)

## Environment Variables (`.env`)

```
LMS_URL=https://lms.ssn.edu.in
LMS_USERNAME=your_email@ssn.edu.in
LMS_PASSWORD=your_password
ANTHROPIC_API_KEY=sk-ant-...
STUDENT_NAME=Your Name
STUDENT_REG_NO=2410112
```
