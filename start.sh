#!/bin/bash
# Start Legal Document Assistant (API + UI)
echo "⚖️ Starting Legal Document Assistant..."

cd "$(dirname "$0")"
python3 -m uvicorn api:app --host 0.0.0.0 --port 8001 --reload &
API_PID=$!
echo "✅ API running at http://localhost:8001 (PID: $API_PID)"

cd ui
export PATH="$PATH:/opt/homebrew/bin"
npm run dev -- --port 3001 &
UI_PID=$!
echo "✅ UI running at http://localhost:3001 (PID: $UI_PID)"

echo ""
echo "🚀 Legal Assistant ready!"
echo "   UI  →  http://localhost:3001"
echo "   API →  http://localhost:8001/docs"
echo ""
echo "Press Ctrl+C to stop both servers"

trap "kill $API_PID $UI_PID 2>/dev/null; echo 'Stopped.'" EXIT INT
wait
