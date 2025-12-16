# ASK WhatsApp Bot

A FastAPI-powered chatbot that receives WhatsApp messages (via pywa), relays them to an ASK agent, and persists per-user conversation state in PostgreSQL.

## Overview

### Conversation Flow

1. User sends a text message on WhatsApp
2. Webhook persists/looks up `users` row (conversation ID + last interaction time)
3. Conversation resets automatically when `/new` is received or the last reply is older than `SESSION_TIMEOUT` minutes
4. Text is sent to ASK. Markdown responses are relayed back to WhatsApp via pywa

**Note:** Conversation history is not stored in the app; only `conversation_id`, `phone_number`, and `last_interaction` time are persisted.

### Tech Stack

- **FastAPI** – Webhook + health endpoints
- **pywa** – WhatsApp Cloud API client (sending/receiving messages)
- **ASK API** – Conversational intelligence (`POST /v1/conversations/`)
- **SQLAlchemy + Alembic + asyncpg** – Async PostgreSQL access and migrations
- **uv** – Fast Python package and project manager

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) installed on PATH
- PostgreSQL 15+ (or any Postgres-compatible service)
- Docker + Docker Compose (for containerized deployment)
- WhatsApp Cloud API account with:
  - Phone number ID
  - Permanent access token
  - App ID and App Secret
