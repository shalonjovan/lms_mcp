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
cp .env.example .env   # Edit with your LMS credentials & AI API keys
```

## Commands

| Command | What it does |
|---|---|
| `python -m app.main mcp` | Run MCP server (stdio) — connect AI agent |
| `python -m app.main web` | Run web dashboard at http://127.0.0.1:8080 |
| `python -m app.main all` | Run web UI + scheduler (MCP SSE mounted at /mcp) |
| `python -m app.main init-db` | Initialize/reset the database |

## MCP Tools (12)

| Tool | Description |
|---|---|
| `login(username?, password?)` | Log in to LMS |
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
| `check_submission_open(id)` | Check if submission window is open |

## MCP Resources (5)

| Resource URI | Description |
|---|---|
| `lms://assignments` | All known assignments from DB |
| `lms://assignments/{id}` | Single assignment details |
| `lms://assignments/{id}/submission` | Latest submission status |
| `lms://history` | Recent activity log |
| `lms://status` | Server & LMS connection health |

## MCP Prompts (3)

| Prompt | Description |
|---|---|
| `solve_assignment_prompt(id)` | End-to-end solve workflow template |
| `classify_assignment_prompt(id)` | Classification workflow template |
| `review_submission(id)` | Pre-submit review checklist |

## Docker

```bash
docker build -t lms-mcp .
docker run -it --rm \
  -e LMS_USERNAME=your_email@ssn.edu.in \
  -e LMS_PASSWORD=your_password \
  -e AI_PROVIDER=google \
  -e GOOGLE_API_KEY=your_key \
  -v "$PWD/data:/app/data" \
  -v "$PWD/generated:/app/generated" \
  lms-mcp   # defaults to MCP stdio mode
```

## Environment Variables (`.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `LMS_URL` | No | `https://lms.ssn.edu.in` | LMS base URL |
| `LMS_USERNAME` | **Yes** | — | LMS login email |
| `LMS_PASSWORD` | **Yes** | — | LMS password |
| `AI_PROVIDER` | No | `google` | LLM provider: `google`, `anthropic`, `openai` |
| `GOOGLE_API_KEY` | Conditional | — | Required if `AI_PROVIDER=google` |
| `ANTHROPIC_API_KEY` | Conditional | — | Required if `AI_PROVIDER=anthropic` |
| `OPENAI_API_KEY` | Conditional | — | Required if `AI_PROVIDER=openai` |
| `STUDENT_NAME` | No | `Student Name` | Your full name |
| `STUDENT_REG_NO` | No | `Registration Number` | Your registration number |
| `STUDENT_DEPT` | No | `Department` | Your department |
| `STUDENT_YEAR` | No | `Year` | Your academic year |
| `DATABASE_PATH` | No | `data/lms_mcp.db` | SQLite database path |
| `GENERATED_DIR` | No | `generated` | Output directory |
| `POLL_INTERVAL_MINUTES` | No | `30` | Dashboard poll interval |
| `MCP_SERVER_HOST` | No | `127.0.0.1` | Web UI host |
| `MCP_SERVER_PORT` | No | `8080` | Web UI port |
| `LOG_LEVEL` | No | `INFO` | Log level: `DEBUG`, `INFO`, `WARNING` |

## Workflow

1. **Monitor** → Scheduler polls LMS for new assignments
2. **Notify** → New assignments are detected and saved
3. **Classify** → AI determines assignment type
4. **Solve** → AI generates solution content
5. **Document** → Generate formatted DOCX/PDF with student info
6. **Review** → User previews/edits/regenerates (via tools)
7. **Submit** → Upload + submit on LMS (user-approved only)

## Project Structure

```
lms_mcp/
├── app/
│   ├── mcp/             # MCP server + tool registrations
│   │   ├── server.py    # FastMCP setup, tool decorators
│   │   ├── tools.py     # Tool implementations
│   │   └── models.py    # Pydantic I/O models
│   ├── lms/             # Playwright LMS automation
│   │   ├── auth.py      # Login/logout
│   │   ├── browser.py   # Browser lifecycle management
│   │   ├── assignments.py   # List, get, download
│   │   ├── submission.py    # Upload, submit, status
│   │   └── selectors.py     # Moodle CSS selectors
│   ├── ai/              # LLM integration
│   │   ├── client.py        # Anthropic/OpenAI/Gemini abstraction
│   │   ├── classifier.py    # Assignment type classification
│   │   └── solver.py        # Solution generation
│   ├── documents/       # Document generation
│   │   ├── generator.py     # DOCX and PDF generation
│   │   └── templates.py     # Document templates
│   ├── database/        # SQLite persistence
│   │   ├── models.py        # Schema
│   │   └── repository.py    # CRUD operations
│   ├── notifications/   # Console notifications
│   │   └── notifier.py
│   ├── scheduler/       # Periodic monitoring
│   │   └── monitor.py       # APScheduler
│   ├── ui/              # Web dashboard
│   │   ├── app.py           # FastAPI app
│   │   ├── routes.py        # API endpoints
│   │   └── templates/       # Jinja2 templates
│   └── main.py          # Entry point
├── config/
│   └── settings.py      # Configuration
├── tests/               # Test suite (68+ tests)
├── data/                # SQLite database (gitignored)
└── generated/           # Output documents (gitignored)
```
