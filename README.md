# 10min AI Daily — Hackathon Scaffold

Docker-first scaffold for the 10min AI Daily project. Frontend uses Next.js/TypeScript, backend uses FastAPI, with Postgres + Redis and a lightweight worker for scraping/LLM tasks. The planning prompt lives in [.github/agent.md](.github/agent.md) and is mirrored at [scripts/prompts/agent.md](scripts/prompts/agent.md).

## Quickstart

1) Copy envs

```sh
cp .env.example .env
```

2) Build and start

```sh
make build
make up
```

Services: frontend http://localhost:3000, API http://localhost:8000/health, Postgres on 5432, Redis on 6379.

3) Logs & stop

```sh
make logs
make down
```

## Project layout

- docker-compose.yml — orchestrates frontend, api, worker, db, redis
- Makefile — common docker commands
- frontend/ — Next.js app with placeholder card feed
- backend/ — FastAPI service + worker stub
- scripts/ — prompt reference + local worker trigger

## Next steps

- Flesh out worker scraping and push data into Postgres/Redis
- Add real card feed endpoints and persistence
- Implement swipe interactions and knowledge graph UI
- Wire LLM-powered briefing generation using prompts in [scripts/prompts/agent.md](scripts/prompts/agent.md)