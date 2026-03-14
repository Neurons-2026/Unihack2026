# Canonical `content_item` Schema (S2)

This is the shared contract for data flowing through:
`ingestion -> preprocessing -> card generation -> briefing -> graph`.

Schema file: `shared/content_schema.json`  
Version: `1.0.0`

Allowed `source` values:
- `github`
- `huggingface`
- `arxiv_cs_ai`
- `arxiv_cs_lg`
- `arxiv_cs_cl`
- `openai_blog`
- `anthropic_blog`
- `deepmind_blog`
- `other`

## Why this exists

- Prevent module-to-module field drift during hackathon parallel work.
- Keep source-specific metadata while enforcing stable core fields.
- Provide one payload shape that can progressively gain fields as processing advances.

## Ownership by stage

1. Ingestion owner (Sam): populate required root fields.
2. Preprocessing owner (Sam/Sunny): populate `preprocessing.*`.
3. Card/UI owners (Steve/Alex): populate and consume `card.*`.
4. Recommendation owner (Liam): consume `card.keywords`, write `ranking.*`.
5. Briefing + graph owners (Sunny/Harry): consume `preprocessing.cleaned_text`, `card.*`, metadata.

Pipeline handoff marker:
- `pipeline_state` in (`raw_scraped`, `keywords_enriched`, `preprocessed`, `card_ready`)

## Required fields at ingestion completion

- `schema_version` (`"1.0.0"`)
- `id`
- `source`
- `source_url`
- `title`
- `raw_content`
- `metadata`
- `fetched_at`

Recommended at ingestion time (if available):
- `raw_summary`
- `published_at`
- `pipeline_state` = `raw_scraped`
- `provenance.collector`
- `provenance.collector_version`
- `provenance.dedupe_key`

## Required fields for card feed readiness

- All ingestion required fields
- `card.card_title`
- `card.card_summary`
- `card.keywords`

Recommended for better quality:
- `preprocessing.cleaned_text`
- `preprocessing.preview_text`
- `preprocessing.quality_score`
- `card.thumbnail_keyword`
- `ranking.source_rank_score`
- `ranking.trending_score` (temporary backward-compatible alias)

## Mapping to database tables

1. `content_items` table:
- root fields (`id`, `source`, `source_url`, `title`, `raw_summary`, `raw_content`, `metadata`, `fetched_at`, `published_at`)

2. `cards` table:
- `card.card_title` -> `card_title`
- `card.card_summary` -> `card_summary`
- `card.keywords` -> `keywords`
- `card.thumbnail_keyword` -> `thumbnail_keyword`
- `preprocessing.cleaned_text` -> `cleaned_text`
- `preprocessing.preview_text` -> card-prep text view (not DB-required)
- `preprocessing.quality_score` -> `quality_score`
- `ranking.trending_score` -> `trending_score`

## Example payload (card-ready)

```json
{
  "schema_version": "1.0.0",
  "id": "3b1a89ad-1531-45cb-8eaf-f40fa2d357ca",
  "source": "github",
  "source_url": "https://github.com/example/repo",
  "title": "Efficient LLM evaluation harness",
  "raw_summary": "A lightweight benchmark toolkit for small models.",
  "raw_content": "Repository README content ...",
  "metadata": {
    "stars": 4820,
    "language": "Python"
  },
  "fetched_at": "2026-03-14T10:10:00Z",
  "published_at": "2026-03-13T22:00:00Z",
  "preprocessing": {
    "cleaned_text": "Cleaned and boilerplate-removed text ...",
    "preview_text": "Short card-ready preview text ...",
    "quality_score": 0.91,
    "quality_notes": ["complete_summary", "source_authoritative"],
    "enrichment_used": false
  },
  "card": {
    "card_title": "Fast eval toolkit trends on GitHub",
    "card_summary": "Open-source harness benchmarks smaller LLMs quickly.",
    "keywords": ["evaluation", "llm", "tooling"],
    "thumbnail_keyword": "benchmark"
  },
  "ranking": {
    "trending_score": 0.78
  },
  "provenance": {
    "collector": "github_trending_scraper",
    "collector_version": "0.1.0",
    "normalizer_version": "0.1.0",
    "dedupe_key": "github:example/repo"
  }
}
```

## Validation rule

Any producer writing `content_item` JSON should validate against:
`shared/content_schema.json`.
