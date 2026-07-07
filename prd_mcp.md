# PRD: AI-Powered LMS Assistant

## 1. Overview

An intelligent assistant that automates LMS interactions — monitoring assignments, generating AI solutions, creating formatted submission documents, and submitting with user approval. Built for the SSN College of Engineering Moodle-based LMS.

## 2. Problem Statement

Students using Moodle-based LMS platforms face repetitive manual workflows: checking for new assignments, reading instructions, writing solutions, formatting documents, and submitting. This project eliminates the repetitive overhead while keeping the student in control of the final submission.

## 3. Goals & Objectives

- Automatically monitor LMS for new assignments via scheduled polling
- Retrieve full assignment details (title, description, attachments, due dates)
- Classify assignment types using AI (document, programming, handwritten, etc.)
- Generate AI-powered solutions
- Produce professionally formatted DOCX/PDF documents
- Submit assignments to LMS with user approval
- Maintain a searchable history of all assignments and submissions
- Provide a web dashboard and MCP server for flexible interaction

## 4. Target Users

- **Primary:** University students using Moodle-based LMS platforms
- **Secondary:** Developers integrating AI assignment workflows via MCP

## 5. Architecture

```
                    ┌─────────────────────────────────┐
                    │         LMS (Moodle)             │
                    └──────────┬──────────────────────┘
                               │ (Playwright automation)
                    ┌──────────▼──────────────────────┐
                    │        MCP Server (stdio)        │
                    │  (12 tools: login, list, solve,  │
                    │   submit, classify, generate, …) │
                    └──┬───────────────┬───────────────┘
                       │               │
              ┌────────▼───┐   ┌───────▼────────┐
              │  AI Agent   │   │  Web Dashboard │
              │  (Gemini /  │   │  (FastAPI +     │
              │  Claude /   │   │   Jinja2 +      │
              │  GPT-4o)    │   │   SQLite)       │
              └─────────────┘   └───────┬─────────┘
                                       │
                              ┌────────▼────────┐
                              │  SQLite Database │
                              │  (assignments,   │
                              │   submissions,   │
                              │   history)       │
                              └─────────────────┘
```

### Core Components

| Component | Technology | Purpose |
|---|---|---|
| **Browser Automation** | Playwright (async) | Login, scrape LMS pages, download attachments, upload & submit files |
| **AI Client** | Google Gemini (primary) / Anthropic Claude / OpenAI GPT-4o | Assignment classification, solution generation |
| **MCP Server** | FastMCP (Python MCP SDK) | Expose LMS/AI capabilities as MCP tools for AI agent consumption |
| **Web UI** | FastAPI + Jinja2 | Web dashboard for assignment overview, solve, and submit actions |
| **Database** | SQLite (WAL mode) | Persistent storage for assignments, submissions, history, courses |
| **Document Generator** | python-docx + reportlab | Generate DOCX/PDF submission documents with student info headers |
| **Scheduler** | APScheduler | Periodic polling for new assignments |
| **Notifications** | Console/logger | Alert user on new assignments and status changes |

## 6. Functional Requirements

### FR1: LMS Authentication
- Log in to Moodle LMS using credentials from environment variables
- Detect existing sessions and skip re-login
- Log out on demand

### FR2: Assignment Monitoring & Retrieval
- List all visible assignments from the dashboard timeline
- Fetch full assignment details (title, intro, course, due dates, attachments)
- Download assignment attachments (PDFs, etc.)
- Extract text from downloaded PDFs for AI context

### FR3: Assignment Classification
- AI-classify assignments into types:
  - `document` — written report/essay
  - `programming` — coding assignment
  - `handwritten` — scanned notebook submission
  - `presentation` — slide deck
  - `quiz` — online quiz/test
  - `image` — image upload
  - `other` — fallback

### FR4: AI Solution Generation
- Generate solutions using configurable LLM provider
- Provider-agnostic abstraction (Google / Anthropic / OpenAI)
- Automatic retry with exponential backoff on quota errors (429)
- Solution output in well-structured Markdown

### FR5: Document Generation
- Generate DOCX and PDF documents from solution Markdown
- Include student info header (name, reg no, subject, date)
- Basic Markdown → DOCX/PDF conversion (headings, lists, code blocks)
- Upload-ready format for LMS

