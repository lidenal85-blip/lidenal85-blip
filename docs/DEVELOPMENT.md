# Development Guide

## Setup

    python -m venv venv
    source venv/bin/activate
    pip install -e ".[dev]"
    cp .env.example .env

## Commands

    make help
    make install
    make dev
    make test
    make lint
    make format
    make clean

## Adding Adapter

1. Create src/survey_finder/adapters/<source>/adapter.py
2. Inherit BaseAdapter
3. Implement initialize(), fetch_surveys(), close()
4. Register in registry.py
5. Add tests
