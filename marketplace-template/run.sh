#!/usr/bin/env bash
#
# One-command bootstrap for the marketplace template (macOS / Linux).
#
#   ./run.sh
#
# It installs both halves (Python backend + Node frontend) on first run and
# starts both servers. No API keys required — it comes up in the zero-setup
# "mock" matchmaker mode. Press Ctrl+C once to stop both.
#
# Windows users: run the two halves manually (see docs/SETUP.md) — this script
# needs bash. Git Bash or WSL will also work.

set -euo pipefail
cd "$(dirname "$0")"

BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

# Keep the two halves in sync when the ports are overridden:
#   • the browser must fetch the backend at its actual port (PUBLIC_API_BASE), and
#   • the backend must allow the frontend's actual origin through CORS.
# With the defaults these are already covered, so overriding a port Just Works.
export PUBLIC_API_BASE="http://localhost:${BACKEND_PORT}"
export FRONTEND_ORIGINS="http://localhost:${FRONTEND_PORT},http://127.0.0.1:${FRONTEND_PORT}"

need() { command -v "$1" >/dev/null 2>&1 || { echo "✗ '$1' is not installed. See docs/SETUP.md for how to install it."; exit 1; }; }
echo "→ Checking prerequisites…"
need python3
need node
need npm
echo "  ✓ python3 $(python3 --version 2>&1 | awk '{print $2}') · node $(node --version) · npm $(npm --version)"

# ── Backend ───────────────────────────────────────────────────────────────────
echo "→ Setting up the backend (http://localhost:${BACKEND_PORT})…"
cd backend
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
# Run WITHOUT --reload here: this is a "just run it" launcher, not an edit loop,
# and a single uvicorn process is cleanly reaped by the trap below (--reload's
# extra reloader/worker child can outlive a kill of the parent PID). For
# hot-reload during development, start the backend by hand (see docs/SETUP.md).
uvicorn main:app --port "${BACKEND_PORT}" &
BACKEND_PID=$!
deactivate || true
cd ..

# Stop BOTH halves when this script exits (Ctrl+C), and wait to reap them so
# nothing is left holding a port. Runs at most once (some shells fire both INT
# and EXIT). FRONTEND_PID is set once the frontend starts, below.
FRONTEND_PID=""
_cleaned=""
cleanup() {
  [ -n "${_cleaned}" ] && return
  _cleaned=1
  echo
  echo "→ Shutting down…"
  [ -n "${FRONTEND_PID}" ] && kill "${FRONTEND_PID}" 2>/dev/null || true
  kill "${BACKEND_PID}" 2>/dev/null || true
  wait "${BACKEND_PID}" "${FRONTEND_PID}" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# ── Frontend ──────────────────────────────────────────────────────────────────
echo "→ Setting up the frontend (http://localhost:${FRONTEND_PORT})…"
cd frontend
if [ ! -d node_modules ]; then
  npm install
fi
echo
echo "════════════════════════════════════════════════════════════════════"
echo "  Marketplace is starting."
echo "  Open →  http://localhost:${FRONTEND_PORT}"
echo "  API  →  http://localhost:${BACKEND_PORT}/api/health"
echo "  Press Ctrl+C to stop."
echo "════════════════════════════════════════════════════════════════════"
echo

# Run the frontend in the background too, so the Ctrl+C trap can stop BOTH halves
# (otherwise the frontend, as the foreground process, would keep running and the
# cleanup could never reach it). `wait -n` blocks until either half exits; if one
# dies, we fall through to cleanup and tear the other down as well.
npm run dev -- --port "${FRONTEND_PORT}" &
FRONTEND_PID=$!

wait -n 2>/dev/null || wait "${BACKEND_PID}" "${FRONTEND_PID}" 2>/dev/null || true
