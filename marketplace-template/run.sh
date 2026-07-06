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
uvicorn main:app --reload --port "${BACKEND_PORT}" &
BACKEND_PID=$!
deactivate || true
cd ..

# Stop the backend when this script exits (Ctrl+C).
cleanup() { echo; echo "→ Shutting down…"; kill "${BACKEND_PID}" 2>/dev/null || true; }
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
npm run dev -- --port "${FRONTEND_PORT}"
