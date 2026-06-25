#!/usr/bin/env bash
set -euo pipefail

ROOT=$(pwd)

echo "=============================="
echo " SURVEY-FINDER SYSTEM SNAPSHOT"
echo "=============================="

echo ""
echo "1. PYTHON / ENV"
echo "----------------"
python --version || true
which python || true
echo "PYTHONPATH=${PYTHONPATH:-unset}"

echo ""
echo "2. PROJECT STRUCTURE"
echo "--------------------"
if command -v tree >/dev/null 2>&1; then
  tree -L 4 src || ls -R src
else
  ls -R src
fi

echo ""
echo "3. IMPORT HEALTH CHECK"
echo "----------------------"
python - << 'PYEOF'
import importlib
import pkgutil
import sys

base = "survey_finder"

print("Scanning package imports...\n")

errors = []

for module_info in pkgutil.walk_packages(["src"]):
    name = module_info.name
    if base in name:
        try:
            importlib.import_module(name)
            print(f"OK   {name}")
        except Exception as e:
            print(f"FAIL {name} -> {e}")
            errors.append((name, str(e)))

print("\nSUMMARY:")
print("Total failures:", len(errors))
PYEOF

echo ""
echo "4. CONFIG CHECK"
echo "---------------"
python - << 'PYEOF'
try:
    from survey_finder.config.settings import settings
    print("settings import: OK")
    print("REDIS_URL:", settings.REDIS_URL)
    print("POSTGRES_DSN:", settings.POSTGRES_DSN)
except Exception as e:
    print("settings import: FAIL", e)
PYEOF

echo ""
echo "5. CRITICAL SYMBOL CHECK"
echo "------------------------"

python - << 'PYEOF'
targets = [
    ("LeaderElectionService", "survey_finder.coordination.leader"),
    ("LeaseManager", "survey_finder.coordination.lease"),
    ("ExecutionController", "survey_finder.runtime.execution_controller"),
    ("ExecutionController", "survey_finder.execution.orchestrator.controller"),
    ("BackpressureBuffer", "survey_finder.execution.buffer.event_buffer"),
    ("IdempotencyGate", "survey_finder.execution.idempotency.gate"),
    ("CycleExecutionProtocol", "survey_finder.contracts.cep"),
]

for sym, mod in targets:
    try:
        m = __import__(mod, fromlist=[sym])
        getattr(m, sym)
        print(f"OK   {sym} -> {mod}")
    except Exception as e:
        print(f"FAIL {sym} -> {mod} -> {e}")
PYEOF

echo ""
echo "6. ENTRYPOINT CHECK (FastAPI)"
echo "-----------------------------"
python - << 'PYEOF'
try:
    from survey_finder.bootstrap.app import app
    print("FastAPI app import: OK")
    print("Routes:", len(app.routes))
except Exception as e:
    print("FastAPI app import: FAIL", e)
PYEOF

echo ""
echo "7. TEST DISCOVERY (NO RUN)"
echo "--------------------------"
pytest --collect-only -q 2>&1 | head -30 || true

echo ""
echo "8. GIT STATUS"
echo "-------------"
git status --short || true
echo ""
git log --oneline -5 || true

echo ""
echo "9. DEPENDENCY CHECK"
echo "-------------------"
pip list | grep -E "pydantic|fastapi|uvicorn|structlog|redis|httpx" || true

echo ""
echo "=============================="
echo " SNAPSHOT COMPLETE"
echo "=============================="
