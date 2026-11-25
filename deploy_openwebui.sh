#!/bin/bash
# INSTRUCTOR ONLY. Copies the application into the shared Open WebUI container and builds the search index there.
# Everyone who uses Open WebUI gets this version, so it replaces the version of everybody else.
# Run it only from the instructor's folder, with code that passes all session checks:
#     bash deploy_openwebui.sh --instructor [container name]      (default container: ai-lab-webui)
# Then in Open WebUI: Admin Panel > Functions, switch the Family Hub function off and on.
set -e
if [ "$1" != "--instructor" ]; then
  echo "STOP: this script replaces the Family Hub assistant in Open WebUI for EVERYONE."
  echo "Participants do not run it. Test your own version with your own service instead:"
  echo "    .venv/bin/uvicorn app:app --port <your port>"
  echo "The instructor deploys the team's version with:  bash deploy_openwebui.sh --instructor"
  exit 1
fi
CONTAINER=${2:-ai-lab-webui}
TARGET=/app/backend/data/familyhub-app
cd "$(dirname "$0")"
echo "Deploying $(pwd) to $CONTAINER:$TARGET (this replaces the shared version)"
docker exec "$CONTAINER" rm -rf "$TARGET"
docker exec "$CONTAINER" mkdir -p "$TARGET"
tar cf - --exclude=.venv --exclude=index --exclude=logs --exclude=.git --exclude=__pycache__ --exclude=tests \
  --exclude=sessions --exclude=staging --exclude=backup . \
  | docker exec -i "$CONTAINER" tar xf - -C "$TARGET"
docker exec -w "$TARGET" "$CONTAINER" python search.py --build | tail -1
echo "Deployed to $CONTAINER:$TARGET"
