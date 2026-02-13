# AI CRM Demo (Real Estate)

Modern AI-assisted real estate CRM demo with two workflows:

- Admin workflow for creating and managing property inventory
- User workflow for natural-language property search

This project demonstrates how to use an LLM safely in a data product:

- LLM converts natural language to structured filters
- Backend validates filters
- Repository applies filters to DB
- Model never queries the DB directly

## What It Solves

- Removes manual filter-building for users
- Lets non-technical users search inventory conversationally
- Keeps admin operations simple (CRUD in one dashboard)
- Keeps AI layer isolated from persistence/query layer for safety and auditability

## How It Works

### End-to-end flow

1. User submits a query like `show villas under 2 crore in mumbai`
2. Backend calls LLM and extracts structured JSON filter
3. Parsed filter is validated with Pydantic schema
4. Location scope is refined against known DB locations
5. SQLAlchemy query executes against SQLite
6. UI displays matched properties, total result count, and NLP engine source

### NLP engine behavior

- Preferred path: `LLM` (Perplexity or OpenAI provider)
- Fallback path: `Heuristic` parser when no valid provider key is configured or provider call fails
- UI shows engine used: `NLP engine: LLM` or `NLP engine: Heuristic fallback`

### Dynamic location resolution (no static city list)

- Known locations are pulled from DB (`SELECT DISTINCT location`)
- Query geography is resolved dynamically against known locations
- Supports typo correction and regional scope inference
- Supports single-location and multi-location filtering

## Architecture

### Backend

- FastAPI
- SQLAlchemy + SQLite
- Pydantic schemas
- AI service layer for LLM + parsing + fallback

### Frontend

- Vanilla JS + HTML
- Tailwind CDN
- Modern responsive UI
- Inline loaders and total result count for search/chat

### Repository structure

```text
backend/   FastAPI app, DB, AI services, schemas, routes
frontend/  Static UI (landing, admin login, admin dashboard, user/chat)
```

## Key Features

- Admin CRUD for properties
- User listing browse + AI chat search
- Landing-page NL search
- Modern interactive UI with responsive layout and visual cards
- Engine source visibility (`parser_source`) in UI
- Dynamic location normalization for better geo-intent matching
- Seed data with India + international cities for geo-scope testing

## API Endpoints

- `GET /admin/properties`
- `POST /admin/properties`
- `PUT /admin/properties/{id}`
- `DELETE /admin/properties/{id}`
- `GET /properties`
- `POST /chat/query` with body:

```json
{ "message": "show plots in delhi" }
```

Chat response includes:

- `interpreted_filter`
- `parser_source` (`llm` or `heuristic`)
- `results`

## Requirements

- Python 3.10+ recommended
- pip
- Internet access for LLM provider calls

Python packages (from `backend/requirements.txt`):

- fastapi
- uvicorn[standard]
- sqlalchemy
- pydantic
- pydantic-settings
- python-dotenv
- httpx

## Configuration

Create `backend/.env` from `backend/.env.example`.

Supported provider variables:

- `PERPLEXITY_API_KEY`
- `PERPLEXITY_MODEL` (default `sonar-pro`)
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (default `gpt-4o-mini`)

Provider priority:

1. Perplexity (`PERPLEXITY_API_KEY`)
2. OpenAI (`OPENAI_API_KEY`)

Compatibility rule:

- If `OPENAI_API_KEY` starts with `pplx-`, it is treated as a Perplexity key.

If no valid provider key is configured, heuristic fallback is used.

## Run Locally

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### Frontend

```bash
cd frontend
python3 -m http.server 5173 --bind 127.0.0.1
```

Open:

- Frontend: `http://127.0.0.1:5173`
- Backend: `http://127.0.0.1:8000`

## Deploy on Render

You have two services:

- Backend API (`ai-crm-api`) as a **Web Service**
- Frontend UI (`ai-crm-web`) as a **Static Site**

This repo now includes `render.yaml` so you can use Render Blueprint deploy.

### Option A: Blueprint (recommended)

1. In Render, click **New +** -> **Blueprint**
2. Select repo: `Waqar-Wani/AI-CRM`
3. Render reads `render.yaml` and creates:
   - `ai-crm-api` (web)
   - `ai-crm-web` (static)
4. Set environment variables:
   - On `ai-crm-api`:
     - `PERPLEXITY_API_KEY=<your_key>`
     - Optional: `PERPLEXITY_MODEL=sonar-pro`
   - On `ai-crm-web`:
     - `BACKEND_URL=https://<your-api-service>.onrender.com`

### Option B: Manual forms (your current screen)

If creating manually from **New Static Site**, use these values for frontend:

- `Name`: `ai-crm-web`
- `Branch`: `main`
- `Root Directory`: `frontend`
- `Build Command`:

```bash
if [ -n "$BACKEND_URL" ]; then
  printf "window.__API_BASE__ = \"%s\";\n" "$BACKEND_URL" > render-config.js
fi
```

- `Publish Directory`: `.`
- Environment variable:
  - `BACKEND_URL=https://<your-backend>.onrender.com`

Then create backend separately as **Web Service**:

- `Name`: `ai-crm-api`
- `Branch`: `main`
- `Root Directory`: `backend`
- `Build Command`: `pip install -r requirements.txt`
- `Start Command`: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment variables:
  - `PERPLEXITY_API_KEY=<your_key>` (or `OPENAI_API_KEY`)
  - Optional model vars (`PERPLEXITY_MODEL`, `OPENAI_MODEL`)

## Quick Demo Script

1. Open landing page and run search queries
2. Click profile and login as admin:
   - `admin@example.com / admin123`
3. Add or update a property from admin dashboard
4. Use landing search or user chat to query data
5. Observe:
   - Total result count
   - NLP engine source
   - Interpreted filter behavior on geo queries

## Notes

- Country-level behavior depends on location-scope resolution against known DB locations.
- Results are deterministic at DB/query layer after filter extraction.
- Keep API keys in `.env` only, never in committed code.

## Security

- Rotate provider keys if they are ever shared or exposed.
- Do not commit real API keys to git history.