### FR6: Assignment Submission
- Upload generated file to LMS submission page
- Click submit button on LMS
- Confirm submission success
- Track submission status

### FR7: Submission Status Tracking
- Check individual assignment submission status on LMS
- Display status in dashboard (submitted / pending)
- Differentiate between submitted and unsubmitted assignments

### FR8: Web Dashboard
- View all assignments in a sortable table
- See submission status badges per assignment
- Get assignments from LMS with one click
- Check unsubmitted assignments
- Login/logout from LMS
- Solve assignments via AI
- Submit assignments (classify → solve → document → upload → submit pipeline)

### FR9: History & Logging
- Log all actions (login, list, classify, solve, generate, submit)
- View history per assignment or globally
- Track submission receipts

### FR10: Periodic Monitoring
- Poll LMS at configurable intervals (default: 30 min)
- Detect new assignments automatically
- Notify user on detection (console logger)
- Save new assignments to database

## 7. MCP Tools (12 tools)

| # | Tool | Input | Output |
|---|---|---|---|
| 1 | `login` | username?, password? | Status message |
| 2 | `logout` | — | Status message |
| 3 | `list_assignments` | — | List of assignment dicts |
| 4 | `get_assignment` | assignment_id | Assignment detail dict |
| 5 | `download_attachment` | assignment_id, url, filename? | File path string |
| 6 | `classify_assignment` | assignment_id | Type string |
| 7 | `solve_assignment` | assignment_id | Solution markdown string |
| 8 | `generate_document` | assignment_id, fmt="docx" | File path string |
| 9 | `upload_submission` | assignment_id, file_path | Status message |
| 10 | `submit_assignment` | assignment_id | Status message |
| 11 | `get_submission_status` | assignment_id | Status string from LMS |
| 12 | — (Web UI exclusive) | — | — |

## 8. Database Schema

### `courses`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| course_id | TEXT UNIQUE | LMS course identifier |
| name | TEXT | Course name |
| url | TEXT | Course page URL |
| created_at | TEXT | Auto timestamp |
| updated_at | TEXT | Auto timestamp |

### `assignments`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| assignment_id | TEXT UNIQUE | LMS assignment ID |
| title | TEXT | Assignment title |
| course_id | TEXT | Foreign key to courses |
| course_name | TEXT | Denormalized course name |
| description | TEXT | Full assignment description |
| intro_html | TEXT | Raw HTML intro |
| attachment_urls | TEXT | JSON array of attachments |
| due_date | TEXT | Due date string from LMS |
| assignment_type | TEXT | AI-classified type |
| status | TEXT | new / solved / submitted / etc |
| created_at | TEXT | Auto timestamp |
| updated_at | TEXT | Auto timestamp |

### `submissions`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| assignment_id | TEXT FK | References assignments |
| solution_text | TEXT | AI-generated solution |
| document_path | TEXT | Path to generated file |
| document_type | TEXT | docx / pdf / markdown |
| submitted_at | TEXT | When submitted to LMS |
| submission_status | TEXT | draft / uploaded / submitted |
| ai_generated | BOOLEAN | Default true |
| created_at | TEXT | Auto timestamp |

### `history`
| Column | Type | Notes |
|---|---|---|
| id | INTEGER PK | Auto-increment |
| assignment_id | TEXT FK | References assignments |
| action | TEXT | e.g., "solve", "submit", "classify" |
| details | TEXT | Contextual info |
| created_at | TEXT | Auto timestamp |

## 9. Non-Functional Requirements

- **Performance:** Dashboard loads in <2s; AI generation may take 5–30s
- **Reliability:** Retry logic for 429 quota errors (3 attempts, exponential backoff)
- **Security:** Credentials stored in `.env` only, never hardcoded; no credential exposure in API responses
- **Portability:** Cross-platform Python (Linux/macOS/Windows); single `pip install -e .` setup
- **Maintainability:** Modular architecture with clear separation of concerns (lms / ai / documents / database / ui / mcp)
- **Observability:** Structured logging via stdlib logging module; all actions logged to history table

## 10. Configuration (`.env`)

