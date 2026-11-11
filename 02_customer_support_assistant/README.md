# AI Customer Support Assistant

A small API that classifies a support message, suggests a reply, and stores the ticket in SQLite. It uses an OpenAI model when `OPENAI_API_KEY` is configured; otherwise it uses a simple keyword-based fallback so the project can be tested without an API key.

## Skills demonstrated
Python, FastAPI, REST APIs, SQL/SQLite, basic async endpoint, LLM API integration, input validation, error handling.

## Run locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs

Add your own `OPENAI_API_KEY` to `.env` to enable LLM-generated classifications and replies. Do not commit `.env`.

## API
- `POST /tickets` — JSON body: `{"customer_name":"Asha","message":"My payment failed"}`
- `GET /tickets` — list saved tickets

## Notes
SQLite is used to keep setup easy. Redis caching, authentication, and production monitoring are intentionally not included in this beginner version.
