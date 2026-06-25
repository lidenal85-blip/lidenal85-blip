#!/usr/bin/env bash
set -euo pipefail

# Survey Finder Deployment Script

echo "🚀 Starting Survey Finder deployment..."

# Load environment
if [ -f .env ]; then
    source .env
fi

# Pull latest changes
echo "📦 Pulling latest changes..."
git pull origin main

# Build and start containers
echo "🐳 Building and starting containers..."
cd deployment/compose
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Run health check
echo "🔍 Running health check..."
if curl -s -f http://localhost:8000/health > /dev/null; then
    echo "✅ Health check passed!"
else
    echo "❌ Health check failed!"
    docker compose -f docker-compose.prod.yml logs --tail=50
    exit 1
fi

# Show status
echo "📊 Deployment status:"
docker compose -f docker-compose.prod.yml ps

echo "✅ Deployment complete!"