- [ASK](https://ask.stg.ai71.ai/) account with:
  - Provisioned agent
  - API key

Refer ASK [docs](https://ask.stg.ai71.ai/docs)

## Quick Start

### 1. Environment Setup

Create a `.env` file based on `env.example`:

```bash
cp env.example .env
```

Then configure the following variables:

#### Core Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `AGENT_ID` | ASK agent identifier | Yes | - |
| `ASK_API_KEY` | ASK API key | Yes | - |
| `ASK_API_BASE` | ASK API base URL | No | `https://api.ask.stg.ai71services.ai` |

#### WhatsApp Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `WHATSAPP_TOKEN` | WhatsApp permanent access token | Yes | - |
| `WHATSAPP_PHONE_ID` | WhatsApp phone number ID | Yes | - |
| `WHATSAPP_APP_ID` | WhatsApp App ID (for webhook validation) | Yes | - |
| `WHATSAPP_APP_SECRET` | WhatsApp App secret (for HMAC validation) | Yes | - |
| `VERIFY_TOKEN` | Token for webhook verification (`hub.verify_token`) | Yes | - |
| `WEBHOOK_URL` | Public URL for webhook (e.g., `https://bot.example.com/webhook`) | Yes | - |

#### Application Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `PORT` | Port to expose the FastAPI application | No | `8443` |
| `SESSION_TIMEOUT` | Minutes of inactivity before conversation reset | No | `60` |

#### Database Configuration

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string  | Yes* | - |
| `DB_PASSWORD` | Database password (for Docker Compose only) | Yes** | `changeme` |

\* Required for local development or when not using docker compose  
\*\* Required when using Docker Compose (automatically constructs `DATABASE_URL`)

**Example `DATABASE_URL` format:**
```
postgresql+asyncpg://user:password@localhost:5432/ask_whatsapp_bot
```

#### Webhook Configuration

Your `WEBHOOK_URL` must be publicly accessible (use ngrok, reverse proxy, or cloud deployment). Configure the same URL and `VERIFY_TOKEN` in the Meta App dashboard. All incoming POST requests to this URL must be forwarded to this service.

### 2. Running with Docker Compose (Recommended)

Docker Compose automatically sets up both the application and PostgreSQL database.

#### Start the Services

```bash
docker compose up --build
```

This command:
- Builds the FastAPI bot and exposes it on port `8443`
- Starts a PostgreSQL 15 instance on port `5432`
- Automatically runs database migrations on startup
- Sets up persistent volume for database data

#### View Logs

```bash
# Watch application logs
docker compose logs -f bot

# Watch all services
docker compose logs -f
```

#### Stop the Services

```bash
docker compose down

# To remove volumes as well
docker compose down -v
```

**Note:** The default database password is `changeme`. Update `DB_PASSWORD` in your `.env` for production deployments.

### 3. Running Locally (Development)

For local development without Docker:

#### Install Dependencies

```bash
uv sync
```

This creates a `.venv/` directory and installs all dependencies from `pyproject.toml`.

#### Configure Database

Ensure PostgreSQL is running and update `DATABASE_URL` in your `.env`:

```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/ask_whatsapp_bot
```

#### Load Environment Variables

```bash
export $(grep -v '^#' .env | grep -v '^$' | xargs)
```

#### Run Database Migrations

```bash
uv run alembic upgrade head
```

#### Start the Application

```bash
./start.sh
```

Or manually:

```bash
uv run uvicorn main:app --host 0.0.0.0 --port ${PORT:-8443}
```

## Database Management

### Apply Migrations

```bash
uv run alembic upgrade head
```

### Create New Migrations

After modifying models in `app/models.py`:

```bash
uv run alembic revision --autogenerate -m "describe your change"
```

Then review the generated migration file in `migrations/versions/` before applying it.

### Rollback Migrations

```bash
# Rollback one version
uv run alembic downgrade -1

# Rollback to specific version
uv run alembic downgrade <revision_id>
```

## API Endpoints

### Health Check

```
GET /health
```

Returns `{"status": "ok"}` for readiness probes.

### Webhook Endpoint

```
POST /webhook
GET /webhook  (for verification)
```

Receives WhatsApp messages and events. This endpoint is automatically configured via `WEBHOOK_URL`.

## Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── ask_service.py       # ASK API integration
│   ├── commands.py          # WhatsApp command handlers
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection
│   ├── error_handlers.py    # Error handling
│   ├── models.py            # SQLAlchemy models
│   └── utils.py             # Utility functions
├── migrations/              # Alembic migrations
├── main.py                  # FastAPI application entry point
├── docker-compose.yml       # Docker Compose configuration
├── Dockerfile               # Container image definition
├── pyproject.toml           # Project dependencies
├── start.sh                 # Startup script
└── README.md                # This file
```

## Troubleshooting

### Connection Issues

- Ensure `WEBHOOK_URL` is publicly accessible and correctly configured in Meta App dashboard
- Verify `VERIFY_TOKEN` matches the one configured in Meta
- Check that the webhook subscription is active in Meta dashboard

### Database Issues

- Verify PostgreSQL is running and accessible
- Check `DATABASE_URL` format and credentials
- Ensure migrations are up to date: `uv run alembic upgrade head`

### Docker Issues

- Ensure Docker daemon is running
- Check logs: `docker compose logs -f bot`
- Verify port `8443` and `5432` are not already in use
- Try rebuilding: `docker compose up --build --force-recreate`

## Contributing

We welcome contributions! Please follow these guidelines:

### Development Workflow

1. **Install dependencies**:
   ```bash
   uv sync
   ```

2. **Make your changes** following the code style of the project

3. **Test your changes** thoroughly:
   - Ensure the application starts without errors
   - Test affected functionality
   - Verify database migrations work if you modified models

4. **Commit your changes** with clear, descriptive messages:
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

   Use conventional commit format:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `refactor:` for code refactoring
   - `test:` for adding tests
   - `chore:` for maintenance tasks

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Open a Pull Request** on GitHub with:
   - Clear title and description
   - Reference to any related issues
   - Screenshots/logs if applicable

### Code Guidelines

- Follow PEP 8 style guidelines for Python code
- Add docstrings to functions and classes
- Keep functions focused and modular
- Update documentation for user-facing changes
- Create database migrations for model changes

### Reporting Issues

- Use GitHub Issues to report bugs or request features
- Provide clear reproduction steps for bugs
- Include relevant logs, error messages, and environment details
- Check existing issues before creating duplicates

### Questions?

Feel free to open a GitHub Discussion or Issue for questions about contributing.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### MIT License Summary

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.
