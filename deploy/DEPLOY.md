# Deploying Coder to a free Oracle Cloud VM

Target: Oracle Cloud **Always Free** tier — a permanently free ARM VM
(up to 4 OCPUs / 24 GB RAM) that supports Docker, so the code-execution
sandbox works exactly like it does locally.

Final architecture on the VM:

```
Internet ──HTTPS──> Caddy (auto Let's Encrypt)
                      ├── /          → built React app (static files)
                      └── /api/*     → FastAPI (systemd service, localhost:8100)
                                          └── docker run python-runner  (per submission)
AI calls ──────────> Groq hosted API (no Ollama on the server)
```

---

## 1. Create the VM (one time, ~15 min)

1. Sign up at https://cloud.oracle.com/free (credit card for identity check;
   Always Free resources never charge).
2. **Create a VM instance**: Compute → Instances → Create.
   - Image: **Ubuntu 24.04** (aarch64).
   - Shape: **VM.Standard.A1.Flex** — give it 2–4 OCPUs and 8–24 GB RAM
     (all within Always Free). If "out of capacity", try another
     availability domain or retry later; it's a known free-tier quirk.
   - Add your SSH public key.
3. **Open the firewall in the cloud console**: Networking → Virtual Cloud
   Networks → your VCN → the subnet's **Security List** → Add Ingress Rules:
   - Source `0.0.0.0/0`, TCP port `80`
   - Source `0.0.0.0/0`, TCP port `443`
4. Note the instance's **public IP**.

## 2. Get a free domain (needed for HTTPS, ~2 min)

1. Go to https://www.duckdns.org, sign in, create a subdomain
   (e.g. `coder-demo`), and point it at your VM's public IP.
2. Your app will live at `https://coder-demo.duckdns.org`.

## 3. Install the app (one command)

SSH in and run:

```bash
ssh ubuntu@<VM_PUBLIC_IP>

sudo git clone https://github.com/rohnroy0/coder.git /opt/coder
cd /opt/coder
sudo bash deploy/setup-server.sh coder-demo.duckdns.org
```

The script is idempotent (safe to re-run) and does everything: Docker,
Caddy, Node, Python venv, builds the sandbox image and the frontend,
generates a strong `SECRET_KEY` and a `TEACHER_SIGNUP_CODE`, installs the
systemd service, configures HTTPS, and opens the host firewall.

## 4. Add your Groq key (the one thing it can't do for you)

```bash
sudo nano /opt/coder/backend/.env     # set AI_API_KEY=gsk_...
sudo systemctl restart coder-backend
```

## 5. Verify

- Open `https://your-subdomain.duckdns.org` — register a student, solve a
  problem, click **Get AI Hint**.
- Register a teacher using the **teacher signup code** the script printed
  (re-print it any time: `sudo grep TEACHER_SIGNUP_CODE /opt/coder/backend/.env`).

---

## Day-2 operations

| Task | Command (on the VM) |
|---|---|
| Deploy latest code | `sudo bash /opt/coder/deploy/update.sh` (backs up the DB first) |
| Backend logs | `sudo journalctl -u coder-backend -f` |
| Restart backend | `sudo systemctl restart coder-backend` |
| Manual DB backup | `sudo cp /opt/coder/backend/ai_code_classroom.db ~/db-backup.sqlite` |
| Nightly DB backups | `echo '0 3 * * * root cp /opt/coder/backend/ai_code_classroom.db /opt/coder/backups/db-$(date +\%F).sqlite' \| sudo tee /etc/cron.d/coder-backup` |
| Swap AI provider | edit `AI_PROVIDER_TYPE`/`AI_API_KEY` in `backend/.env`, restart backend |

## Notes & limits

- **Single uvicorn worker by design**: scoring uses an in-process lock and
  the DB is SQLite. Plenty for a class-sized user base. If you ever outgrow
  it: move `DATABASE_URL` to PostgreSQL first, then raise `--workers`.
- **API docs** (`/docs`) are deliberately not exposed publicly. View them
  via an SSH tunnel: `ssh -L 8100:127.0.0.1:8100 ubuntu@<IP>` then open
  `http://localhost:8100/docs`.
- **Groq free tier**: per-minute rate limits. If a whole class clicks
  "Get AI Hint" in the same minute, some get a clean "try again later".
  Paid Groq (or a second key on `gemini`) removes the ceiling.
- The local Windows `start.ps1` workflow is unaffected — it remains your
  development environment.
