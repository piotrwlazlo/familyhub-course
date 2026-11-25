#!/bin/bash
# Run ONCE on the GB10, by one person with sudo (for example the GB10 admin), before session 1:
#     sudo bash install_shared.sh
# It makes /srv/familyhub-course: the course package and one Python environment, read-only for everyone.
# Nobody edits anything in that folder: each participant takes their own copy with get_my_copy.sh.
set -e
TARGET="${TARGET:-/srv/familyhub-course}"
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$TARGET"
cp "$HERE/familyhub-app.bundle" "$HERE/get_my_copy.sh" "$TARGET/"
if [ ! -x "$TARGET/venv/bin/python" ]; then
  python3 -m venv "$TARGET/venv"
  "$TARGET/venv/bin/pip" install -q openai pydantic chromadb rank_bm25 ipykernel loguru fastapi uvicorn httpx pytest trafilatura
fi
chmod -R a+rX,go-w "$TARGET"
echo "Done. Each participant now runs, as themselves:   bash $TARGET/get_my_copy.sh"
