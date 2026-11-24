#!/bin/bash
# Copy the application into the Open WebUI container and build the search index there.
# Usage: bash deploy_openwebui.sh [container name]   (default: ai-lab-webui)
# Then install familyhub_pipe.py in Open WebUI: Admin Panel > Functions.
set -e
CONTAINER=${1:-ai-lab-webui}
TARGET=/app/backend/data/familyhub-app
cd "$(dirname "$0")"
docker exec "$CONTAINER" rm -rf "$TARGET"
docker exec "$CONTAINER" mkdir -p "$TARGET"
tar cf - --exclude=.venv --exclude=index --exclude=.git --exclude=__pycache__ --exclude=tests --exclude=sessions . \
  | docker exec -i "$CONTAINER" tar xf - -C "$TARGET"
docker exec -w "$TARGET" "$CONTAINER" python search.py --build | tail -1
echo "Deployed to $CONTAINER:$TARGET"
