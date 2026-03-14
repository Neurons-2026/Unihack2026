# 10min AI Daily — Agent Instructions

You are working on **10min AI Daily**, a hackathon project. It is a lightweight AI news companion where users swipe through daily AI content cards, build a knowledge basket, generate a 10-minute briefing via LLM, and explore a personal knowledge graph. The stack is a **Next.js + Tailwind** frontend with a **FastAPI (Python)** backend and **Supabase Postgres** database.

This is a hackathon — prioritize speed, demo impact, and working code over perfection. Do not over-engineer. Do not add features not described here.

---

## Project structure

```
10min-ai-daily/
├── AGENTS.md                  # This file
├── README.md
├── frontend/                  # Next.js + React + TypeScript + Tailwind
│   ├── src/
│   │   ├── app/               # Next.js App Router pages
│   │   │   ├── page.tsx       # Home — card swipe feed
│   │   │   ├── basket/        # Basket review page
│   │   │   ├── briefing/      # Briefing display page
│   │   │   └── graph/         # Knowledge graph page
│   │   ├── components/        # Reusable React components
│   │   │   ├── CardDeck.tsx   # Swipe card stack
│   │   │   ├── CardItem.tsx   # Individual card
│   │   │   ├── BasketBar.tsx  # Basket counter/indicator
│   │   │   ├── BriefingView.tsx
│   │   │   └── GraphView.tsx  # Knowledge graph visualization
│   │   ├── lib/               # Utilities, API client, types
│   │   │   ├── api.ts         # Backend API client functions
│   │   │   ├── types.ts       # Shared TypeScript types
│   │   │   └── store.ts       # Zustand store
│   │   └── styles/
│   ├── public/
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── next.config.js
├── backend/                   # FastAPI + Python
│   ├── main.py                # FastAPI app entry point, CORS, routers
│   ├── routers/
│   │   ├── cards.py           # GET /cards, GET /cards/recommended
│   │   ├── interactions.py    # POST /interactions
│   │   ├── basket.py          # POST /basket, GET /basket
│   │   ├── briefing.py        # POST /briefing/generate, GET /briefing/:id
│   │   └── graph.py           # POST /graph/generate, GET /graph
│   ├── services/
│   │   ├── ingestion.py       # Scraping + API fetching logic
│   │   ├── preprocessing.py   # Text cleaning, card metadata generation
│   │   ├── recommendation.py  # Scoring + ranking logic
│   │   ├── briefing.py        # LLM prompt + generation
│   │   └── knowledge_graph.py # Node extraction, edge creation, merge
│   ├── models/
│   │   ├── schemas.py         # Pydantic request/response models
│   │   └── database.py        # Supabase client + DB helpers
│   ├── scripts/
│   │   ├── ingest.py          # Manual ingestion trigger
│   │   └── seed.py            # Seed DB with fallback data
│   ├── data/
│   │   └── seed_cards.json    # Fallback curated dataset (15-20 items)
│   ├── requirements.txt
│   └── .env.example
├── shared/                    # Shared schemas / contracts
│   └── content_schema.json    # Canonical content item schema
└── .github/
    └── copilot-instructions.md
```

---

## Dev environment

### Frontend

```bash
cd frontend
npm install
npm run dev          # Starts Next.js dev server on http://localhost:3000
npm run build        # Production build — run this to verify before committing
npm run lint         # ESLint check
```

Key frontend dependencies:
- `react-tinder-card` — swipe gesture component
- `react-force-graph-2d` — knowledge graph visualization
- `zustand` — lightweight state management
- `tailwindcss` — utility-first CSS

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload      # Starts FastAPI on http://localhost:8000
```

Key backend dependencies:
- `fastapi` + `uvicorn` — API framework
- `beautifulsoup4` + `requests` — web scraping
- `readability-lxml` — article text extraction
- `anthropic` — Claude API for briefing generation
- `scikit-learn` — TF-IDF for recommendation
- `spacy` — NER for knowledge graph
- `networkx` — graph data structure + operations
- `supabase` — database client

After installing, download the spaCy model:
```bash
python -m spacy download en_core_web_sm
```

### Environment variables

Copy `backend/.env.example` to `backend/.env` and fill in:
```
SUPABASE_URL=
SUPABASE_KEY=
ANTHROPIC_API_KEY=
```

The frontend calls the backend at `http://localhost:8000` by default. Set `NEXT_PUBLIC_API_URL` in `frontend/.env.local` to override.

