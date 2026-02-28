# Adaptive Child Learning RAG System

Production-grade, AI-powered adaptive learning platform for children with neurodiverse conditions (ADHD, ASD, Dyslexia, SPD) and physical disabilities. Uses Retrieval-Augmented Generation (RAG) to personalise every educational interaction in real time.

## Tech Stack

- **Runtime:** Python 3.12  
- **API:** FastAPI 0.115+ (async)  
- **Database:** PostgreSQL 16 + pgvector + TimescaleDB  
- **Cache:** Redis 7  
- **Embeddings:** Mistral mistral-embed (1024 dims)  
- **LLM:** Mistral mistral-small-latest (chat for /ask)  
- **Auth:** JWT (python-jose + bcrypt)  
- **Migrations:** Alembic  

## Setup

1. **Clone and install**

   ```bash
   cd adaptive_learning
   pip install -r requirements.txt
   ```

2. **Environment**

   Copy `.env.example` to `.env` and set at least:

   - `DATABASE_URL` — PostgreSQL (async: `postgresql+asyncpg://...`)
   - `REDIS_URL`
   - `OPENAI_API_KEY` — used for embeddings
   - `MISTRAL_API_KEY` — used for /ask chat (set `LLM_PROVIDER=mistral` and `LLM_MODEL=mistral-small-latest`). Use `LLM_PROVIDER=openai` and `LLM_MODEL=gpt-4o-mini` to use OpenAI for chat instead.
   - `JWT_SECRET` (min 32 chars for production)

3. **Database**

   Ensure PostgreSQL has **pgvector** and **TimescaleDB**:

   ```bash
   # If using Docker for DB (see below), run migrations after DB is up:
   alembic upgrade head
   ```

4. **Run**

   ```bash
   uvicorn app.main:app --reload
   ```

   API: `http://localhost:8000`  
   Docs: `http://localhost:8000/docs`

## Docker Compose

Starts PostgreSQL 16 (TimescaleDB + pgvector), Redis 7, the API, and the Next.js frontend:

```bash
docker compose up -d
# Apply migrations (from host or exec into api):
docker compose exec api alembic upgrade head
```

- **db:** Postgres with extensions, volume `pgdata`  
- **redis:** Redis 7  
- **api:** FastAPI app on port 8000, healthcheck on `/health`  
- **frontend:** Next.js app on port 3000 (open http://localhost:3000); uses `NEXT_PUBLIC_API_URL=http://localhost:8000` so the browser can call the API  

## API Overview

- **Auth:** `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/refresh`  
- **Children:** `POST /api/children`, `GET /api/children/{id}`, `PUT /api/children/{id}/neuro`, `POST /api/children/{id}/disabilities`  
- **Sessions:** `POST /api/sessions/start`, `POST /api/sessions/{id}/end`, `GET /api/sessions/{id}`  
- **Learn:** `POST /api/learn/ask`, `POST /api/learn/signal`, `POST /api/learn/feedback`  
- **Progress:** `GET /api/progress/{id}`, `GET /api/progress/{id}/mastery`, `GET /api/progress/{id}/timeline`, `GET /api/progress/{id}/report`, `GET /api/progress/{id}/review-queue`  
- **Admin:** `POST /api/admin/ingest` (content for RAG corpus)  

All `/api/*` routes except `/api/auth/*` require `Authorization: Bearer <access_token>`.

## Example: Register, create child, start session, ask

```bash
# Register
curl -s -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"parent@test.com","password":"SecurePass123!","full_name":"Parent"}' \
  | jq .

# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"parent@test.com","password":"SecurePass123!"}' \
  | jq -r .access_token)

# Create child
CHILD=$(curl -s -X POST http://localhost:8000/api/children \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Alex","date_of_birth":"2015-01-01","primary_language":"en"}' \
  | jq -r .child_id)

# Start session
SESSION=$(curl -s -X POST http://localhost:8000/api/sessions/start \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"child_id\":\"$CHILD\"}" \
  | jq -r .session_id)

# Ask (requires OpenAI key and ingested content for RAG)
curl -s -X POST http://localhost:8000/api/learn/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"child_id\":\"$CHILD\",\"session_id\":\"$SESSION\",\"input_text\":\"What is 2+2?\"}" \
  | jq .
```

## Architecture (short)

- **Personalised learning:** Every LLM prompt is built from live DB state (diagnosis, cognitive load, mood, modalities, mastery gaps).  
- **Progress tracking:** All interactions and mastery updates are stored; FSRS-4.5 drives spaced repetition; caregivers get reports.  
- **Disability support:** Disability types and accommodations are first-class; they drive content filters and UI directives.  
- **Special needs:** ADHD, ASD, Dyslexia, etc. are modelled as diagnosis enums and drive prompt rules, retrieval filters, and reranking.  

## Frontend (Next.js)

A child-friendly web app to test the API is in `frontend/`:

```bash
cd frontend
cp .env.local.example .env.local   # set NEXT_PUBLIC_API_URL if API is not on localhost:8000
npm install
npm run dev
```

Open **http://localhost:3000**. You can sign up, add learners, start a learning session (ask questions and get RAG answers), send simple reactions (Good / Need help), and view progress (overview, mastery, timeline, report, review queue). The UI uses large tap targets, soft colours, and clear labels.

## Tests

```bash
pytest -x -q
```

Use `.env` or env vars for `DATABASE_URL` / `REDIS_URL` if tests hit real services; otherwise mocks are used where applicable.
