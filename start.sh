#!/bin/sh
set -e

echo "✅ Starting AgentVerge..."
echo "✅ Python version:"
python --version

echo "✅ Checking uvicorn import"
python - <<EOF
import uvicorn
print("Uvicorn import OK")
EOF

echo "✅ Launching FastAPI"
exec python -m uvicorn main:app --host 0.0.0.0 --port 8080
