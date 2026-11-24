#!/bin/bash
# Start the Family Hub API server (OpenAI-compatible).
#   bash run_app.sh                                                 port 8100, model from config.py
#   PORT=8101 bash run_app.sh                                       custom port
#   FAMILYHUB_MODEL_URL=http://10.100.64.2:8004/v1 bash run_app.sh  remote model endpoint
set -e
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
  .venv/bin/pip install -q openai pydantic chromadb rank_bm25
fi
.venv/bin/python -c "import fastapi, uvicorn" 2>/dev/null || .venv/bin/pip install -q fastapi uvicorn
[ -d index ] || .venv/bin/python search.py --build | tail -1
exec .venv/bin/uvicorn app:app --host 0.0.0.0 --port "${PORT:-8100}"
