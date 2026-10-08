# AI Code Classroom - Backend

An AI-powered coding assessment and learning platform combining features of Google Classroom, HackerRank, and local open-source AI problem generation (Ollama).

- **Phase 1**: Base backend foundation, database ORM models, JWT authentication, role-based authorization (`TEACHER` and `STUDENT`), and classroom management APIs.
- **Phase 2**: Coding environment, problem management, test case management, submission system, code execution engine, and Docker-based secure container execution.
- **Phase 3**: React + Vite + Tailwind CSS frontend, Monaco Editor coding workspace, student dashboard, teacher dashboard, and real-time evaluation UI.
- **Phase 4**: Ollama AI Question Generation & Deterministic Question Verification Pipeline using isolated Docker containers.
- **AI Coding Tutor**: progressive hints (levels 1-3) with error classification for failed submissions.
- **Phase 6**: Configurable scoring (points events), deterministic classroom leaderboard, and student/classroom analytics with topic mastery.
- **Phase 7**: Assignments with deadlines, publishing, and per-student progress tracking.
- **Teacher Student Performance Profile**: one page per student covering everything above (see the end of this file).

---

## Technical Features

- **FastAPI**: Modern, high-performance REST API architecture with automatic interactive OpenAPI documentation (`/docs`).
- **PostgreSQL / SQLite Dual Engine**: Defaults to local SQLite for instant zero-config development, with full PostgreSQL support via SQLAlchemy ORM.
- **Security & Authorization**: JWT token issuance, Passlib `bcrypt` password hashing, and role protection (`TEACHER` and `STUDENT`).
- **Classroom Management**: Automatic generation of unique 7-character classroom join codes (e.g., `PY10192`).
- **Local Open-Source AI Generation (Ollama)**: Generates structured coding problems using local LLMs (e.g. `qwen2.5-coder:7b`) without requiring external or paid API keys.
- **Deterministic Question Verification Pipeline**: Automatically executes AI-generated reference solutions in isolated Docker containers against generated test cases before teacher preview.
- **Isolated Code Execution Engine**: Python, C, and C++ code execution isolated in Docker containers (`python-runner` image, which bundles `gcc`/`g++`) with execution timeouts, resource limits, and network isolation.
- **Submission System & History**: Real-time evaluation (`PENDING`, `RUNNING`, `ACCEPTED`, `WRONG_ANSWER`, `RUNTIME_ERROR`, `TIME_LIMIT_EXCEEDED`).
- **Alembic Database Migrations**: Schema evolution for users, classrooms, problems, testcases, and submissions.
- **Automated Test Suite**: 88 unit and security tests (`pytest`) across all phases, including the teacher student profile access rules.
- **Teacher Student Performance Profile**: Per-student page for teachers covering assignments, problems, submissions (with read-only code), AI tutor statistics, error analysis, topic mastery, trends and points history.

---

## Directory Structure

```
backend/
├── app/
│   ├── main.py                     # FastAPI app, CORS, routers, sandbox-unavailable (503) handler
│   ├── core/
│   │   ├── config.py               # Settings (JWT, DB, Ollama, scoring thresholds, CORS)
│   │   ├── security.py             # Password hashing & JWT
│   │   └── time.py                 # utcnow() helper (naive UTC)
│   ├── database/                   # Declarative Base, engine & session
│   ├── models/                     # user, classroom, problem (+TestCase), submission,
│   │                               # feedback (AI tutor), points (StudentPointsEvent), assignment
│   ├── schemas/                    # Pydantic request/response models, incl. student_profile.py
│   ├── api/
│   │   ├── auth.py                 # /register, /login, /me
│   │   ├── classrooms.py           # Classroom CRUD, join, and teacher student profile endpoints
│   │   ├── problems.py             # Problems, test cases, AI generate/confirm/discard
│   │   ├── submissions.py          # Submit code, history, AI tutor feedback
│   │   ├── analytics.py            # Student/classroom analytics & leaderboard
│   │   └── assignments.py          # Assignments & progress
│   ├── services/
│   │   ├── code_runner.py          # Docker sandbox (refuses to run code if Docker is unavailable)
│   │   ├── submission_service.py   # Judging, failed-test number & error message
│   │   ├── question_generator.py   # AI generation pipeline (+ question_validator, ai_provider, ollama_provider, ai_service)
│   │   ├── tutor_service.py        # AI tutor (+ tutor_validator)
│   │   ├── scoring_service.py      # Points events
│   │   ├── leaderboard_service.py  # Ranking engine
│   │   ├── analytics_service.py    # Analytics & topic classification
│   │   ├── assignment_service.py   # Assignments (+ deadline_service)
│   │   ├── student_profile_service.py  # Teacher → student profile aggregation & authorization
│   │   └── classroom_service.py
│   └── dependencies/auth.py        # get_current_user / teacher / student
├── alembic/versions/               # 5 migrations (problems → AI fields → AI feedback → points → assignments)
├── docker/python_runner/Dockerfile # Sandbox image
├── tests/                          # pytest suite (one file per area)
├── run.ps1                         # Start backend on :8100 with win_venv + auto-reload
├── requirements.txt
└── .env.example
```

---

