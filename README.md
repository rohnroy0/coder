# Coder

**A Smarter Coding Platform for Every Student and Teacher**

Coder is a full-stack coding education platform that combines the essentials of Google Classroom, HackerRank, and a local, open-source AI problem generator. Teachers create classrooms, author or AI-generate coding problems, and track student performance in real time; students join classrooms, solve problems in an in-browser Monaco editor, get Socratic AI tutoring on failed submissions, and progress through a Duolingo-style learning path with streaks, levels, and badges.

All code execution runs sandboxed in Docker — nothing submitted by a student ever touches the host.

---

## Features

- **Classrooms & assignments** — teachers create classrooms with unique join codes, assign problems with deadlines, and track per-student progress.
- **Problem authoring** — manual problem creation with hidden/sample test cases, or AI-generated problems (via a local Ollama model) that are automatically verified in Docker before a teacher confirms them.
- **Sandboxed code execution** — Python, C, and C++ submissions run in an isolated Docker container with timeouts and resource limits.
- **AI coding tutor** — progressive, Socratic hints (not solutions) on failed submissions, with a server-side anti-solution-leak guard.
- **Learning paths** — a Duolingo-style chapter model for students to self-study concepts independently of classroom assignments.
- **Streaks, levels & badges** — gamified progress tracking to keep students engaged.
- **Leaderboard & analytics** — classroom leaderboards, topic mastery breakdowns, and a full teacher-facing per-student performance profile.
- **Role-based auth** — JWT-based authentication with distinct teacher/student roles and permissions, enforced on every endpoint.

---

## Tech Stack

**Backend:** FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2, JWT (PyJWT + Passlib), SQLite (dev) / PostgreSQL-ready, pytest.

**Frontend:** React 19, Vite 6, React Router 7, Tailwind CSS 4, Monaco Editor, Axios, lucide-react.

**AI / Execution:** Ollama (local LLM, default `qwen2.5-coder:7b`) for problem generation and tutoring; Docker for isolated code execution and reference-solution verification.

---

## Repository Layout

```
.
├── backend/            FastAPI app, SQLAlchemy models, Alembic migrations, pytest suite
│   ├── app/
│   │   ├── api/         Route modules: auth, classrooms, problems, submissions, analytics, assignments, badges, learning
│   │   ├── core/        Config, security, time helpers
│   │   ├── models/      ORM models
│   │   ├── schemas/     Pydantic request/response schemas
│   │   ├── services/    Business logic (code execution, AI generation, tutoring, scoring, leaderboard, analytics)
│   │   └── dependencies/
│   ├── alembic/versions/
│   ├── docker/python_runner/   Sandbox image (Python/C/C++ runner)
│   └── tests/
├── frontend/            React + Vite SPA
│   └── src/
│       ├── pages/
│       │   ├── public/   Landing, login, register
│       │   ├── student/   Dashboard, classrooms, problems, workspace, learning paths, submission history, performance
│       │   └── teacher/   Dashboard, classrooms, problem authoring, AI generation, assignments, student profiles
│       ├── routes/       AppRoutes.jsx
│       ├── components/, layouts/, context/, api/
├── start.cmd / start.ps1   One-step local startup (Docker, Ollama, backend, frontend, browser)
└── stop.ps1                Stops backend/frontend dev servers
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js (for the Vite frontend)
- Docker Desktop (required for code execution and AI verification)
- [Ollama](https://ollama.com/download) (optional, only needed for AI problem generation and the AI tutor)

### One-step start (Windows)
```powershell
.\start.ps1
```
This starts Docker Desktop and Ollama if they're off, builds the sandbox image on first run, launches the backend (`:8100`) and frontend (`:5180`) in their own windows, and opens the browser. Safe to re-run — anything already running is left alone. Use `.\stop.ps1` to stop the dev servers.

### Manual setup

```bash
# 1. Build the sandbox image
docker build -t python-runner ./backend/docker/python_runner

# 2. Backend
cd backend
python -m venv venv && source venv/bin/activate   # win_venv + Activate.ps1 on Windows
pip install -r requirements.txt
alembic upgrade head
cp .env.example .env   # fill in as needed
uvicorn app.main:app --reload --port 8100

# 3. Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Backend docs: `http://127.0.0.1:8100/docs` · Frontend: `http://localhost:5180`

### Running tests
```bash
cd backend
pytest -v
```
