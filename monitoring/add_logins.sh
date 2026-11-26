#!/bin/bash
# ONLY the person who started the monitoring (part A of sessions/s12/task.md).
# Give each person in the team a Grafana login and a folder that only they can change.
#   bash add_logins.sh <name> [<name> ...]      e.g.  bash add_logins.sh anna tom
# Everybody can look at every dashboard, but change only the ones in their own folder.
# Running it again for an existing name changes nothing for that name.
set -e
cd "$(dirname "$0")"
[ $# -ge 1 ] || { echo "usage: bash add_logins.sh <name> [<name> ...]"; exit 1; }
[ -f .env ] || { echo "STOP: no .env here (the Grafana admin password). Do step A4 of sessions/s12/task.md first."; exit 1; }
source .env
GRAFANA=${GRAFANA_URL:-http://127.0.0.1:3001}
api() {  # api METHOD PATH [JSON]  -> prints the body, fails on HTTP errors
  curl -sS --fail-with-body -u "admin:$GRAFANA_ADMIN_PASSWORD" -H "Content-Type: application/json" \
       -X "$1" "$GRAFANA$2" ${3:+-d "$3"}
}
json() { python3 -c "import json,sys; print(json.load(sys.stdin)$1)"; }

touch learners.txt && chmod 600 learners.txt
for raw in "$@"; do
  name=$(echo "$raw" | tr '[:upper:]' '[:lower:]')
  if api GET "/api/users/lookup?loginOrEmail=$name" >/dev/null 2>&1; then
    echo "$name: already has a login, nothing changed"
    continue
  fi
  password=$(openssl rand -base64 18 | tr -d '/+=' | cut -c1-12)
  id=$(api POST /api/admin/users "{\"name\":\"$name\",\"login\":\"$name\",\"email\":\"$name@localhost\",\"password\":\"$password\"}" | json "['id']")
  api POST /api/folders "{\"uid\":\"learner-$name\",\"title\":\"$name\"}" >/dev/null
  # Only this person may edit the folder; everybody else (Viewer) may look.
  api POST "/api/folders/learner-$name/permissions" \
      "{\"items\":[{\"userId\":$id,\"permission\":2},{\"role\":\"Viewer\",\"permission\":1}]}" >/dev/null
  echo "$name  $password" >> learners.txt
  echo "$name: login created, folder '$name' created"
done
echo
echo "Logins and first passwords are in learners.txt (only you can read it). Give each person their line;"
echo "they change the password in Grafana: profile picture > Profile > Change password."
