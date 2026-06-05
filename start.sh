#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "📖 Flipbook — Starting up..."

# ── Check dependencies ──────────────────────────────────
check_cmd() {
  if ! command -v "$1" &>/dev/null; then
    echo "❌ $1 not found. Please install it first."
    echo "   pip install $2"
    echo "   or:  npm install $3"
    exit 1
  fi
}

# ── Backend ─────────────────────────────────────────────
echo ""
echo "🔧 Starting backend (FastAPI)..."

# Install Python deps if needed
if ! python3 -c "import uvicorn" 2>/dev/null; then
  echo "📦 Installing Python dependencies..."
  pip install -q fastapi uvicorn pillow httpx pydantic
fi

# Start backend in background
python3 -m uvicorn server.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload \
  --reload-dir server \
  &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID (http://localhost:8000)"

# ── Frontend ────────────────────────────────────────────
echo ""
echo "🎨 Starting frontend (Vite)..."

cd client

# Install npm deps if needed
if [ ! -d "node_modules" ]; then
  echo "📦 Installing npm dependencies..."
  npm install
fi

# Start frontend
npx vite --host 0.0.0.0 --port 3000 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID (http://localhost:3000)"

cd "$SCRIPT_DIR"

# ── Cleanup ─────────────────────────────────────────────
cleanup() {
  echo ""
  echo "🛑 Shutting down..."
  kill $BACKEND_PID 2>/dev/null
  kill $FRONTEND_PID 2>/dev/null
  wait 2>/dev/null
  echo "👋 Bye!"
}

trap cleanup EXIT INT TERM

echo ""
echo "✅ Flipbook is running!"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop."

# Wait for either process to exit
wait -n 2>/dev/null || wait
