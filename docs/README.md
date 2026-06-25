# Survey Finder

Production-grade survey monitoring system with multi-source survey
aggregation, smart filtering, and Telegram notifications.

## Features

- Multi-source monitoring — Prolific, CloudResearch, Respondent
- Smart filtering — Explainable eligibility decisions with score
- Idempotent delivery — No duplicate notifications
- Observability — Metrics, structured logging, health checks
- Production hardened — Circuit breakers, rate limiting, graceful shutdown
- Docker ready — Easy deployment with Docker Compose
- DLQ — Dead Letter Queue for failed items with replay

## Quick Start

    git clone https://github.com/lidenal85-blip/lidenal85-blip.git
    cd survey-finder
    make install
    make dev

## Configuration

    cp .env.example .env
    # Edit .env with your values

Required:

- TELEGRAM_BOT_TOKEN
- TELEGRAM_CHAT_ID
- POSTGRES_DSN
- REDIS_URL

## Testing

    make test

## Monitoring

- Health: http://localhost:8000/health
- Cycle status: http://localhost:8000/cycle/status

## License

MIT
