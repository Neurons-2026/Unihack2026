# 10min AI Daily — Hackathon Stack

This repo follows the agent instructions in [AGENTS.md](AGENTS.md). Stack: Next.js + Tailwind frontend, FastAPI backend, Supabase Postgres. Keep it hackathon-simple: no auth, no extra infra.

## Quickstart (preferred: local dev)

Frontend:

```sh
cd frontend
npm install
npm run dev   # http://localhost:3000
```

Backend:

```sh
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Env vars (backend/.env): SUPABASE_URL, SUPABASE_KEY, ANTHROPIC_API_KEY.
Frontend API base overrides: set NEXT_PUBLIC_API_URL in frontend/.env.local if not localhost.

## Project layout (target)

- AGENTS.md — working instructions
- frontend/src/app — pages: home, basket, briefing, graph
- frontend/src/components — CardDeck, CardItem, BasketBar, BriefingView, GraphView
- frontend/src/lib — api client, types, Zustand store
- backend/main.py — FastAPI app, CORS, routers
- backend/routers — cards, interactions, basket, briefing, graph
- backend/services — ingestion, preprocessing, recommendation, briefing, knowledge_graph
- backend/models — schemas, database (Supabase helper)
- backend/data/seed_cards.json — fallback dataset
- scripts/prompts/agent.md — prompt reference copy

## Notes

- Agent guidance prefers local dev; Docker files remain for convenience but are optional. Ports: frontend 3001 (compose), API 8000, Postgres 55432 when using docker-compose.
- Keep features inside scope: swipe cards, basket cap, recommendation, briefing generation, knowledge graph; no auth.