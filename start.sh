#!/bin/bash
# Run database migrations
uv run alembic upgrade head
# Start the bot
uv run uvicorn main:app --host 0.0.0.0 --port ${PORT:-8443}