## Ollama Local Setup Instructions

1. **Install Ollama**: Download and install Ollama from [https://ollama.com/download](https://ollama.com/download).
2. **Start Ollama Server**:
   ```bash
   ollama serve
   ```
3. **Pull Target Model**:
   ```bash
   ollama pull qwen2.5-coder:7b
   ```
4. **Configure `.env`**:
   ```env
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=qwen2.5-coder:7b
   OLLAMA_TIMEOUT=120
   AI_MAX_RETRIES=3
   AI_PROVIDER_TYPE=ollama
   ```

*Note: Automated tests do NOT require Ollama to be running. Pytest uses `MockAIProvider` for instant, deterministic test execution.*

---

## Installation & Setup

### 1. Prerequisites
- Python 3.10+ installed.
- Docker (required for code execution and AI reference solution verification).

### 2. Build Docker Runner Container
```bash
docker build -t python-runner ./docker/python_runner
```
This image runs Python, C, and C++ submissions. If you already have a `python-runner` image built from before C/C++ support was added, rebuild it (`docker build -t python-runner ./docker/python_runner`) so `gcc`/`g++` are installed.

### 3. Create and Activate Virtual Environment

**Windows (PowerShell):** the project's environment is `win_venv` (used by `run.ps1`):
```powershell
python -m venv win_venv
.\win_venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Database Migrations (Alembic)

Apply all database migrations:
```bash
alembic upgrade head
```

---

## Running the App

This project uses non-default ports so it doesn't clash with other local apps on 5173/8000:

| Service | URL |
| :--- | :--- |
| Backend (FastAPI) | `http://127.0.0.1:8100` (docs at `/docs`) |
| Frontend (Vite) | `http://localhost:5180` (proxies `/api` to the backend) |

**One step:** double-click `start.cmd` in the project folder (or run `.\start.ps1`). It starts Docker Desktop and Ollama if they are off, builds the sandbox image if missing, opens the backend and frontend in their own windows, and opens the browser. Anything already running is skipped. `.\stop.ps1` stops the two servers (Docker and Ollama keep running).

**Manually:**

```powershell
# Backend: always uses win_venv, so the right package versions are loaded
cd backend; .\run.ps1

# Frontend (separate terminal)
cd frontend; npm run dev
```

Docker Desktop must be running (with the `python-runner` image built) for code submissions and AI question verification.

---

## Running Automated Tests

Run the complete test suite:

```bash
pytest -v
```

All **88 test cases** pass, covering authentication, classrooms, problems, submissions and Docker execution, AI question generation, scoring and analytics, assignments, and the teacher student profile (including its access rules).

---

## API Documentation (AI & Problem Management)

### AI Question Generation & Preview APIs (`/api/problems`)

| Method | Endpoint | Allowed Role | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/problems/generate` | `TEACHER` | Generate coding problems via Ollama and verify reference solutions in Docker |
| `POST` | `/api/problems/{id}/confirm` | `TEACHER` | Save and publish a draft verified AI problem (makes it visible to students) |
| `POST` | `/api/problems/{id}/discard` | `TEACHER` | Discard an unconfirmed AI problem preview |

#### Example AI Generation Request:
```json
{
  "language": "python",
  "difficulty": "MEDIUM",
  "topic": "recursion",
  "count": 2
}
```

#### Example AI Generation Response:
```json
{
  "generated": 2,
  "verified": 2,
  "failed": 0,
  "questions": [
    {
      "id": 14,
      "title": "Recursive Fibonacci Number",
      "description": "Calculate the N-th Fibonacci number recursively.",
      "difficulty": "MEDIUM",
      "status": "DRAFT",
      "language": "python",
      "topic": "recursion",
      "constraints": "1 <= N <= 30",
      "input_format": "Single integer N",
      "output_format": "N-th Fibonacci number",
      "examples": "[{\"input\": \"5\", \"output\": \"5\"}]",
      "test_case_count": 3,
      "verification_message": "Reference solution passed all generated test cases."
    }
  ]
}
```

---

## Teacher → Student Performance Profile (`/api/classrooms`)

Read-only, teacher-only endpoints. Every request is checked on the backend: the user must be a **teacher**, must **own the classroom**, and the student must be **enrolled in it** (otherwise `403`/`404`).

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/classrooms/{id}/students` | Roster with rank, points, accuracy and assignment progress (uses the Phase 6 leaderboard engine) |
| `GET` | `/api/classrooms/{id}/students/{student_id}/profile` | Full profile: header, summary, overall metrics, assignments, problems, submission history, AI tutor stats, error analysis, topic mastery, trends, points history, recent activity |
| `GET` | `/api/classrooms/{id}/students/{student_id}/submissions/{submission_id}` | One submission including its source code |

The profile never includes hidden test cases, reference solutions or AI hint text (AI tutor use is reported as counts and categories). Source code is only returned by the single-submission endpoint.

Known limitations: memory usage is not measured by the sandbox, and opening a problem is not tracked. Metrics cover all of a student's submissions, since problems are shared across classrooms; this matches the classroom leaderboard.

UI: **My Classrooms → View Details → Students → click a student** opens `/teacher/classrooms/{id}/students/{student_id}`.
