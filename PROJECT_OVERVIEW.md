# Coder — Complete Project Guide

> A single reference document for the team to understand everything about the
> project before the final review: what it is, how it's built, how each part
> works, how it's deployed and reachable online, and how to run and demo it.
>
> Live demo URL: **https://laptop-2cieedeq.tail166231.ts.net**
> GitHub: **https://github.com/rohnroy0/coder**

---

## 1. What is Coder? (the one-paragraph pitch)

**Coder is a web platform for teaching and assessing programming.** It combines
the *classroom management* of Google Classroom with the *automated coding
judge* of HackerRank, and adds an *AI tutor* that helps students learn without
handing them the answer. Teachers create classrooms, build or AI-generate
coding problems with hidden test cases, and assign them with deadlines.
Students write code in an in-browser editor; every submission is executed
inside an isolated Docker container, graded against the hidden tests, and
scored on a transparent points system with streaks, badges, and per-classroom
leaderboards. When a student gets stuck, an AI tutor gives progressive Socratic
hints. Teachers get analytics on class and per-student performance.

**Who uses it:**
- **Teachers (role: TEACHER / shown as "Faculty")** — run classrooms, author
  problems, set assignments, view analytics.
- **Students (role: STUDENT)** — join classrooms, solve problems, track
  progress, earn points/badges.

---

## 2. Feature list (what the app can actually do)

**Accounts & classrooms**
- Register/login with JWT auth; separate Student and Teacher roles.
- Teachers create classrooms (each gets a join code); students join by code.
- A student can be in multiple classrooms; scoring is tracked *per classroom*.

**Problems & the code judge**
- Teachers create problems manually (description, input/output format,
  constraints, sample + hidden test cases) **or** generate them with AI.
- Supports **Python, C, and C++**.
- **Run** button: tests code against sample (visible) cases only — nothing saved.
- **Submit** button: runs against *all* test cases (including hidden) in Docker,
  returns a verdict: `ACCEPTED`, `WRONG_ANSWER`, `RUNTIME_ERROR`,
  `TIME_LIMIT_EXCEEDED`, plus which test number failed and execution time.
- 5-second per-run time limit, memory/CPU/process limits, no network inside the
  sandbox.

**AI features** (powered by a Large Language Model — see section 5)
- **AI Problem Generator** (teachers): describe a topic/difficulty/language and
  the AI writes complete problems *with reference solutions and test cases*,
  which are then auto-verified in Docker before the teacher confirms them.
- **AI Tutor** (students): on a failing Run or Submission, gives progressive
  Socratic hints (Level 1 conceptual → Level 3 targeted) that explain the error
  and guide toward the fix **without revealing the solution**.

**Assignments**
- Teachers bundle problems into assignments with start/due dates and points.
- Students see their assignments, progress, and scores; deadlines are enforced.

**Gamification & analytics**
- Transparent points: +100 solve, +20 fast-execution bonus, +10 first-attempt
  bonus, −5 penalties (capped). Levels every 200 points.
- 10 badges (First Blood, Problem Solver, Speed Demon, Clean Coder, etc.).
- Per-classroom leaderboards (rank by points → solved → accuracy).
- Streaks (consecutive days with activity).
- Teacher analytics: class overview, topic strength, "struggling students",
  and a detailed per-student performance profile.

---

## 3. Technology stack (what it's built with)

| Layer | Technology | Why |
|---|---|---|
| **Frontend** | React 19 + Vite 6, Tailwind CSS 4, React Router 7 | Fast modern SPA; Vite dev server with hot reload |
| **Code editor** | Monaco Editor (the editor from VS Code) | Professional in-browser coding experience |
| **Icons / fonts** | lucide-react, Google Fonts (Fraunces + Inter) | Clean "collegiate" visual theme |
| **Backend** | Python 3.11, FastAPI | Fast, typed, auto-generated API docs |
| **ORM / DB** | SQLAlchemy 2.0 + SQLite (Postgres-ready) | Simple file DB for our scale; can scale up |
| **Auth** | JWT (PyJWT) + Passlib (pbkdf2_sha256 hashing) | Stateless tokens, securely hashed passwords |
| **Code sandbox** | Docker (`python-runner` image, Alpine + gcc/g++) | Real isolation for running untrusted student code |
| **AI** | Groq hosted API (model `openai/gpt-oss-120b`), OpenAI-compatible | Free, fast cloud LLM; swappable to Gemini/Ollama |
| **Tests** | pytest (173 tests) | Confidence the backend behaves correctly |
| **Hosting (demo)** | Tailscale Funnel (public HTTPS tunnel to the laptop) | Free public URL with real HTTPS, no cloud account |