---

## Database schema

We use Supabase Postgres. Tables:

**content_items** — raw ingested content from sources
- `id` (UUID, PK), `source` (text: github/huggingface/openai_blog/anthropic_blog/other), `source_url` (text), `title` (text), `raw_summary` (text), `raw_content` (text), `metadata` (jsonb), `fetched_at` (timestamptz), `published_at` (timestamptz)

**cards** — preprocessed, card-ready data
- `id` (UUID, PK), `content_item_id` (UUID, FK → content_items), `card_title` (text), `card_summary` (text, < 120 chars), `keywords` (text[]), `thumbnail_keyword` (text), `cleaned_text` (text), `quality_score` (float), `trending_score` (float)

**user_actions** — swipe interaction log
- `id` (UUID, PK), `session_id` (text), `card_id` (UUID, FK → cards), `action` (text: swipe_right/swipe_left/undo), `dwell_time_ms` (int), `session_date` (date), `created_at` (timestamptz)

**basket_items** — user's selected cards for a session
- `id` (UUID, PK), `session_id` (text), `card_id` (UUID, FK → cards), `session_date` (date), `added_at` (timestamptz)

**briefings** — generated digests
- `id` (UUID, PK), `session_id` (text), `card_ids` (UUID[]), `content` (text, Markdown), `reading_time_min` (float), `generated_at` (timestamptz), `share_token` (text, nullable)

**graph_nodes** — knowledge graph concepts
- `id` (UUID, PK), `session_id` (text), `label` (text), `description` (text), `first_seen` (timestamptz), `last_seen` (timestamptz), `frequency` (int)

**graph_edges** — knowledge graph relationships
- `id` (UUID, PK), `session_id` (text), `source_node_id` (UUID, FK → graph_nodes), `target_node_id` (UUID, FK → graph_nodes), `relationship` (text), `weight` (float), `created_at` (timestamptz)

When writing migrations or seed scripts, always use these exact table and column names.

---

## API contracts

All backend endpoints are under `http://localhost:8000/api/v1/`.

### Cards
- `GET /api/v1/cards?session_id={id}` — returns today's card feed (optionally ranked by recommendation)
- `GET /api/v1/cards/{card_id}` — returns single card detail

### Interactions
- `POST /api/v1/interactions` — body: `{ session_id, card_id, action, dwell_time_ms }`

### Basket
- `GET /api/v1/basket?session_id={id}` — returns current basket items
- `POST /api/v1/basket` — body: `{ session_id, card_id }` — adds card to basket
- `DELETE /api/v1/basket/{item_id}` — removes card from basket

### Briefing
- `POST /api/v1/briefing/generate` — body: `{ session_id, card_ids }` — generates briefing via LLM, returns Markdown content. Use streaming if possible.
- `GET /api/v1/briefing/{briefing_id}` — returns cached briefing

### Knowledge Graph
- `POST /api/v1/graph/generate` — body: `{ session_id, card_ids }` — extracts nodes/edges from cards
- `GET /api/v1/graph?session_id={id}` — returns full graph (nodes + edges)

All responses use JSON. Errors return `{ "detail": "error message" }` with appropriate HTTP status codes. Use Pydantic models in `backend/models/schemas.py` for all request/response validation.

---

## Code style

### Python (backend)
- Use type hints on all function signatures.
- Use Pydantic `BaseModel` for all request/response schemas.
- Use `async def` for all route handlers.
- Keep route handlers thin — delegate logic to service functions in `backend/services/`.
- Use `logging` module, not `print()`.
- Format with `black`. Lint with `ruff`.
- Imports: stdlib first, then third-party, then local, separated by blank lines.

### TypeScript (frontend)
- Use functional React components with hooks. No class components.
- Use TypeScript strict mode. Define interfaces for all props and API responses in `lib/types.ts`.
- Use Tailwind utility classes for styling. No CSS modules, no styled-components.
- Use Zustand for shared state (basket contents, session ID). Use local `useState` for component-local state.
- Fetch data with `fetch()` or a thin wrapper in `lib/api.ts`. No Redux, no React Query (overkill for hackathon).
- Component files: PascalCase (`CardDeck.tsx`). Utility files: camelCase (`api.ts`).

