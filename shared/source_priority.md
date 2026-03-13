# S3: Source List + Ingestion Priority

This document defines the agreed source order for Sam's ingestion pipeline.
Machine-readable version: `shared/source_priority.json`.

## Priority Order

1. P0: GitHub Trending - `https://github.com/trending`
2. P0: HuggingFace Papers - `https://huggingface.co/papers`
3. P0: OpenAI News - `https://openai.com/news/`
4. P0: Anthropic News - `https://www.anthropic.com/news`
5. P1: arXiv (AI Recent Papers) - `https://arxiv.org/list/cs.AI/recent`
6. P1: arXiv (Machine Learning) - `https://arxiv.org/list/cs.LG/recent`
7. P1: arXiv (Computational Linguistics) - `https://arxiv.org/list/cs.CL/recent`
8. P1: Google DeepMind Blog - `https://deepmind.google/discover/blog/`

## Build Sequence Recommendation

1. Implement P0 connectors first (GitHub + HuggingFace).
2. Add OpenAI/Anthropic once schema normalization is stable.
3. Add arXiv + DeepMind as expansion once demo reliability is locked.

## Fallback Rule

- If live scraping returns fewer than 10 usable items or fails due to layout/rate-limit/network issues, switch to seeded data in `backend/data/seed_cards.json`.
- Keep minimum 15 items ready for demo safety.
