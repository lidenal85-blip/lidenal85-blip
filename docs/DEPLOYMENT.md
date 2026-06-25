# Deployment Guide

## Docker Compose

    # Development
    make docker-up-dev

    # Production
    cp .env.production.example .env
    make deploy

## Systemd

    sudo cp deployment/systemd/survey-finder.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable survey-finder
    sudo systemctl start survey-finder

## Commands

    make health   # Health check
    make logs     # View logs
    make backup   # Create backup
