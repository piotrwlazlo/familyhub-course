#!/bin/bash
# ONLY the person who started the monitoring (part A of sessions/s12/task.md). Remove the monitoring stack completely: containers, collected data, dashboards,
# Grafana logins, images, the admin password file and the password list. Your model is not touched.
#   bash cleanup.sh --yes
set -e
cd "$(dirname "$0")"
if [ "$1" != "--yes" ]; then
  echo "This deletes Prometheus, Grafana, every dashboard the participants built and all collected data."
  echo "Run again with --yes to do it:  bash cleanup.sh --yes"
  exit 1
fi
GRAFANA_ADMIN_PASSWORD=unused docker compose down --volumes --rmi all
rm -f .env learners.txt
echo "Left over (should be empty):"
docker ps -a --filter name=familyhub-prometheus --filter name=familyhub-grafana --format '{{.Names}}'
docker volume ls --filter name=familyhub-monitoring --format '{{.Name}}'
echo "Done. The files in this folder stay, so you can start again from step 1."
