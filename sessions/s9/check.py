"""Session 9 check: your unit tests pass and catch broken code, the real bug is fixed,
and your smoke test passes against the running service.

Run from your main folder:  python sessions/s9/check.py   (about 1 minute, the model is needed for the smoke test)
"""
import socket
import subprocess
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # the sessions folder
sys.path.insert(0, str(Path(__file__).resolve().parent))          # this folder (hunt.py)

from common import APP, finish  # noqa: E402  (also sets up the paths and the fixed date)

import httpx  # noqa: E402

import hunt  # noqa: E402

MIN_TESTS = 8
MIN_SMOKE_CHECKS = 4
passed = 0

# 1. Unit tests
tests_file = APP / "tests" / "test_units.py"
count = tests_file.read_text(encoding="utf-8").count("def test_") if tests_file.exists() else 0
ok = count >= MIN_TESTS
passed += ok
print(f"{'PASS' if ok else 'FAIL'} | at least {MIN_TESTS} unit tests in tests/test_units.py (you have {count})\n")

caught, total, alive = hunt.hunt()
ok = caught == total
passed += ok
print(f"\n{'PASS' if ok else 'FAIL'} | your unit tests catch {caught} of {total} broken versions")

# 2. The real bug
from fastapi.testclient import TestClient  # noqa: E402
import app  # noqa: E402
try:
    status = TestClient(app.app).post("/v1/chat/completions", json={"messages": []}).status_code
except Exception as error:            # the bug: the service crashes
    status = f"crash ({type(error).__name__})"
ok = status == 400
passed += ok
print(f"{'PASS' if ok else 'FAIL'} | the real bug is fixed: an empty message list gets 400 (got {status})")

# 3. The smoke test against the running service
smoke = APP / "tests" / "smoke_test.py"
checks_written = smoke.read_text(encoding="utf-8").count("\ncheck(") if smoke.exists() else 0
ok = False
if checks_written < MIN_SMOKE_CHECKS:
    print(f"FAIL | at least {MIN_SMOKE_CHECKS} checks in tests/smoke_test.py (you have {checks_written})")
else:
    with socket.socket() as free:
        free.bind(("127.0.0.1", 0))
        port = free.getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    server = subprocess.Popen([sys.executable, "-m", "uvicorn", "app:app", "--port", str(port)], cwd=APP,
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        for _ in range(60):                       # wait until the service answers (index and model loading)
            try:
                httpx.get(f"{url}/v1/models", timeout=2)
                break
            except httpx.HTTPError:
                time.sleep(1)
        print(f"\nYour smoke test against the service on port {port}:")
        ok = subprocess.run([sys.executable, str(smoke), url], cwd=APP, timeout=300).returncode == 0
    finally:
        server.terminate()
        server.wait(timeout=10)
    print(f"{'PASS' if ok else 'FAIL'} | your smoke test passes against the running service")
passed += ok

finish(passed, 4)
