#!/usr/bin/env bash
set -euo pipefail

# Health check script

ENDPOINT="${HEALTH_ENDPOINT:-http://localhost:8000/health}"
TIMEOUT="${TIMEOUT:-10}"

echo "🔍 Checking health: $ENDPOINT"

response=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$ENDPOINT")

if [ "$response" = "200" ]; then
    echo "✅ Health check passed (HTTP $response)"
    exit 0
else
    echo "❌ Health check failed (HTTP $response)"
    exit 1
fi