**Key ports (local dev):** backend = **8100**, frontend = **5180**.

---

## 4. Architecture — how the pieces fit together

```
                    ┌───────────────────────────────────────────────┐
  Browser  ──HTTPS──►  Tailscale Funnel (public URL, auto HTTPS)     │
 (any user)         └───────────────────┬───────────────────────────┘
                                        │  forwards to the laptop
                                        ▼
                         ┌──────────────────────────────┐
                         │  Vite dev server  :5180       │   serves the React app
                         │  (React single-page app)      │   and proxies /api ──┐
                         └──────────────────────────────┘                        │
                                                                                 ▼
                                                        ┌────────────────────────────────┐
                                                        │  FastAPI backend  :8100         │
                                                        │  - auth, classrooms, problems,  │
                                                        │    submissions, assignments,    │
                                                        │    analytics, AI endpoints      │
                                                        └───────┬───────────────┬─────────┘
                                                                │               │
                                       per code submission      │               │  AI requests
                                                                ▼               ▼
                                            ┌─────────────────────────┐   ┌──────────────────┐
                                            │ Docker container         │   │ Groq API (cloud) │
                                            │ (python-runner image)    │   │ LLM: gpt-oss-120b│
                                            │ runs the student's code  │   └──────────────────┘
                                            │ in isolation, 5s limit   │
                                            └─────────────────────────┘
                                                                │
                                                                ▼
                                            ┌─────────────────────────┐
                                            │ SQLite database file     │
                                            │ (users, classrooms,      │
                                            │  problems, submissions,  │
                                            │  points, badges, ...)    │
                                            └─────────────────────────┘
```

**Request flow for a code submission (the heart of the app):**
1. Student writes code in the Monaco editor and clicks **Submit**.
2. React sends the code to `POST /api/submissions`.
3. FastAPI validates (problem is published, student enrolled, deadline not
   passed), saves a PENDING submission.
4. For each test case, the backend writes the code + input to a temp folder,
   then runs `docker run` with the `python-runner` image, mounting the code
   read-only, with strict limits (128 MB RAM, 0.5 CPU, no network, 5 s timeout).
5. The container compiles (for C/C++) and runs the program, measuring the
   *program's* execution time inside the container.
6. The backend compares output to the expected output → produces a verdict.
7. The Scoring Service awards/deducts points; the Badge Service checks for newly
   earned badges; assignment progress is updated.
8. The verdict, failed test number, time, points, and any new badges are
   returned to the browser and displayed.

---

## 5. How the AI works (important for the review — this is a selling point)

**The design goal:** the AI should be *swappable*. All AI calls go through one
interface (`AIProvider`), so we can switch between providers by editing one line
in a config file — no code changes.

**Providers supported** (set by `AI_PROVIDER_TYPE` in `backend/.env`):
- `groq` — **what we currently use.** Groq hosts open-source LLMs behind a free,
  rate-limited API. Fast (hints in ~1–2 s) and no credit card needed.
- `gemini` — Google's free-tier API (backup option).
- `ollama` — runs an LLM *locally* on the machine (our original approach; needs
  a powerful PC and is much slower).
- `openai_compat` — any other OpenAI-compatible host.
- `mock` — canned responses, used by the automated tests.

**Current model:** `openai/gpt-oss-120b` (a 120-billion-parameter open model,
served by Groq). Note: Groq occasionally retires models — if AI stops working
with a "model_not_found" error, list available models and update `AI_API_MODEL`
in `.env` (documented in `backend/README.md`).

