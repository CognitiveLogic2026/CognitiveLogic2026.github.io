#!/bin/bash
# Copyright (c) 2026 Roberto Bob Malini - Cognitive Logic
# https://www.cognitivelogic.it
# Licensed under CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)
set -e
PROJECT_ROOT="/root/qen-framework"
echo "=================================="
echo "QEN Bolkestein S4 - Deployment"
echo "=================================="
echo ""
echo "→ Copying S4 deployment script..."
cp ./qen_bolkestein_s4.py "$PROJECT_ROOT/"
chmod +x "$PROJECT_ROOT/qen_bolkestein_s4.py"
echo "✓ S4 script ready"
echo ""
echo "→ Checking Python venv..."
if [ ! -d "$PROJECT_ROOT/venv" ]; then
    cd "$PROJECT_ROOT"
    python3 -m venv venv
fi
echo "✓ venv ready"
echo ""
echo "→ Installing dependencies..."
source "$PROJECT_ROOT/venv/bin/activate"
pip install -q fastapi uvicorn python-dotenv requests 2>/dev/null || true
echo "✓ Dependencies ready"
echo ""
mkdir -p "$PROJECT_ROOT/logs"
echo "→ Running S4 deployment..."
echo ""
python3 "$PROJECT_ROOT/qen_bolkestein_s4.py"
echo ""
echo "✓ Deployment complete!"
