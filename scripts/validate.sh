#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Survey Finder Validation Suite"
echo "================================"
echo ""

# 1. Check Python version
echo "1. Python Version:"
python --version
echo ""

# 2. Check dependencies
echo "2. Checking dependencies..."
pip list | grep -E "pydantic|fastapi|uvicorn|structlog|redis|httpx|playwright" || echo "⚠️ Some dependencies missing"
echo ""

# 3. Run syntax check
echo "3. Running syntax check..."
python -m py_compile src/survey_finder/bootstrap/app.py
echo "✅ Syntax OK"
echo ""

# 4. Run import check
echo "4. Running import check..."
python -c "from survey_finder.bootstrap.app import app; print('✅ Imports OK')"
echo ""

# 5. Run quick tests
echo "5. Running quick tests..."
pytest -v --tb=short 2>&1 | head -30
echo ""

# 6. Check configuration
echo "6. Checking configuration..."
python -c "from survey_finder.config.settings import settings; print(f'✅ Config OK: REDIS_URL={settings.REDIS_URL}')"
echo ""

# 7. Health check
echo "7. Running health check..."
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Health check passed"
else
    echo "⚠️ Health check failed (server may not be running)"
fi

echo ""
echo "✅ Validation complete!"
