#!/usr/bin/env bash
# Socratic Code-Tutor Pet - Single Startup Script (Bash)
# Usage: ./start.sh [--student-id "local-user"] [--dev-ui]

set -e
STUDENT_ID="local-user"
DEV_UI=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --student-id) STUDENT_ID="$2"; shift ;;
        --dev-ui) DEV_UI=true ;;
    esac
    shift
done

echo "=========================================================="
echo "       Starting Socratic Code-Tutor Pet Stack             "
echo "=========================================================="

# 1. Check Python
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "[ERROR] Python 3 is required."
    exit 1
fi
PYTHON_CMD=$(command -v python3 || command -v python)
echo "[OK] Python detected: $($PYTHON_CMD --version)"

# 2. Check Node & npm
if ! command -v npm &> /dev/null; then
    echo "[ERROR] Node.js & npm are required for the UI."
    exit 1
fi
echo "[OK] npm detected: $(npm --version)"

# 3. Check FalkorDB / Docker
echo -e "\n[*] Checking FalkorDB..."
FALKOR_ONLINE=false
if nc -z 127.0.0.1 6379 2>/dev/null; then
    echo "[OK] FalkorDB is running on localhost:6379."
    FALKOR_ONLINE=true
else
    echo "[*] FalkorDB not reachable on 6379. Attempting docker compose..."
    if command -v docker &> /dev/null; then
        docker compose up -d falkordb 2>/dev/null || true
        sleep 2
        if nc -z 127.0.0.1 6379 2>/dev/null; then
            echo "[OK] FalkorDB container launched via docker compose."
            FALKOR_ONLINE=true
        fi
    fi
    if [ "$FALKOR_ONLINE" = false ]; then
        echo "[WARN] Docker not available or FalkorDB offline."
        echo "       Daemon will use in-memory graph adapter with persistent disk caching."
    fi
fi

# 4. Check Ollama
echo -e "\n[*] Checking Ollama..."
if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "[OK] Ollama is active on http://localhost:11434."
    if curl -s http://localhost:11434/api/tags | grep -q "qwen2.5-coder"; then
        echo "[OK] Model 'qwen2.5-coder:7b' is available."
    else
        echo "[WARN] 'qwen2.5-coder:7b' not pulled yet. You can run: ollama pull qwen2.5-coder:7b"
    fi
else
    echo "[WARN] Ollama is offline or not installed."
    echo "       Tutor will use high-confidence Socratic seed questions and pattern heuristics."
fi

# 5. Ingest concepts and ensure demo student data
echo -e "\n[*] Preparing graph knowledge and student history..."
$PYTHON_CMD -c "import sys; sys.path.insert(0, 'daemon'); from adapters.graph_adapter import GraphAdapter; g = GraphAdapter(); g.ingest_concepts(); print('[OK] Concepts verified.')"
if [ ! -f "$HOME/.cache/tutor-pet/student_history.json" ]; then
    echo "[*] First run: seeding demo student history..."
    $PYTHON_CMD scripts/seed_demo_student.py --student-id "$STUDENT_ID"
fi

# 6. Start Daemon
echo -e "\n[*] Launching Socratic Tutor Daemon on http://127.0.0.1:7777..."
(cd daemon && $PYTHON_CMD -m uvicorn app:app --host 127.0.0.1 --port 7777) &
DAEMON_PID=$!
sleep 2

# Cleanup on exit
cleanup() {
    echo -e "\n[*] Stopping Tutor Pet services..."
    kill $DAEMON_PID 2>/dev/null || true
    if [ -n "$UI_PID" ]; then
        kill $UI_PID 2>/dev/null || true
    fi
    echo "[OK] All services stopped."
}
trap cleanup EXIT INT TERM

# 7. Start UI
echo -e "\n[*] Launching Socratic Pet UI..."
TAURI_EXE="ui/src-tauri/target/release/tutor-pet"
if [ "$DEV_UI" = false ] && [ -f "$TAURI_EXE" ]; then
    echo "[OK] Starting Tauri native desktop app..."
    "$TAURI_EXE" &
    UI_PID=$!
else
    echo "[OK] Starting UI via Vite server..."
    (cd ui && npm run dev -- --host 127.0.0.1) &
    UI_PID=$!
fi

echo "=========================================================="
echo " Socratic Code-Tutor Pet is running!"
echo "  * Daemon:    http://127.0.0.1:7777"
echo "  * UI Pet:    http://localhost:5173"
echo "  * Dashboard: http://localhost:5173/dashboard.html"
echo " Press Ctrl+C to stop all services."
echo "=========================================================="

wait
