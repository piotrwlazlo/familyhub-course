"""Session 12 check: your own dashboard in Grafana shows the four things the team watches.

Run from your main folder:  python sessions/s12/check.py
It asks for your Grafana login and password (the password is not saved anywhere).
Grafana address: http://127.0.0.1:3001, or set GRAFANA_URL if the instructor gave you another one.
"""
import getpass
import os
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common import finish  # noqa: E402

GRAFANA = os.environ.get("GRAFANA_URL", "http://127.0.0.1:3001").rstrip("/")
NEEDED = {   # what the panel queries must use: the name of the thing in the check -> part of the metric name
    "tokens per second": "generation_tokens",
    "requests running or waiting": "num_requests_",
    "time to first token": "time_to_first_token",
    "KV cache use": "kv_cache_usage",
}
passed, total = 0, 4


def report(ok: bool, text: str) -> None:
    global passed
    passed += ok
    print(f"{'PASS' if ok else 'FAIL'} | {text}")


def all_panels(panels: list) -> list:
    """Panels, including the ones inside collapsed rows."""
    found = []
    for panel in panels:
        found.append(panel)
        found += panel.get("panels", [])
    return found


def has_data(client: httpx.Client, expr: str, datasource: dict) -> bool:
    """True if the query returns at least one number above 0 in the last 30 minutes."""
    body = {"from": "now-30m", "to": "now", "queries": [{
        "refId": "A", "datasource": datasource, "expr": expr, "range": True, "intervalMs": 15000, "maxDataPoints": 120}]}
    reply = client.post("/api/ds/query", json=body)
    if reply.status_code != 200:
        return False
    for frame in reply.json().get("results", {}).get("A", {}).get("frames", []):
        values = frame.get("data", {}).get("values", [])
        if len(values) > 1 and any(isinstance(v, (int, float)) and v > 0 for v in values[1]):
            return True
    return False


login = (os.environ.get("GRAFANA_LOGIN") or input(f"Grafana login [{getpass.getuser()}]: ").strip() or getpass.getuser()).lower()
password = os.environ.get("GRAFANA_PASSWORD") or getpass.getpass("Grafana password: ")
client = httpx.Client(base_url=GRAFANA, auth=(login, password), timeout=30)

try:
    me = client.get("/api/user")
except httpx.HTTPError as error:
    print(f"FAIL | cannot reach Grafana at {GRAFANA}: {error}")
    finish(0, total)
report(me.status_code == 200, f"log in to Grafana as {login}")
if me.status_code != 200:
    finish(passed, total)

found = client.get("/api/search", params={"type": "dash-db", "folderUIDs": f"learner-{login}"}).json()
if not found:
    report(False, f"a dashboard saved in your folder '{login}' (none found: did you press Save, in your folder?)")
    finish(passed, total)
report(True, f"a dashboard saved in your folder: {', '.join(item['title'] for item in found)}")

queries = []          # (panel title, expr, datasource)
for item in found:
    dashboard = client.get(f"/api/dashboards/uid/{item['uid']}").json()["dashboard"]
    for panel in all_panels(dashboard.get("panels", [])):
        for target in panel.get("targets", []):
            if target.get("expr"):
                source = target.get("datasource") or panel.get("datasource") or {"uid": "prometheus"}
                if not isinstance(source, dict) or source.get("uid", "").startswith("$"):
                    source = {"uid": "prometheus"}
                queries.append((panel.get("title", ""), target["expr"], source))

missing = [what for what, metric in NEEDED.items() if not any(metric in expr for _, expr, _ in queries)]
report(not missing, "panels for tokens per second, requests, time to first token and KV cache"
       + (f" (missing: {', '.join(missing)})" if missing else ""))

speed = [(title, expr, source) for title, expr, source in queries if "generation_tokens" in expr]
moving = any(has_data(client, expr, source) for _, expr, source in speed)
report(moving, "your tokens-per-second panel shows traffic in the last 30 minutes"
       + ("" if moving else " (no data yet: run python sessions/s12/load.py and check again)"))
finish(passed, total)
