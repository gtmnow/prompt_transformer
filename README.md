# Prompt Transformer

Prompt Transformer is a deterministic FastAPI service that rewrites prompts using:

- a precomputed `final_profile` stored in PostgreSQL
- deterministic task inference
- local model policies
- optional summary persona overrides

The service never calls an LLM.

## Quick start

1. Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

2. Set environment variables:

```bash
cp .env.example .env
```

3. Run migrations:

```bash
alembic upgrade head
```

4. Seed sample data:

```bash
python -m app.db.seed
```

5. Start the API:

```bash
uvicorn app.main:app --reload
```

## API

`POST /api/transform_prompt`

Example request:

```json
{
  "session_id": "sess_123",
  "user_id": "user_1",
  "raw_prompt": "Explain this concept simply",
  "target_llm": {
    "provider": "openai",
    "model": "gpt-4.1"
  }
}
```

## Railway

Create a Railway project with:

1. A PostgreSQL service
2. An app service pointing at this repo

Set these environment variables on the app service:

```bash
DATABASE_URL=<railway postgres url>
APP_ENV=production
LOG_LEVEL=INFO
PORT=8000
ENABLE_REQUEST_LOGGING=false
RAILWAY_AUTO_MIGRATE=true
RAILWAY_SEED_ON_START=true
HOST=0.0.0.0
```

Notes:

- `RAILWAY_AUTO_MIGRATE=true` runs `alembic upgrade head` during startup.
- `RAILWAY_SEED_ON_START=true` is useful for the first MVP deploy. After the sample profiles are loaded, switch it to `false`.
- The included `railway.json` starts the service through `python3 -m app.run_server`, which bootstraps the database and then launches Uvicorn.