### General
- Keep files under 200 lines. Split if longer.
- No comments that restate the code. Comment only for "why," not "what."
- Use descriptive variable names. No single-letter variables except loop indices.

---

## LLM integration (briefing generation)

Use the Anthropic Python SDK with `claude-sonnet-4-20250514`. The briefing prompt lives in `backend/services/briefing.py`.

The briefing prompt must instruct the model to:
- Write for a non-technical audience
- Structure output with clear section headings
- Include "what happened" and "why it matters" for each item
- Keep total output around 2,000 words (~10 min reading)
- Include source URLs as Markdown links
- Never hallucinate facts not present in the provided source text

---

## Knowledge graph

Node extraction uses spaCy NER + keyword extraction from card text. Edge creation uses co-occurrence (concepts from the same card are connected). Graph operations use NetworkX in-memory, then persist to Postgres.

Merge logic: when new nodes are added, check for existing nodes with the same normalized label (lowercase, stripped). If found, increment `frequency` and update `last_seen`. For edges, increment `weight` if the same pair already exists.

Keep edge relationship types simple: `related_to`, `mentions`, `overlaps_with`, `builds_on`.

---

## Recommendation system

Uses content-based filtering with TF-IDF + cosine similarity from scikit-learn.

- **Cold start** (no interaction history): rank cards by `trending_score`.
- **Warm start**: build a user interest vector from keywords of liked cards, compute cosine similarity against new card keywords, blend with trending score.

Do not use embeddings, collaborative filtering, or any ML model that requires training. Keep it simple and explainable.

---

## Testing

No unit test framework is required. Testing is manual with a smoke test checklist.

Before any integration or demo:
1. Verify seeded data loads: `python backend/scripts/seed.py`
2. Verify card feed returns data: `curl http://localhost:8000/api/v1/cards`
3. Verify swipe logging works: POST an interaction, check DB
4. Verify basket add/remove works
5. Verify briefing generation returns valid Markdown
6. Verify graph generation returns nodes + edges
7. Verify frontend renders cards, basket, briefing, and graph pages without console errors
8. Verify the app works fully offline with seeded/fallback data

If you write any test scripts, put them in `backend/scripts/` and make them runnable with `python backend/scripts/test_*.py`.

---

## Git workflow

- Single `main` branch. Feature branches named `{owner}/{short-description}` (e.g., `sam/github-scraper`, `steve/card-ui`).
- Commit messages: imperative mood, short first line.
- Merge to `main` frequently. Do not let branches diverge for more than a few hours.
- Tag stable demo-ready states: `git tag demo-v1`, `git tag demo-final`.

---

## Boundaries — do NOT do these things

- **Do not add authentication or user accounts.** We use a simple `session_id` (generated client-side, stored in Zustand).
- **Do not install a CSS framework besides Tailwind.**
- **Do not add Redux, React Query, SWR, or tRPC.**
- **Do not use a graph database** (store graph data in Postgres tables).
- **Do not add Docker or Kubernetes.** Local dev + direct deploy to Vercel/Railway.
- **Do not write unit tests with pytest or jest.** Manual smoke tests only.
- **Do not build a sharing feature** unless all P0 features are complete and stable.
- **Do not add WebSockets** unless streaming briefing generation specifically requires it (SSE is preferred).
- **Do not over-engineer the recommendation system.**
- **Do not refactor working code** for cleanliness during the hackathon.
- **Do not add new npm or pip dependencies** without checking if an existing dependency already solves the problem.
- **Do not modify `data/seed_cards.json`** without coordinating — it is the shared fallback dataset.

---

## Deployment

- **Frontend:** Deploy to Vercel. Root directory: `frontend/`.
- **Backend:** Deploy to Railway. Root directory: `backend/`, start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`.
- **Database:** Supabase hosted Postgres.
- Set all environment variables in the deployment platform dashboards.
- Deploy early (Sunday morning latest). Have a working deployed URL before demo prep begins.

---

## Fallback strategy

If any system fails during the demo:
- **Scraping fails →** use `data/seed_cards.json`
- **LLM API fails →** serve a pre-generated cached briefing from the `briefings` table
- **Graph generation fails →** serve a pre-generated graph snapshot
- **Deployment fails →** run locally and screen-share, or use the backup demo video
- **Swipe gesture buggy →** fall back to Save/Skip buttons (the `CardDeck` component should support both modes)

Always have `python backend/scripts/seed.py` ready to repopulate the database instantly.
