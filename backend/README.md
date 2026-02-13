## Backend (FastAPI + SQLite + AI)

### What it does
- CRUD properties in SQLite
- Chat endpoint converts NL → JSON filter (LLM) → DB search (repo layer)

### Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Configure AI (optional but recommended)
Edit `.env`:
- `PERPLEXITY_API_KEY=...`
- `PERPLEXITY_MODEL=sonar-pro` (or any available Perplexity model)
- `OPENAI_API_KEY=...` (optional alternative provider)
- `OPENAI_MODEL=gpt-4o-mini` (when using OpenAI provider)

Provider order is:
1) Perplexity (`PERPLEXITY_API_KEY`, or `OPENAI_API_KEY` if it starts with `pplx-`)
2) OpenAI (`OPENAI_API_KEY`)

If no valid provider key is set, the app uses a **small heuristic fallback** so the demo still works.

### Run
```bash
uvicorn app.main:app --reload
```

### Notes (common macOS issue)
If `pip install` fails with SSL certificate verification errors, fix your Python certs:
- For python.org installer: run the included **Install Certificates.command**
- Or use a Python install via **Homebrew/pyenv**, then recreate the venv and reinstall
