# Coder — Production Scaling & Cost Guide (for a real college deployment)

> **Purpose:** If a college wants to actually buy and run this platform for all
> its students (high traffic, always online, exam-day bursts), this document
> explains *what has to change*, *what it costs*, and *which option to pick*.
>
> Written in plain language for the team. All prices are **approximate monthly
> estimates** (late-2026) and will vary by provider and usage. USD figures first,
> rough INR in brackets at ~₹84 = $1.

---

## 1. The one thing that decides everything: running student code

Our app's special part is the **code judge** — it runs each student's code
inside a Docker sandbox. This is the heaviest part and it's what shapes the
cost. Three facts to keep in mind:

1. **It needs a real server with Docker.** Cheap "app hosts" like Render,
   Railway, or Vercel **cannot** run our judge (they don't give you Docker).
   So production must use a **rented cloud server (VM)** — which *does* give
   you Docker — or a dedicated code-execution service.
2. **It's CPU-heavy.** Each submission uses real CPU for a few seconds. 200
   students clicking "Submit" at the same minute (exam deadline) is the moment
   that decides how big a server you need.
3. **Good news:** our existing one-command deploy kit (`deploy/` folder)
   already targets a cloud VM with Docker. So the *cheapest* real option needs
   almost **no code change** — just a bigger server and a stronger database.

---

## 2. What has to change to go from "laptop demo" to "college product"

| # | Change | Why | Effort |
|---|--------|-----|--------|
| 1 | **Laptop → always-on cloud server** | 24/7 uptime, not tied to your laptop | Easy (deploy kit exists) |
| 2 | **SQLite → PostgreSQL** | SQLite can't handle many students writing at once | Easy (code is already Postgres-ready) |
| 3 | **1 backend worker → several** | Serve many users at once | Small (groundwork already done) |
| 4 | **Automatic daily backups** | Never lose student data | Easy |
| 5 | **Groq free tier → paid AI tier** | No rate limits when a whole class asks for hints | Config only |
| 6 | **A real domain + HTTPS** | e.g. `coder.yourcollege.edu` | Easy |
| 7 | **Monitoring + error alerts** | Know when something breaks | Easy |
| 8 | *(Heavy traffic only)* **Judge queue + worker pool** | Handle big exam-time bursts smoothly | Medium engineering |
| 9 | *(Optional)* **College login (Google/Microsoft SSO)** | Students use their college account | Medium |

Items 1–7 are straightforward. Item 8 is the real engineering work, and it's
only needed if the college is large and expects heavy simultaneous usage.

---

## 3. Three deployment options (pick by college size)

### OPTION A — Single powerful server  *(small–medium college, budget-friendly)*

Everything runs on **one strong rented VM** using Docker Compose: the backend
(a few workers), PostgreSQL, and the Docker judge — all on the same machine.
This runs essentially our **current code** with minimal change.

- **Good for:** up to ~500–1500 students, light-to-moderate exam bursts.
- **Risk:** during a very large simultaneous submission burst, submissions
  queue up and take longer (still works, just slower for a few minutes).

**Estimated cost:** **$50 – $130 / month**  (~₹4,000 – ₹11,000 / month)

| Item | Provider example | Monthly |
|------|-----------------|---------|
| 1 server, 8 CPU / 16 GB RAM | Hetzner (cheapest) / DigitalOcean | $35 – $90 |
| Automatic backups | provider add-on | $5 – $10 |
| Domain name | Namecheap/GoDaddy (~$12/yr) | ~$1 |
| Paid AI (Groq/Gemini, usage) | Groq / Google | $10 – $30 |
| **Total** | | **~$50 – $130** |

> Tip: **Hetzner** gives the most CPU per rupee and is ideal for Option A.
> DigitalOcean/Linode are slightly pricier but very beginner-friendly.

---

### OPTION B — Managed & load-balanced  *(large college, smooth under exam bursts)*

The grown-up setup. The judge runs as a **separate autoscaling pool of worker
servers** fed by a queue, so hundreds of simultaneous submissions are absorbed
smoothly. Database, cache, and backups are **managed services** (the provider
maintains them). This is what you'd run for a whole college seriously.

- **Good for:** 1,500 – 10,000+ students, heavy exam-day bursts, high uptime.
- **Needs:** the queue + worker-pool engineering (item 8 above) built first.

**Estimated cost:** **$250 – $500 / month**  (~₹21,000 – ₹42,000 / month),
and it can **autoscale higher only during exams** then shrink back to save money.

| Item | What it does | Monthly |
|------|--------------|---------|
| Load balancer | spreads users across servers | ~$12 |
| 2× backend servers | serve the website/API | ~$48 |
| Judge worker pool (2–4 CPU servers, autoscaled) | run student code | $100 – $200 |
| Managed PostgreSQL (with standby) | the database | $30 – $60 |
| Managed Redis | the submission queue/cache | ~$15 |
| Object storage + CDN | fast frontend worldwide | ~$5 |
| Backups + monitoring + alerts | safety & visibility | $15 – $40 |
| Paid AI (Groq/Gemini, higher usage) | hints & generation | $20 – $100 |
| Domain | the web address | ~$1 |
| **Total** | | **~$250 – $500** |

---

### OPTION C — Enterprise / multi-college  *(overkill for one college)*

Kubernetes cluster, multiple regions, high availability, dedicated DevOps.
Only relevant if this became a product sold to many colleges.
**Estimated cost:** **$800 – $2,500+ / month.** Not recommended now — listed
only for completeness.

---

## 4. One-time / yearly costs (on top of monthly)

| Item | Cost | Notes |
|------|------|-------|
| Domain name | ~$12 / year (~₹1,000) | Renewed yearly |
| HTTPS certificate | **Free** | Let's Encrypt, auto-renews |
| Engineering to productionize (Option A) | **Low** | Mostly config; deploy kit exists |
| Engineering to build the judge queue (Option B) | **One-time dev work** | The main effort if going big |
| Optional: college SSO integration | One-time dev work | If they want college-account login |

If the college has its own IT team, items above are their staff time. If they
hire a developer, it's a one-time project fee (varies widely by region).

---

## 5. Our honest recommendation

**Start with Option A.** It uses the code and deploy kit we already have, costs
about the price of a few pizzas a month, and comfortably serves a typical
college department. Switch to **Option B only when real usage proves you need
it** (e.g. you see submissions lagging during big exams). Don't pay for Option
B's complexity before the traffic actually demands it.

**Suggested first real deployment (Option A):**
1. Rent one Hetzner/DigitalOcean server (8 CPU / 16 GB).
2. Point a college domain at it (`coder.college.edu`).
3. Run our `deploy/setup-server.sh` (installs Docker, HTTPS, the app).
4. Switch the database setting to a managed PostgreSQL.
5. Put the paid Groq/Gemini key in the config.
6. Turn on daily database backups.

That's a real, always-on, HTTPS product for roughly **$50–130/month**, built on
exactly what we already have — no laptop, no tunnel, no rewrite.

---

## 6. Quick answer for the review panel

> *"The platform runs today on a laptop via a secure tunnel for demos. For a
> real college deployment it moves to a cloud server (which, unlike free app
> hosts, supports our Docker-based code judge), with PostgreSQL and paid AI.
> A small college runs comfortably for about $50–130/month using our existing
> deployment scripts; a large college with heavy exam-time load uses an
> autoscaling judge-worker setup for roughly $250–500/month. The architecture
> is designed to scale from one to the other without rewriting the app."*

---

*Prices are estimates for planning only; always check current provider pricing.
The `deploy/` folder in this repo already contains the Option-A deployment
scripts.*