**Two AI pipelines:**
1. **Problem generation** — the teacher's topic/difficulty prompt is sent to the
   LLM with a strict instruction to return JSON (problem text + test cases +
   a reference solution). The reference solution is then **actually executed in
   Docker against the generated tests** to verify it's correct before the
   teacher ever sees it. Bad generations are rejected automatically.
2. **Tutoring** — the student's failing code + the error type is sent to the LLM
   with a "Socratic tutor" system prompt that forbids giving the solution. The
   response is validated (an anti-solution check) before being shown.

---

## 6. How student code runs safely (the Docker sandbox)

Running untrusted student code is risky, so every execution is **sandboxed**:
- Runs inside a throwaway Docker container built from the `python-runner` image
  (Alpine Linux + Python + gcc/g++ for C/C++).
- **No network** (`--network none`) — code can't call out to the internet.
- **Memory capped** at 128 MB, **CPU** at 0.5, **processes** capped — prevents
  fork bombs and resource exhaustion.
- **Read-only filesystem**; the student code is mounted read-only.
- **5-second timeout** enforced both inside and outside the container.
- The container is **auto-removed** after each run.

Security hardening we specifically built in (came out of a full bug audit):
- Hidden test-case inputs are never leaked back to students (a student can't
  trick the error message into printing the secret test input).
- Students can't fake a "sandbox unavailable" error to dodge penalties (the
  backend double-checks with Docker directly).
- Submissions are validated: you can't submit to an unpublished problem, to an
  assignment you're not enrolled in, or after a deadline.

---

## 7. Scoring, levels, and badges (exact rules)

**Points per problem (configurable in `backend/app/core/config.py`):**
- `+100` for an accepted (correct) solution — **once per problem per classroom.**
- `+20` fast-execution bonus (average in-container runtime ≤ 0.2 s per test).
- `+10` first-attempt bonus (solved on the very first submission).
- `−5` penalty for each wrong answer / runtime error / time-limit (capped at 5
  penalties per problem, so you can't be punished infinitely).

**Levels:** every `200` points = one level.

**Badges (10 total):** First Blood (1st solve), Problem Solver (10 solved),
Problem Crusher (25 solved), Sharpshooter (10 submissions), Speed Demon (earn a
fast bonus), Clean Coder (first-attempt solve), Getting Started / Consistent
Coder / Unstoppable (3/7/30-day streaks), Assignment Ace (5 assignments done).

**Leaderboard ranking order:** total points → problems solved → accuracy →
(student id as tiebreaker). Scoped to each classroom's assigned problems.

---

## 8. How it's made available online (the deployment story)

This is the part reviewers often ask about: *"how can we access it?"*

**The challenge:** the code judge needs real Docker, which free web hosts
(Vercel, Render free tier, etc.) don't allow. And we had no credit card or
university email, which rules out most free cloud VM trials.

**Our solution: Tailscale Funnel.** The app runs on the developer's laptop, and
Tailscale Funnel creates a secure public tunnel to it with a real HTTPS
certificate and a stable URL (`https://laptop-2cieedeq.tail166231.ts.net`).
This is free, needs no credit card, and gives anyone on the internet access —
as long as the laptop is on and the app is running.

**Also in the repo (`deploy/` folder):** a complete, one-command deployment to a
real cloud VM (Ubuntu + Docker + Caddy for HTTPS + systemd service). If we ever
get a cloud account, `deploy/setup-server.sh <domain>` sets up the whole thing.
This shows the project is *production-ready*, not just a laptop demo —
worth mentioning in the review. Details in `deploy/DEPLOY.md`.

**Security for public exposure:** because anyone can reach the URL, teacher
registration is gated behind a **teacher signup code** (students register
freely). The code is stored in `backend/.env` (not in GitHub).

---

## 9. How to run it locally (for teammates on Windows)

Prerequisites: **Docker Desktop**, **Node.js**, **Python 3.11**, and a free
**Groq API key** (from console.groq.com) for AI features.

1. Clone the repo and open the folder.
2. Copy `backend/.env.example` to `backend/.env` and fill in:
   - `SECRET_KEY` (any long random string)
   - `AI_PROVIDER_TYPE=groq` and `AI_API_KEY=<your groq key>`
   - optionally `TEACHER_SIGNUP_CODE=<some code>`
3. Double-click **`start.cmd`** (or run `.\start.ps1` in PowerShell). This script
   starts Docker, builds the sandbox image, starts the backend (:8100) and
   frontend (:5180), and opens the browser.
4. To stop everything: `.\stop.ps1`.

The app is then at **http://localhost:5180**.

Run the backend tests: `cd backend; .\win_venv\Scripts\python.exe -m pytest tests -q`

---

## 10. Important facts & credentials (keep these handy for the demo)

- **Live URL:** https://laptop-2cieedeq.tail166231.ts.net  (up only while the
  laptop is on and `start.ps1` is running; after a reboot just run `start.ps1`).
