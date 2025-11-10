# Deploy the existing polling bot (no code changes)

This keeps exactly what works with `start_bot.bat` (runs `bot_neon.py` with long polling).
Serverless (Vercel) cannot run long-polling loops, so use one of:

- Render (free worker process)
- Railway (service with Python)
- Any VPS/VM (Windows/Linux) as a background service

## 1) Render (recommended free option)

Prereqs: GitHub repo connected.

Option A — using the included `render.yaml` (monorepo friendly):

1. Push these files if not already in your repo: `anon-board-bot/Procfile`, `render.yaml`, `anon-board-bot/.env.example`.
2. Open https://render.com > New + > Blueprint.
3. Point to your repository.
4. It will detect the worker `neon-telegram-bot` at `anon-board-bot/`.
5. Set environment variables:
   - TELEGRAM_BOT_TOKEN: your bot token
   - VERCEL_API_URL: https://anonimka.kz (or your domain)
6. Create Resources. Build will:
   - pip install -r anon-board-bot/requirements.txt
   - start with `python bot_neon.py`
7. Confirm the worker is running (“Live”).

Option B — manual worker:

1. New + > Worker > Build from repo.
2. Root Directory: `anon-board-bot`.
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python bot_neon.py`
5. Add env vars as above and Create.

## 2) Railway

1. New Project > Deploy from GitHub (pick your repo).
2. Service Settings:
   - Nixpacks auto-detects Python from `requirements.txt`.
   - Start Command: `python bot_neon.py` (set explicitly under Variables/Start Command).
3. Add variables:
   - TELEGRAM_BOT_TOKEN, VERCEL_API_URL.
4. Deploy. Ensure the service stays up. Enable auto-redeploy on push if desired.

## 3) Run 24/7 on Windows (no cloud)

If you want to keep it on your PC/server exactly like `start_bot.bat`:

A) As a Windows service (NSSM):

- Download NSSM from https://nssm.cc/download and extract.
- Open PowerShell as Administrator:

```
# Adjust paths to your machine
nssm install NeonBot "E:\my project\app chat\.venv\Scripts\python.exe" "E:\my project\app chat\anon-board-bot\bot_neon.py"
# Set Startup directory to E:\my project\app chat\anon-board-bot
# Set AppStdout/AppStderr to a log file path if you want logs
nssm start NeonBot
```

B) Via Task Scheduler (auto-start on boot):

- Create Task > Run whether user is logged on or not.
- Trigger: At startup (and optionally on logon).
- Action: Start program:
  - Program/script: `E:\my project\app chat\.venv\Scripts\python.exe`
  - Arguments: `bot_neon.py`
  - Start in: `E:\my project\app chat\anon-board-bot`

Ensure a `.env` file exists in `anon-board-bot` with `TELEGRAM_BOT_TOKEN` (and optional `VERCEL_API_URL`).

## Notes

- No webhook needed. This uses `application.run_polling(...)` as-is.
- Keep your token secret. Do NOT commit `.env`.
- If you later want Vercel-only hosting, you must migrate to webhooks (already scaffolded separately in Next.js).
