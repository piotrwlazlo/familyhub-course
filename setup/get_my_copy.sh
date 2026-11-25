#!/bin/bash
# Each participant runs this ONCE, as themselves (takes a few seconds):
#     bash /srv/familyhub-course/get_my_copy.sh
# Result: ~/familyhub, your own copy of the code, starting at session 1. Open it in VS Code.
set -e
SHARED="$(cd "$(dirname "$0")" && pwd)"
DEST="${DEST:-$HOME/familyhub}"
if [ -e "$DEST" ]; then echo "$DEST already exists: nothing to do."; exit 0; fi
git clone -q "$SHARED/familyhub-app.bundle" "$DEST"      # the code with all golden states (gold-s1 ... gold-s8)
ln -s "$SHARED/venv" "$DEST/.venv"                 # the shared Python environment (read-only, nothing to install)
cd "$DEST"
git checkout -q -b my-work gold-s1
echo "Ready: $DEST   Open this folder in VS Code."