- **Teacher signup code:** stored in `backend/.env` as `TEACHER_SIGNUP_CODE`.
  Needed to register a Faculty account; students don't need it. (Ask the repo
  owner for the current value — it's intentionally not committed to GitHub.)
- **AI provider:** Groq, model `openai/gpt-oss-120b`. Free tier has per-minute
  rate limits — if a whole class clicks "AI Hint" at once, some get a polite
  "try again" message.
- **Database:** a single SQLite file at `backend/ai_code_classroom.db`. Back it
  up by copying that file.
- **Secrets are safe:** `.env` and the database are gitignored, so the Groq key,
  JWT secret, and teacher code are **not** on GitHub.

---

## 11. Repository layout (where to find things)

```
0_Main_project/
├── backend/
│   ├── app/
│   │   ├── api/          # HTTP endpoints (auth, classrooms, problems, submissions, assignments, analytics, badges, learning)
│   │   ├── services/     # business logic (code_runner, scoring, badges, AI providers, tutor, leaderboard, ...)
│   │   ├── models/       # database tables (SQLAlchemy)
│   │   ├── schemas/      # request/response shapes (Pydantic)
│   │   ├── core/         # config, security (JWT/hashing), time helpers
│   │   └── main.py       # app entry point
│   ├── docker/python_runner/   # the sandbox image (Dockerfile)
│   ├── tests/            # 173 automated tests
│   └── .env              # secrets & config (NOT in git)
├── frontend/
│   └── src/
│       ├── pages/        # screens (public / student / teacher)
│       ├── components/   # reusable UI (navbar, sidebar, cards, coding panels)
│       ├── layouts/      # the app shell (navbar + sidebar + content)
│       ├── api/          # functions that call the backend
│       └── index.css     # the design system (collegiate theme tokens)
├── deploy/               # production deployment kit (cloud VM)
├── start.ps1 / stop.ps1 / start.cmd   # one-click run scripts (Windows)
└── PROJECT_OVERVIEW.md   # this file
```

---

## 12. The design / UI theme

The interface uses a deliberate **"collegiate" design system**: deep ink-navy as
the primary color, warm parchment backgrounds, academic burgundy as the teacher
accent, and collegiate gold for highlights — with a serif display font
(Fraunces) for headings to give it a refined, university feel. The whole look is
driven by a single set of design tokens in `frontend/src/index.css`, so the
entire product stays visually consistent. Students see navy accents; teachers
see burgundy. The UI is fully responsive (works on phones, with a slide-in
navigation drawer).

---

## 13. Quality & engineering notes (good talking points for the review)

- **173 automated backend tests** cover auth, submissions, scoring, assignments,
  analytics, the AI pipeline, and security rules.
- A **full security & correctness audit** was performed and ~30 issues fixed,
  including: authorization gaps (students/teachers accessing data they
  shouldn't), a deadline-bypass bug, a points double-award race condition,
  hidden-test-input leakage, timezone handling bugs, and resource leaks.
- The **AI provider is abstracted** so it can be swapped (Groq ↔ Gemini ↔ local
  Ollama) via config only.
- The database schema has a clean **Alembic migration baseline** and the app
  also auto-creates tables on startup, so it runs on a fresh machine with no
  manual DB setup.
- A **production deployment kit** exists (`deploy/`), so moving from the laptop
  demo to a real server is a single script.

---

*Document maintained for the Coder final-year project. If anything here is
unclear, the code is organized exactly as described in section 11, and the
backend's interactive API docs are available at `/docs` when running locally.*