```
LMS_URL=               # LMS base URL
LMS_USERNAME=          # LMS login email
LMS_PASSWORD=          # LMS password
AI_PROVIDER=           # "google" | "anthropic" | "openai"
GOOGLE_API_KEY=        # Google Gemini API key
ANTHROPIC_API_KEY=     # Anthropic Claude API key
OPENAI_API_KEY=        # OpenAI GPT-4o API key
STUDENT_NAME=          # Student name for document headers
STUDENT_REG_NO=        # Registration number
STUDENT_DEPT=          # Department
STUDENT_YEAR=          # Year
DATABASE_PATH=         # SQLite DB path
GENERATED_DIR=         # Output directory for documents
POLL_INTERVAL_MINUTES= # Scheduler interval (default: 30)
```

## 11. Run Modes

| Command | Description |
|---|---|
| `python -m app.main mcp` | Run MCP server (stdio transport) for AI agent |
| `python -m app.main web` | Run web dashboard at http://127.0.0.1:8080 |
| `python -m app.main all` | Run MCP + Web UI + Scheduler together |
| `python -m app.main init-db` | Initialize/reset database |
| `python run_fetch.py` | CLI script: fetch & display pending assignments |
| `python run_solve.py` | CLI script: full pipeline for a hardcoded assignment (ID: 130712) |

## 12. Project Structure

```
lms_mcp/
├── app/
│   ├── ai/               # LLM integration
│   │   ├── client.py     # Provider-agnostic client (Gemini/Claude/GPT)
│   │   ├── classifier.py # Assignment type classification
│   │   └── solver.py     # Solution generation with typed prompts
│   ├── database/         # Persistence
│   │   ├── models.py     # Schema definition + init_db()
│   │   └── repository.py # CRUD operations
│   ├── documents/        # Document generation
│   │   ├── generator.py  # DOCX/PDF generation
│   │   └── templates.py  # Student info + markdown template
│   ├── lms/              # LMS browser automation
│   │   ├── auth.py       # Login/logout
│   │   ├── browser.py    # Playwright lifecycle manager
│   │   ├── assignments.py # List, get details, download
│   │   ├── submission.py # Upload, submit, status check
│   │   └── selectors.py  # Moodle CSS selectors
│   ├── mcp/              # MCP server
│   │   ├── server.py     # FastMCP server with tool decorators
│   │   └── tools.py      # Tool implementations
│   ├── notifications/    # User notifications
│   │   └── notifier.py   # Console notifications
│   ├── scheduler/        # Periodic monitoring
│   │   └── monitor.py    # APScheduler-based polling
│   ├── ui/               # Web dashboard
│   │   ├── app.py        # FastAPI app with lifespan
│   │   ├── routes.py     # REST API endpoints
│   │   └── templates/    # Jinja2 templates
│   └── main.py           # CLI entry point
├── config/
│   └── settings.py       # Environment-based configuration
├── data/                 # SQLite database (gitignored)
├── generated/            # Generated documents (gitignored)
├── testing/              # Test outputs
├── site_files/           # Reference HTML snapshots
├── run_fetch.py          # CLI: fetch pending assignments
├── run_solve.py          # CLI: solve pipeline for specific assignment
├── prd.md                # This document
└── README.md             # Project readme
```

## 13. Known Limitations

- **LMS Theme Dependency:** CSS selectors in `selectors.py` are tied to the current Moodle theme; may break after LMS theme updates
- **No Official LMS API:** Relies entirely on browser automation (Playwright), which is fragile compared to a proper API integration
- **Single LMS Support:** Currently hardcoded to SSN College LMS; would need abstraction for other LMS platforms
- **No Edit/Review UI:** The web dashboard shows assignments but doesn't yet support inline editing of AI solutions before submission
- **Free-tier Quota Limits:** Google Gemini free tier has rate limits; the app retries but repeated quota errors will block the pipeline

## 14. Future Enhancements

- [ ] In-browser solution preview and editing
- [ ] Calendar/deadline integration with reminders
- [ ] Multiple LMS platform support (Canvas, Blackboard, etc.)
- [ ] Plagiarism/self-check warnings
- [ ] Auto-citation generation (IEEE/APA/MLA)
- [ ] OCR for handwritten/scanned assignment instructions
- [ ] Team assignment collaboration support
- [ ] Mobile companion app (notifications + status)
- [ ] Email/push notifications (beyond console)
- [ ] Analytics dashboard (submission trends, grades tracking)
