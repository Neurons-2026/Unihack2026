# Unified Hackathon Project Plan

## Table of Contents

- [Part 1: Product Summary & Value Proposition](#part-1-product-summary--value-proposition)
- [Part 2: Hackathon PRD](#part-2-hackathon-prd)
- [Part 3: System Design & Data Model](#part-3-system-design--data-model)
- [Part 4: Team Task Breakdowns](#part-4-team-task-breakdowns)
- [Part 5: Linear Project Management Plan](#part-5-linear-project-management-plan)
- [Part 6: Tech Stack Recommendations](#part-6-tech-stack-recommendations)
- [Part 7: 3-Day Execution Plan](#part-7-3-day-execution-plan)
- [Part 8: Risks, Trade-offs & Simplification Strategy](#part-8-risks-trade-offs--simplification-strategy)
- [Part 9: Demo Strategy & Final Recommendations](#part-9-demo-strategy--final-recommendations)

---

# Part 1: Product Summary & Value Proposition

## Product Positioning

**Product Name:** 10min AI Daily

**One-Line Slogan:** Swipe today's AI signals, understand the future in 10 minutes.

This product is a lightweight AI news companion that helps users understand the latest AI developments in 10 minutes per day. Instead of forcing users to scroll through repetitive news feeds, research threads, GitHub repos, and company blogs, it turns the latest signals into simple, swipeable content cards. Users pick a few items they care about, and the system generates a low-cognitive-load daily briefing plus a growing personal knowledge graph.

The product combines discovery, personalization, summarization, and visual learning in one loop.

## Target Users

**Persona A — "The Busy AI-Aware Student"**
Studies CS/DS/AI/business/design. Wants to know what's happening in AI every day. Has 10 minutes, not 2 hours. Gets overwhelmed by jargon-heavy articles. Wants a product that feels modern and motivating.

**Persona B — "The Early-Career Builder"**
Works in tech, startup, product, or a research-adjacent role. Wants first-hand source discovery without doomscrolling. Cares more about "what happened and why it matters" than technical detail. Wants personalized discovery over time.

**Persona C — "The Curious Non-Expert"**
Interested in AI trends and tools. Doesn't easily understand papers/repos. Needs plain-language summaries and guided exploration.

## Core Value Proposition

Spark curiosity, minimize cognitive load, deliver fast understanding. Users get curated first-hand sources and relief from FOMO/anxiety — no wading through repetitive or redundant information. The product reduces noise, reduces anxiety, improves signal selection, and helps users build a cumulative understanding of the AI landscape over time rather than consuming isolated articles.

## Pain Points Addressed

1. AI news moves too fast — practitioners and enthusiasts struggle to keep up.
2. Content is spread across GitHub, HuggingFace, arXiv, X/Twitter, newsletters, company blogs, and product releases.
3. Most sources are repetitive or too technical.
4. Users waste time deciding what is worth reading.
5. News feeds are not personalized for interest-based learning.
6. Users do not accumulate structured understanding over time.

## Why Existing Alternatives Fall Short

| Alternative | Weaknesses |
|---|---|
| **Newsletters** | Low interactivity, same content for everyone, often too long, delayed by editorial cadence |
| **Twitter / Reddit / HN** | High noise, high cognitive load, easy to get distracted, not beginner-friendly |
| **AI news sites** | Mostly article lists, no preference learning loop, weak personalization, no cumulative knowledge structure |
| **Research ranking pages** (e.g., Papers with Code) | Good raw signals, poor explanation, not accessible to non-experts, no user memory or concept graph |

## Why This Product is Better

- Starts with interest-first interaction rather than article-first reading.
- Lowers cognitive load with swipeable cards.
- Generates a personalized 10-minute digest, not just a feed.
- Creates a personal knowledge graph, turning daily consumption into long-term understanding.
- Feels both fun and productive — a strong hook for judges and future users.

## Why This is Worth Building at a Hackathon

- Highly demoable, visually strong, easy for judges to understand in under 30 seconds.
- Combines multiple impressive AI product elements — ingestion, ranking, summarization, recommendation, knowledge graph — into one coherent user story.
- Multiple obvious "wow moments" in the demo.
- Can be scoped into a strong MVP while still showing stretch vision.

---

# Part 2: Hackathon PRD

## 2.1 Product Goal

Build an MVP that lets a user:

1. Open the app and view a set of curated AI content cards from the latest sources
2. Swipe right to save interesting items and left to skip
3. Generate a 10-minute personalized briefing from saved items
4. View a lightweight knowledge graph based on the selected content
5. Optionally see a simple personalization effect based on prior swipes

**The hackathon goal is not to build the perfect recommendation engine or full production graph system. The goal is to deliver a cohesive, polished loop that feels like a real product.**

## 2.2 Core User Journey

```
Step 1: Landing / Home
    → User sees "Today's AI Signals" with a short explanation: "Swipe to build your 10-minute AI briefing"
    → Backend: Module 1 (Ingestion) has already run; Module 2 (Preprocessing) has structured cards
    → Backend: Module 4 (Recommendation) ranks cards for this user

Step 2: Card Selection
    → User sees cards with title, source, keyword tags, one-line explanation
    → Swipe right = add to basket; swipe left = skip
    → Each swipe logged → Module 4 (Recommendation logging)
    → Basket capped at 3–5 items
    → Frontend: Module 3 (Card Interaction UI)

Step 3: Basket Review
    → User sees selected items, can remove or reorder
    → Clicks "Generate My 10-Minute Briefing"

Step 4: Digest Generation
    → Module 6 (Briefing): LLM generates readable brief — what happened, why it matters, key themes, industry impact, source links
    → Module 5 (Knowledge Graph): extracts concepts, creates nodes/edges, merges with history

Step 5: Briefing Display
    → User reads formatted briefing (~10 min read)
    → Source links embedded for deeper reading

Step 6: Knowledge Graph Exploration
    → Interactive graph shows today's additions highlighted
    → User can explore historical connections, zoom, pan, click-to-inspect

Step 7 (Optional): Sharing
    → Module 7 generates shareable link for briefing or graph export
```

## 2.3 Feature Specifications

### Feature 1: AI Signal Ingestion (P0)

**Purpose:** Collect the latest AI-relevant items from a small number of high-quality sources.

**How user uses it:** Indirectly — user sees cards generated from this pipeline.

**Sources:** GitHub Trending repos (AI/ML), HuggingFace daily papers and trending models, OpenAI blog/news, Anthropic blog/news, optionally curated static sample data.

**Input/Output:**

| Field | Type | Description |
|---|---|---|
| `id` | UUID | Unique content identifier |
| `title` | string | Original title |
| `summary` | string | Raw excerpt or abstract |
| `url` | string | Source URL |
| `source` | enum | github / huggingface / openai_blog / anthropic_blog / other |
| `timestamp` | datetime | Publication or trending timestamp |
| `raw_content` | string | Full scraped text |
| `metadata` | JSON | Stars, forks, likes, citation count, etc. |

**Success Criteria:**

- At least 10–20 usable cards available for demo
- Sources are recent and relevant
- Titles and metadata look clean
- Deduplicates content across sources
- Handles rate limits and failures with retries

**Downgrade Path:** Use a semi-static curated JSON dataset (15–20 high-quality items) if live ingestion is unstable.

**Priority:** P0

---

### Feature 2: Preprocessing + Card Generation (P0)

**Purpose:** Turn raw content into swipe-friendly cards and briefing-ready text.

**How user uses it:** User browses concise cards instead of raw articles or repos.

**Sub-features:**

1. **Text Cleaning:** Strip HTML, ads, nav elements, boilerplate; extract core text.
2. **Card Data Generation:** Produce card title, one-line summary (< 120 chars), 3–5 keyword tags, thumbnail keyword.
3. **Quality Assessment:** Score items 0–1 based on content length, source authority, completeness.
4. **Supplementary Search:** For low-quality items, trigger web search to enrich context.
5. **Briefing Text Preparation:** Generate cleaned full text suitable for LLM digest generation.

**Output per item:**

| Field | Type | Description |
|---|---|---|
| `card_title` | string | Cleaned, concise title (not too technical) |
| `card_summary` | string | One-line summary (< 120 chars) |
| `keywords` | string[] | 3–5 topic tags |
| `thumbnail_keyword` | string | Primary visual keyword for display |
| `cleaned_text` | string | Full cleaned text for briefing use |
| `quality_score` | float | 0–1 confidence score |
| `source_url` | string | Link back to original |

**Success Criteria:**

- Cards are readable in < 5 seconds each
- Titles are not too technical
- Metadata is consistent across sources
- Processing completes within 30 seconds per batch of 20 items

**Downgrade Path:** Use templated heuristics instead of deep content enrichment. Only process selected basket items, not entire corpus.

**Priority:** P0

---

### Feature 3: Swipe-to-Basket UI (P0)

**Purpose:** Provide a low-friction mechanism for interest selection.

**How user uses it:** Swipe right to save, left to skip. Card displays: title + keyword tag pills + one-line explanation (minimal, like a YouTube thumbnail + title).

**Input/Output:**

- Input: card interaction (swipe direction, dwell time)
- Output: saved basket list + logged preference event

**UI Specification:**

- Swipeable card stack with smooth exit animations (60fps)
- Visual basket counter (e.g., "3/5 selected")
- Ability to undo the last swipe
- Empty state shown when all cards are processed

**Success Criteria:**

- Smooth interaction; demo feels polished
- Basket updates correctly
- Cards render in < 200ms
- Basket enforces configurable cap (default: 5)

**Downgrade Path:** Buttons ("Save" / "Skip") with swipe-like animation instead of true gesture swipe if needed.

**Priority:** P0

---

### Feature 4: 10-Minute Briefing Generation (P0)

**Purpose:** Produce one readable personalized summary from selected items.

**How user uses it:** Clicks "Generate My 10-Minute Briefing" after saving items.

**Input:** 3–5 selected cards with cleaned source text.

**Output — structured digest with sections:**

- Today's overview (in plain English)
- Per-item summary: what happened
- Why it matters / industry implications
- Trends to watch
- Key takeaways
- Links to original sources

**Requirements:**

- Understandable to non-experts — low cognitive load
- Feels coherent, not like disconnected bullets
- Target reading time: ~10 minutes (~2,000 words)
- Generated within 5–15 seconds in demo
- No hallucinated facts — all claims traceable to source material

**Success Criteria:**

- Summary is understandable to non-technical audience
- Reading time is between 8–12 minutes
- Proper source attribution with clickable links
- Coherent narrative across multiple items

**Downgrade Path:** Pre-generate or cache digests for known demo card selections.

**Priority:** P0

---

### Feature 5: Lightweight Knowledge Graph (P1)

**Purpose:** Visualize how selected topics connect over time.

**How user uses it:** Opens graph after digest generation.

**Sub-features:**

1. **Create Nodes:** Extract key concepts from each basket card (via NLP or LLM).
2. **Connect Nodes:** Identify relationships between nodes — co-occurrence in same card = connected; optionally LLM-labeled edge types (related_to, mentions, overlaps_with, builds_on).
3. **Merge Graph:** Each time new content is added, merge the new subgraph with the user's accumulated graph — find matching existing nodes (fuzzy label match), update edge weights, add new nodes/edges.
4. **Interactive Visualization:** Zoom, pan, click-to-inspect node details. Today's additions visually highlighted.

**Success Criteria:**

- Each card generates at least 3 concept nodes
- Users can clearly see concept clusters and relationships
- Graph looks visually impressive
- Connection logic is understandable enough for demo
- Graph renders within 2 seconds for up to 200 nodes

**Downgrade Path:** Only generate graph from current basket (no historical merge). Connect nodes by shared keywords/theme similarity. Use normalized lowercase label matching only.

**Priority:** P1

---

### Feature 6: Simple Personalization / Recommendation (P1)

**Purpose:** Use past swipes to slightly improve future feed relevance.

**How user uses it:** Indirectly — future cards appear more aligned with prior preferences.

**Approach:**

- Log all user-card interactions: swipe direction, dwell time, card keywords, timestamp
- Cold start: rank by trending score (stars, likes, recency)
- Warm start: content-based filtering — keyword overlap between liked-card tags and new-card tags, weighted by recency and frequency
- Recommendation ranking runs in < 500ms per session

**Success Criteria:**

- Can demonstrate "because you liked X, we surfaced more Y"
- Ranking is explainable (not black box)
- Returning users see noticeably personalized ordering vs. random

**Downgrade Path:** Keyword overlap scoring only. Or mock "personalized" reorder for demo.

**Priority:** P1

---

### Feature 7: Source Enrichment (P1)

**Purpose:** Improve low-quality or sparse source items.

**How user uses it:** Indirectly — through better card quality and digest quality.

**Success Criteria:** Better explanations for terse repos/pages. Fewer empty or cryptic cards.

**Downgrade Path:** Only enrich selected basket items, not entire corpus.

**Priority:** P1

---

### Feature 8: Shareable Digest Page (P2)

**Purpose:** Let users share their generated briefing with others.

**Downgrade Path:** Export as screenshot only.

**Priority:** P2

---

### Feature 9: Cross-Session Graph Merge by Account (P2)

**Purpose:** Persist and connect graph across multiple days or users.

**Downgrade Path:** Mention as roadmap only during demo.

**Priority:** P2

---

## 2.4 Functional Requirements

1. System must ingest or load a set of AI news/source items.
2. System must normalize source data into a unified schema.
3. System must render swipeable cards.
4. System must save user selections to basket.
5. System must generate a digest based on selected items.
6. System must generate a lightweight knowledge graph from selected items.
7. System must persist core entities in database: content items, cards, user actions, basket selections, graph nodes/edges.
8. System should record interactions for simple personalization.
9. System should link every card back to original source.

## 2.5 Non-Functional Requirements

| Requirement | Target | Notes |
|---|---|---|
| Demo reliability | Core flow works with seeded data even if APIs fail | Most critical NFR |
| Card load time | < 200ms | Card browsing should feel instant |
| Swipe animation | 60fps | Smooth on modern browsers |
| Briefing generation | 5–15s | Ideally < 10s for demo |
| Knowledge graph render | < 2s | For graphs up to 200 nodes |
| Daily ingestion | < 5 min | Full pipeline: scrape → preprocess → store |
| Integration complexity | Low | One frontend, one backend, one DB preferred |
| Visual polish | High | UI should look intentional and productized |
| Explainability | High | Recommendation and graph logic simple enough to explain live |
| Graceful fallback | Full coverage | Cached demo data must work if live systems fail |

---

# Part 3: System Design & Data Model

## 3.1 Architecture Principle

Build a single coherent pipeline with controlled scope:

```
Source Ingestion → Content Normalization → Card Generation → User Swipes → Basket → Digest Generation → Graph Extraction/Visualization
```

Prefer: a single frontend app, a lightweight backend/API layer, one relational DB, seeded demo data plus optional live ingestion.

## 3.2 Data Model

### Core Entities

**content_items (raw ingested content)**

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| source | enum | github / huggingface / openai_blog / anthropic_blog / other |
| source_url | string | Original URL |
| title | string | Original title |
| raw_summary | string | Raw excerpt or abstract |
| raw_content | text | Full scraped text |
| metadata | JSON | Stars, forks, likes, citations, etc. |
| fetched_at | datetime | When ingested |
| published_at | datetime | Original publication date |

**cards (preprocessed, card-ready)**

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| content_item_id | UUID | FK → content_items |
| card_title | string | Cleaned, concise title |
| card_summary | string | One-line summary (< 120 chars) |
| keywords | string[] | 3–5 topic tags |
| thumbnail_keyword | string | Primary visual keyword |
| cleaned_text | text | Full text for briefing use |
| quality_score | float | 0–1 |
| trending_score | float | Normalized popularity metric |

**user_actions (interaction log)**

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id / session_id | string | User or session identifier |
| card_id | UUID | FK → cards |
| action | enum | swipe_right / swipe_left / undo |
| dwell_time_ms | int | Time spent viewing card |
| session_date | date | Which daily session |
| created_at | datetime | Timestamp |

**basket_items**

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id / session_id | string | User or session identifier |
| card_id | UUID | FK → cards |
| session_date | date | |
| added_at | datetime | |

**briefings**

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id / session_id | string | |
| card_ids | UUID[] | Cards included |
| content | text | Generated briefing (Markdown/HTML) |
| reading_time_min | float | Estimated reading time |
| generated_at | datetime | |
| share_token | string | nullable, for sharing |

**graph_nodes**

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id / session_id | string | |
| label | string | Concept name (normalized lowercase) |
| description | string | Short definition |
| first_seen | datetime | When first added |
| last_seen | datetime | Most recent card referencing this |
| frequency | int | How many cards contributed |

**graph_edges**

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id / session_id | string | |
| source_node_id | UUID | FK → graph_nodes |
| target_node_id | UUID | FK → graph_nodes |
| relationship | string | Edge label (related_to, mentions, overlaps_with, builds_on) |
| weight | float | Strength (incremented on re-encounter) |
| created_at | datetime | |

### Entity Relationships

- User 1:N user_actions, 1:N basket_items, 1:N briefings, 1:N graph_nodes, 1:N graph_edges
- content_items 1:1 cards
- cards 1:N user_actions, 1:N basket_items
- briefings N:M cards (via card_ids array)
- graph_nodes N:M graph_nodes (via graph_edges)

---

# Part 4: Team Task Breakdowns

## Timeline Assumptions

- 3-day hackathon: Friday evening, Saturday (full day), Sunday (until demo)
- Friday Night: ~3 hours (setup + scope lock)
- Saturday: ~12 hours (Morning, Afternoon, Evening)
- Sunday: ~8 hours (Morning + Afternoon), demo in late afternoon

---

## Sam — Crawling + Preprocessing + Project Management

**Mission:** Own the source ingestion pipeline, content normalization spec, and delivery coordination so the team stays integrated and on schedule.

### Task List

| # | Task Title | Description | Priority | Est. Time | Dependencies | Labels |
|---|---|---|---|---|---|---|
| S1 | Set up Linear project structure | Create projects, labels, cycles, board columns, assign initial P0 tickets | P0 | 45min | None | `infra`, `pm` |
| S2 | Define canonical content_item schema | Write JSON schema for content flowing between modules (ingestion → preprocessing → cards → briefing → graph). Share as Linear doc. | P0 | 1h | None | `infra`, `docs` |
| S3 | Create source list + ingestion priority order | Decide which sources to build first, which to fallback | P0 | 20min | None | `docs`, `ingestion` |
| S4 | Build GitHub Trending scraper | Scrape github.com/trending, extract repo name, description, stars, language, URL. Output: normalized JSON. | P0 | 2h | S2 | `backend`, `ingestion` |
| S5 | Build HuggingFace papers/models fetcher | Use HF API or scrape huggingface.co/papers for daily papers: title, abstract, URL, authors. | P0 | 2h | S2 | `backend`, `ingestion` |
| S6 | Build OpenAI blog scraper | Fetch latest posts from OpenAI blog via RSS or scraping. | P1 | 1.5h | S2 | `backend`, `ingestion` |
| S7 | Build Anthropic blog scraper | Fetch latest posts from Anthropic blog via RSS or scraping. | P1 | 1.5h | S2 | `backend`, `ingestion` |
| S8 | Normalize source metadata into shared format | Unify all scraper outputs into canonical schema. Remove low-quality/duplicate items. | P0 | 1.5h | S4, S5 | `backend`, `ingestion` |
| S9 | Create fallback seeded dataset | Curate 15–20 pre-scraped items as normalized JSON for demo reliability. | P0 | 1h | S4, S5 | `data`, `demo` |
| S10 | Build ingestion scheduler/trigger | Script that runs all scrapers, deduplicates, and writes to DB. Manual trigger + optional cron. | P0 | 1h | S8, Steve's DB | `backend`, `infra` |
| S11 | Produce sample dataset for Steve/UI integration | Deliver a clean JSON file Steve can immediately use for frontend development. | P0 | 30min | S8 | `data`, `integration` |
| S12 | Write ingestion README for team | Document how to run scrapers, where data lives, schema fields. | P1 | 30min | S8 | `docs` |
| S13 | Integration test: ingestion → preprocessing → cards | Verify end-to-end data flow from scraper output to preprocessed card data in DB. | P0 | 1h | S10, Sunny's tasks | `testing` |
| S14 | Run standups and unblock team | Morning + afternoon check-ins each day. Update Linear board. Flag blockers. | P0 | Ongoing | None | `pm` |
| S15 | Run source quality review before demo | Verify cards look good, titles aren't cryptic, no garbage data. | P0 | 30min | All ingestion tasks | `testing`, `demo` |

### Collaboration Interfaces

- **Delivers to:** Sunny (cleaned text fields), Liam (source metadata & tags), Steve (schema for DB/UI), Harry (keywords for graph), Alex (card display field expectations)
- **Needs from:** Steve (DB connection, card storage endpoint), team agreement on schema

### Milestones

| Checkpoint | Tasks | Goal |
|---|---|---|
| Friday Night | S1, S2, S3, S9 (start) | Linear set up; schema agreed; source priority set |
| Saturday Morning | S4, S5, S8, S9, S11 | GitHub + HF scrapers working; fallback data ready; sample data to Steve |
| Saturday Afternoon | S10, S13 | Scheduler running; integration test passes |
| Saturday Evening | S6, S7, S15 | Blog scrapers; source quality review |
| Sunday Morning | S14, bug fixes | Unblock others; fix pipeline issues |
| Sunday Afternoon | S14, demo support | Final integration check; support demo prep |

---

## Sunny — Preprocessing + 10-Minute Briefing + Demo Video

**Mission:** Own the language experience — make content understandable, generate the digest, and support the storytelling/video narrative.

### Task List

| # | Task Title | Description | Priority | Est. Time | Dependencies | Labels |
|---|---|---|---|---|---|---|
| SU1 | Define target digest structure | Document the sections, tone, length, and style of the briefing output. | P0 | 45min | None | `docs`, `briefing` |
| SU2 | Define tone guidelines | Simple, helpful, non-technical. Write examples of good vs. bad card summaries and briefing prose. | P0 | 30min | None | `docs`, `preprocess` |
| SU3 | Build text cleaning pipeline | Strip HTML, ads, boilerplate from raw scraped content. Use BeautifulSoup/readability-lxml. Output: cleaned plaintext. | P0 | 2h | Sam's S2 | `backend`, `preprocess` |
| SU4 | Build card metadata generator | Use LLM to produce: concise title, one-line summary (< 120 chars), 3–5 keywords per item. | P0 | 2.5h | SU3 | `backend`, `preprocess` |
| SU5 | Design briefing prompt template | Write system prompt + user prompt for digest generation. Must produce ~2000-word, non-technical, 10-min readable output with sections. | P0 | 2h | SU1 | `backend`, `briefing` |
| SU6 | Implement briefing generation endpoint | Endpoint accepts basket card IDs → retrieves cleaned text → calls LLM → returns formatted briefing. Streaming preferred. | P0 | 3h | SU5, SU3, Steve's DB | `backend`, `briefing` |
| SU7 | Add source attribution to briefing | Every section links back to original source URL. | P0 | 30min | SU6 | `backend`, `briefing` |
| SU8 | Test briefing quality (3–5 samples) | Generate sample briefings, verify readability, accuracy, reading time. Iterate on prompt. | P0 | 1.5h | SU6 | `testing`, `briefing` |
| SU9 | Create fallback pre-generated digests | Cache 2–3 pre-generated digests for known demo card selections. | P0 | 1h | SU6 | `demo`, `briefing` |
| SU10 | Implement quality assessment scoring | Score each item 0–1 based on content length, source authority, completeness. | P1 | 1.5h | SU3 | `backend`, `preprocess` |
| SU11 | Build supplementary search trigger | For low-quality items, run web search to find additional context. | P1 | 2h | SU10 | `backend`, `preprocess` |
| SU12 | Review keyword quality for graph readability | Coordinate with Harry — ensure keywords make sense as graph node labels. | P1 | 30min | SU4, Harry | `integration` |
| SU13 | Produce demo script language | Write the narration and talking points for the demo presentation. | P1 | 1.5h | All modules stable | `demo` |
| SU14 | Record and edit demo video | Screen-record the full user flow; edit with narration. 2–3 minutes. | P1 | 3h | All modules done | `demo` |
| SU15 | Create 2–3 sample demo personas/paths | Prepare named demo scenarios showing different user interests. | P1 | 45min | SU9 | `demo` |

### Collaboration Interfaces

- **Needs from:** Sam (raw content JSON, schema), Steve (DB endpoints, digest display page), Alex (video narrative)
- **Delivers to:** Steve (preprocessed card data), Alex (briefing content via API, demo video), Harry (keyword quality review)

### Milestones

| Checkpoint | Tasks | Goal |
|---|---|---|
| Friday Night | SU1, SU2, SU5 (start) | Digest structure defined; tone guidelines written; prompt draft started |
| Saturday Morning | SU3, SU5 | Text cleaning working; briefing prompt finalized |
| Saturday Afternoon | SU4, SU6, SU7 | Card metadata generated; briefing API functional with source links |
| Saturday Evening | SU8, SU9 | Briefing quality validated; fallback digests cached |
| Sunday Morning | SU10, SU12, SU13, SU15 | Quality scoring; keyword review; demo script and personas |
| Sunday Afternoon | SU14 | Demo video recorded and edited |

---

## Steve — UI + Database + Testing

**Mission:** Own the app shell, database schema, state flow, and demo reliability.

### Task List

| # | Task Title | Description | Priority | Est. Time | Dependencies | Labels |
|---|---|---|---|---|---|---|
| ST1 | Initialize app structure | Set up Next.js/React frontend + backend (FastAPI or Next.js API routes). Configure repo structure, env vars. | P0 | 1.5h | None | `infra`, `frontend`, `backend` |
| ST2 | Configure database + environment | Set up Supabase (or SQLite for speed). Configure connection. | P0 | 1h | None | `infra`, `db` |
| ST3 | Create DB schema | Implement all tables: content_items, cards, user_actions, basket_items, briefings, graph_nodes, graph_edges. | P0 | 1.5h | Sam's S2 | `backend`, `db` |
| ST4 | Seed initial content to DB | Load Sam's sample/fallback dataset into the database. | P0 | 30min | ST3, Sam's S11 | `data`, `db` |
| ST5 | Build card deck UI (swipe component) | Swipeable card stack with left/right gestures, exit animations, or Save/Skip buttons as fallback. | P0 | 3h | ST1 | `frontend`, `card-ui` |
| ST6 | Build "Today's AI Signals" feed page | Main page that loads cards from DB/API, renders the card deck. | P0 | 1h | ST5, ST4 | `frontend` |
| ST7 | Implement basket counter/state + basket page | Visual basket indicator (X/5), basket review page where user can remove items. | P0 | 1.5h | ST5 | `frontend` |
| ST8 | Build interaction logging endpoint | POST /interactions — log swipe direction, dwell time, user/session, card. | P0 | 1h | ST3 | `backend` |
| ST9 | Build "Generate Briefing" action flow | Button triggers briefing generation, shows loading state, receives and stores result. | P0 | 1h | Sunny's SU6 | `frontend`, `backend` |
| ST10 | Build briefing display page | Render the generated briefing (Markdown → HTML). Clean typography, source links, reading time estimate. | P0 | 2h | Sunny's SU6 | `frontend`, `briefing` |
| ST11 | Build graph page/container | Page with graph visualization component (provided by Alex). Route: /graph. | P0 | 1h | Alex's A3, Harry's H5 | `frontend` |
| ST12 | Build app layout and navigation | Top nav, page routing: Home (cards) → Basket → Briefing → Knowledge Graph. | P0 | 1h | ST1 | `frontend`, `design` |
| ST13 | Implement loading/error states | Skeleton loaders, spinners, error fallbacks for all pages. | P1 | 1h | ST5, ST10 | `frontend`, `design` |
| ST14 | Build simple session management | Cookie or in-memory session — no auth needed. Mock user for demo. | P1 | 45min | ST3 | `backend`, `infra` |
| ST15 | Create smoke test checklist | Document the end-to-end test path. Run before every integration checkpoint. | P0 | 45min | All P0 modules | `testing` |
| ST16 | Test cross-page state flow | Verify: cards load → swipe → basket updates → briefing generates → graph displays. | P0 | 1.5h | All P0 modules | `testing` |
| ST17 | Test failure fallback with seeded data | Verify app works fully offline with cached/seeded content. | P0 | 1h | ST4, SU9 | `testing`, `demo` |
| ST18 | Support deployment | Deploy frontend (Vercel) + backend (Railway/Render). | P0 | 1.5h | All P0 | `infra`, `deployment` |
| ST19 | Polish UI — animations, responsive | Refine swipe animations, transitions, mobile-friendly layout. | P1 | 2h | ST5, ST10 | `frontend`, `polish` |

### Collaboration Interfaces

- **Needs from:** Sam (schema, sample data), Sunny (preprocessed cards, briefing API), Alex (graph visualization component, card designs), Liam (recommendation-ranked card list), Harry (graph data endpoints)
- **Delivers to:** Everyone (DB access, API endpoints, frontend framework, deployment)

### Milestones

| Checkpoint | Tasks | Goal |
|---|---|---|
| Friday Night | ST1, ST2, ST3 | App skeleton running; DB schema drafted |
| Saturday Morning | ST4, ST5, ST6, ST12 | Seeded data in DB; card deck rendering; app layout done |
| Saturday Afternoon | ST7, ST8, ST9, ST10 | Basket flow; interaction logging; briefing display |
| Saturday Evening | ST11, ST16, ST17 | Graph page; end-to-end test; fallback verified |
| Sunday Morning | ST13, ST14, ST15, ST18 | Polish; session management; deployment |
| Sunday Afternoon | ST19, final bug fixes | Demo-ready stable build |

---

## Alex — UI + Demo Video + Knowledge Graph (Assisting Harry)

**Mission:** Make the product visually impressive and help package the final story.

### Task List

| # | Task Title | Description | Priority | Est. Time | Dependencies | Labels |
|---|---|---|---|---|---|---|
| A1 | Design card visual layout | Card component design: title typography, keyword tag pills, source badge, swipe affordances. | P0 | 2h | Sam's S2 | `frontend`, `design` |
| A2 | Design briefing page layout | Typography, section headings, source citation styling, reading progress indicator. | P0 | 1.5h | None | `frontend`, `design` |
| A3 | Build knowledge graph visualization component | Use react-force-graph or Cytoscape.js. Support zoom, pan, click-to-inspect. | P1 | 4h | Harry's H5 | `frontend`, `graph` |
| A4 | Highlight today's additions in graph | Visually distinguish new nodes/edges from historical (color, glow, animation). | P1 | 1.5h | A3 | `frontend`, `graph` |
| A5 | Build graph page layout | Full page with graph visualization, node detail sidebar on click. | P1 | 1.5h | A3 | `frontend`, `graph` |
| A6 | Add branding, typography, spacing, motion | Overall app visual polish — consistent colors, spacing, branded feel. | P1 | 2h | ST1 | `frontend`, `polish` |
| A7 | Support graph visualization styling with Harry | Work with Harry on layout readability, simplify graph density. | P1 | 1h | A3, Harry's H4 | `frontend`, `graph` |
| A8 | Create demo-friendly loading/empty/error states | Skeleton loaders, "no cards" state, briefing generating animation. | P1 | 1h | ST5, ST10 | `frontend`, `design` |
| A9 | Prepare screenshot-ready states | Clean UI states for submission screenshots. | P1 | 30min | All UI done | `demo` |
| A10 | Record polished walkthrough clips | Screen-capture the key demo moments. | P1 | 1.5h | All modules done | `demo` |
| A11 | Edit final demo video (with Sunny) | Assemble clips, narration, titles into 2–3 min video. | P1 | 2h | A10, SU13 | `demo` |
| A12 | Create UI consistency checklist | Ensure fonts, colors, spacing are consistent across all pages. | P1 | 30min | A6 | `design`, `testing` |

### Collaboration Interfaces

- **Needs from:** Steve (UI framework, card component base), Harry (graph data API, node/edge schema), Sunny (briefing API format, narration)
- **Delivers to:** Steve (card design, briefing design, graph visualization component), Harry (graph styling), Sunny (demo video assets)

### Milestones

| Checkpoint | Tasks | Goal |
|---|---|---|
| Friday Night | A1 (start), A2 (start) | Card and briefing design direction set |
| Saturday Morning | A1, A2 | Designs finalized and handed to Steve |
| Saturday Afternoon | A6, A8 | Branding polish; loading states |
| Saturday Evening | A3 (start) | Graph visualization prototype rendering test data |
| Sunday Morning | A3 (finish), A4, A5, A7 | Graph visualization complete with highlights |
| Sunday Afternoon | A9, A10, A11, A12 | Screenshots, video recording and editing |

---

## Liam — Recommendation System + Crawling + Preprocessing

**Mission:** Implement a simple, believable recommendation layer and support ingestion/preprocessing throughput.

### Task List

| # | Task Title | Description | Priority | Est. Time | Dependencies | Labels |
|---|---|---|---|---|---|---|
| L1 | Define recommendation scoring formula | Document the heuristic: keyword overlap + recency + popularity weighting. | P0 | 45min | Sam's S2 | `docs`, `recommender` |
| L2 | Assist Sam: build additional scraper | Pick up one source target (e.g., HF trending models, or additional blog). | P0 | 2h | Sam's S2 | `backend`, `ingestion` |
| L3 | Build keyword extraction pipeline | TF-IDF or LLM-based keyword extraction from cleaned text. Output: keyword list per item. | P0 | 2h | Sunny's SU3 | `backend`, `preprocess` |
| L4 | Build trending score calculation | Compute normalized trending score from metadata (stars, forks, likes, citations). Used for cold-start ranking. | P0 | 1h | Sam's S4, S5 | `backend`, `preprocess` |
| L5 | Implement cold-start ranking | New users (no history): rank cards by trending score. | P0 | 1h | L4, Steve's ST4 | `backend`, `recommender` |
| L6 | Build user preference profile from saves/skips | Aggregate keywords from liked cards into a user interest vector. | P1 | 1.5h | L3, Steve's ST8 | `backend`, `recommender` |
| L7 | Build recommendation scoring engine | Compute similarity between user interest keywords and new card keywords. Rank cards by score. | P1 | 2.5h | L6, L3 | `backend`, `recommender` |
| L8 | Build recommendation API endpoint | GET /cards/recommended?session_id=X → returns ordered card list. Falls back to cold-start if no history. | P1 | 1.5h | L7, L5 | `backend`, `recommender` |
| L9 | Test recommendation quality | Simulate user with known preferences, verify ordering improves. Create "before vs after" comparison. | P1 | 1h | L8 | `testing`, `recommender` |
| L10 | Write judge-facing explanation of personalization | Short paragraph explaining the recommendation tradeoff (heuristic over ML, explainability over accuracy). | P1 | 30min | L7 | `demo`, `docs` |
| L11 | Help preprocess tags and categories | Support Sunny with keyword consistency and category normalization. | P1 | 1h | SU4, L3 | `preprocess` |

### Collaboration Interfaces

- **Needs from:** Sam (raw content, metadata), Sunny (cleaned text for keyword extraction), Steve (interaction logs, card API)
- **Delivers to:** Steve (recommendation API for frontend card ordering), Harry (keywords for graph node extraction), Sunny (keyword quality)

### Milestones

| Checkpoint | Tasks | Goal |
|---|---|---|
| Friday Night | L1 | Recommendation formula documented |
| Saturday Morning | L2, L3, L4 | Additional scraper done; keyword extraction; trending scores |
| Saturday Afternoon | L5 | Cold-start ranking working |
| Saturday Evening | L6, L7 | Preference profile + recommendation engine functional |
| Sunday Morning | L8, L9, L10 | Recommendation API serving; quality tested; judge explanation |
| Sunday Afternoon | L11, bug fixes | Polish recommendation; help integration |

---

## Harry — Knowledge Graph (Primary Owner)

**Mission:** Own the knowledge graph generation logic and data model so the product has a strong "second wow moment."

### Task List

| # | Task Title | Description | Priority | Est. Time | Dependencies | Labels |
|---|---|---|---|---|---|---|
| H1 | Define graph node + edge schema | Document node/edge fields, relationship types, merge rules. | P0 | 1h | Sam's S2 | `docs`, `graph` |
| H2 | Decide extraction strategy | Choose: keyword/entity extraction via spaCy NER, LLM labeling, or KeyBERT. Document decision. | P0 | 45min | None | `research`, `graph` |
| H3 | Build concept extraction pipeline | Extract key concepts from card text as graph nodes. At least 3 nodes per card. | P1 | 3h | Liam's L3, Sunny's SU3 | `backend`, `graph` |
| H4 | Build edge creation logic | Connect nodes: co-occurrence in same card = connected. Optionally LLM-labeled relationship type. Keep edge types simple: related_to, mentions, overlaps_with. | P1 | 2.5h | H3 | `backend`, `graph` |
| H5 | Build graph generation API endpoint | POST /graph/generate — accepts basket card IDs, returns nodes + edges JSON. GET /graph?session_id=X — returns full graph. | P1 | 2h | H4, Steve's ST3 | `backend`, `graph` |
| H6 | Build lightweight merge algorithm | Find matching existing nodes (normalized lowercase label match), merge duplicates, update edge weights, add new nodes/edges. | P1 | 2h | H4 | `backend`, `graph` |
| H7 | Build node normalization function | Lowercase, stem/lemmatize, deduplicate near-identical concept labels. | P1 | 1h | H3 | `backend`, `graph` |
| H8 | Test graph quality with 3–5 sample baskets | Feed sample cards through pipeline, verify: nodes make sense, duplicates merged, edges meaningful. | P1 | 1.5h | H5 | `testing`, `graph` |
| H9 | Simplify graph density for readability | If graph is too dense, filter to top-N nodes by frequency, prune weak edges. | P1 | 1h | H8 | `backend`, `graph` |
| H10 | Work with Alex on layout/styling | Coordinate visualization: node sizes, colors, labels, edge rendering. | P1 | 1h | Alex's A3 | `frontend`, `graph` |
| H11 | Write judge explanation: "how graph grows" | Short paragraph for demo showing long-term vision. | P1 | 30min | H6 | `demo`, `docs` |
| H12 | Build graph export (JSON) | Export user's full graph as portable JSON. | P2 | 1h | H5 | `backend`, `graph`, `sharing` |

### Collaboration Interfaces

- **Needs from:** Sunny (cleaned text), Liam (keywords per card), Steve (DB access, graph tables), Alex (visualization component)
- **Delivers to:** Alex (graph data via API), Steve (graph endpoints for frontend routing)

### Milestones

| Checkpoint | Tasks | Goal |
|---|---|---|
| Friday Night | H1, H2 | Graph schema + extraction strategy decided |
| Saturday Morning | H3 | Concept extraction working on test data |
| Saturday Afternoon | H4, H7 | Edge creation + node normalization |
| Saturday Evening | H5, H6 | API endpoints + merge algorithm |
| Sunday Morning | H8, H9, H10 | Quality tested; density simplified; styling coordinated |
| Sunday Afternoon | H11, H12 (if time) | Judge explanation; export if time permits |

---

# Part 5: Linear Project Management Plan

## 5.1 Project Structure

**Option A — 6 Projects (detailed):**

1. MVP Core Product
2. AI Pipeline (ingestion + preprocessing)
3. Frontend & UX
4. Graph & Personalization
5. Demo & Submission
6. Infra & Deployment

**Option B — 4 Projects (simpler, recommended for hackathon speed):**

1. Core App (frontend + backend + DB)
2. AI Pipeline (ingestion + preprocessing + briefing)
3. Graph & Recommender
4. Demo / Infra

## 5.2 Label Taxonomy

**Type labels:** `feature`, `bug`, `infra`, `blocker`, `polish`, `research`, `demo`, `docs`

**Area labels:** `ingestion`, `preprocess`, `frontend`, `backend`, `db`, `recommender`, `graph`, `briefing`, `testing`, `deployment`

**Priority:** Use Linear's built-in priority levels — map Urgent/High → P0, Medium → P1, Low → P2

**Classification guide:**

- `feature` — user-facing or core system capability
- `bug` — something broken or incorrect
- `infra` — setup, deployment, config, CI, environment
- `blocker` — prevents parallel progress or integration
- `polish` — improves presentation, clarity, UX, visuals
- `research` — exploration or spike needed before implementation

## 5.3 Workflow Status Columns

| Status | Description |
|---|---|
| **Backlog** | Nice idea or future work; not committed yet |
| **Todo** | Approved and ready to be worked on; clear owner assigned |
| **In Progress** | Actively being worked on by owner |
| **Blocked** | Cannot continue — missing dependency or waiting on another issue |
| **Review** | Ready for teammate validation or integration check |
| **Done** | Shipped, merged, or confirmed complete |
| **Demo Ready** (optional) | Feature complete AND explicitly validated for live presentation |

## 5.4 Milestone / Cycle Setup

- **Cycle 1: "Friday Night — Foundation"** — Scope lock, schema, skeleton, Linear setup
- **Cycle 2: "Saturday — Build"** — All P0 modules independently working + integration
- **Cycle 3: "Sunday — Polish & Demo"** — Integration, polish, deployment, demo prep, video

## 5.5 Ticket Writing Template

```
Title: Short action-based title
Context: Why this task matters in product flow
Goal: What should be true when this ticket is done
Acceptance Criteria: Checklist of concrete success conditions
Dependency: What must exist first
Owner: Assigned teammate
Priority: P0 / P1 / P2
Labels: [type] [area]
```

**Example:**

```
Title: Implement basket save/skip action logging
Context: The app needs to persist user card interactions for basket flow and personalization.
Goal: Save every save/skip action to database and expose it for recommendation logic.
Acceptance Criteria:
  - Records card ID, session ID, action type, timestamp
  - Works from frontend interaction
  - Failed writes show graceful error handling
  - Tested with at least 5 interactions
Dependency: DB schema for user_actions; Card UI available
Owner: Steve
Priority: P0
Labels: feature, backend, db
```

## 5.6 Standup Workflow

| Time | Format | Duration | Focus |
|---|---|---|---|
| Friday Night 7:00 PM | Full kickoff | 30–45 min | Scope freeze, assign P0 tickets, schema agreement |
| Saturday 9:00 AM | Morning standup | 10 min | Status on P0 items, surface blockers |
| Saturday 1:00 PM | Midday sync | 5 min | Integration readiness, reassign if stuck |
| Saturday 6:00 PM | Evening review | 10 min | Assess MVP completeness, plan Sunday |
| Sunday 9:00 AM | Morning sync | 10 min | Integration status, demo plan |
| Sunday 2:00 PM | Final check | 5 min | Confirm demo flow, assign demo roles, code freeze |

---

# Part 6: Tech Stack Recommendations

| Module | Primary Choice | Alternative | Reasoning |
|---|---|---|---|
| **Data Ingestion / Scraping** | Python + BeautifulSoup + requests (+ GitHub REST API, HF API) | Scrapy; cheerio (Node.js) | BS4 + requests is fastest to set up for targeted scraping. GitHub and HF have usable APIs. Scrapy/cheerio are alternatives but add complexity for 3–5 sources. |
| **Preprocessing** | Python + readability-lxml + LLM API (for summarization & keywords) | trafilatura + spaCy | readability-lxml excels at article extraction. LLM-based summarization produces higher-quality card metadata. trafilatura is a solid alternative. |
| **Keyword Extraction** | KeyBERT / YAKE + spaCy noun chunks | LLM extraction (slower but higher quality) | Fast enough for hackathon, visually useful for tags. LLM extraction as upgrade path. |
| **Backend Services** | FastAPI (Python) + APScheduler | Next.js API routes; Flask + Celery | FastAPI has async support, auto-generated OpenAPI docs, fastest Python DX. APScheduler handles cron simply. Next.js API routes good if team prefers JS monolith. |
| **Database** | Supabase (PostgreSQL) | Neon + Prisma; SQLite + JSON files | Supabase gives hosted Postgres with REST API out of the box. SQLite simpler but lacks hosting/concurrent access. Neon + Prisma strong for TypeScript teams. |
| **Frontend / UI** | Next.js (React) + Tailwind CSS + react-tinder-card | Vite + React + Framer Motion | Next.js provides routing, SSR, great DX. react-tinder-card handles swipe UX out of the box. Framer Motion offers more custom animation but more setup. |
| **State Management** | Zustand or simple React useState | Redux (overkill) | Zustand is minimal and hackathon-friendly. Simple local state may suffice. |
| **Recommendation System** | scikit-learn (TF-IDF + cosine similarity) | Keyword overlap heuristic (no ML library needed) | TF-IDF + cosine is trivial to implement. Keyword overlap is even simpler and sufficient for demo. |
| **Knowledge Graph** | spaCy (NER) + NetworkX + LLM for relationship labeling | KeyBERT + simple co-occurrence | spaCy provides fast NER, NetworkX handles graph operations in-memory. LLM calls label relationships. KeyBERT + co-occurrence is the simplest viable approach. |
| **KG Visualization** | react-force-graph (2D) | Cytoscape.js; vis-network; React Flow | react-force-graph is React-native, performant, supports zoom/pan/click with minimal config. Cytoscape.js and React Flow are strong alternatives. |
| **Briefing Generation** | Claude API (claude-sonnet-4-20250514) via Anthropic SDK | OpenAI GPT-4o | Claude Sonnet offers excellent long-form writing quality. GPT-4o is a strong alternative. Use streaming for perceived performance. Use whichever the team already has access to. |
| **Sharing** | UUID-based share links + JSON export | Screenshot export (html2canvas) | Token-based share links are simple. Screenshot export is the minimal fallback. |
| **Hosting / Deployment** | Vercel (frontend) + Supabase (DB) + Railway (backend) | Fly.io; Render | Vercel has zero-config Next.js deploy. Railway is quick for Python backends. Easiest full-stack deployment. |
| **Project Management** | Linear | — | Team's chosen tool. |
| **Code Repository** | GitHub (monorepo) | GitLab | Standard, integrates with Linear, everyone knows it. Monorepo for hackathon speed. |
| **Demo Video** | OBS Studio (recording) + CapCut / iMovie (editing) | Loom | OBS is free and high quality. CapCut/iMovie for fast editing. Loom is simpler but less flexible. |
| **Testing** | Manual QA checklist + seeded data + smoke test scripts | — | Best use of hackathon time. No unit test frameworks needed. |
| **Logging** | Console logs + DB logging table + optional Sentry | — | Enough for debugging. No full analytics suite needed. |

### Quick-Start Install

```bash
# Backend (Python)
pip install fastapi uvicorn beautifulsoup4 requests readability-lxml \
    apscheduler scikit-learn spacy networkx anthropic supabase keybert
python -m spacy download en_core_web_sm

# Frontend
npx create-next-app@latest frontend --typescript --tailwind
cd frontend
npm install react-tinder-card react-force-graph-2d zustand
```

---

# Part 7: 3-Day Execution Plan

## Friday Night (~3 hours)

**Primary goal:** Lock scope, lock architecture, create working skeleton, prevent chaos.

**Must complete:**

- Scope freeze on Must-Have (P0) features
- Canonical content schema agreed and documented
- Repo structure and branch strategy
- Linear board created with P0 tickets assigned
- App skeleton running (even if empty)
- DB schema drafted
- At least one source ingestion path working OR seeded JSON ready
- Digest prompt structure drafted

**Can delay:** Advanced recommender, real graph merge, sharing features, auth.

**Who must sync:**

- Everyone for 30–45 min kickoff
- Sam, Steve, Sunny, Harry must align on schemas/contracts
- Alex and Liam align on frontend/recommender dependencies

**Avoid failure:**

- Do not debate tech stacks for too long — pick and move
- Do not build auth
- Do not over-design APIs
- Decide fallback data strategy tonight

---

## Saturday Morning

**Primary goal:** Get all core modules independently working.

**Key outputs:**

- Ingestion/preprocessing pipeline produces usable content
- Card feed renders (even with seeded data)
- Basket interaction works
- Briefing generation works in isolation (at least with static input)
- Graph generation works in isolation (sample basket)

**Can delay:** Personalization reranking, motion polish, full deployment.

**Who must sync:**

- Sam + Liam on data
- Steve + Alex on UI
- Sunny + Sam on cleaned text
- Harry + Alex + Steve on graph payload format

**Avoid failure:** Keep graph logic simple. Keep recommendation heuristic simple. Test each module with fixed sample inputs.

---

## Saturday Afternoon

**Primary goal:** Integrate the full user flow end-to-end.

**Key outputs:**

- Card feed → basket → digest → graph works as one path
- Data persistence partially working
- First usable demo path exists

**Must complete:**

- End-to-end happy path functional
- Basket selection passes correct payload into briefing and graph modules
- UI displays returned outputs properly

**Can delay:** Perfect styling, full recommender loop, sharing page.

**Who must sync:** Steve with everyone (he's the integration hub).

**Avoid failure:**

- Stop adding features during integration
- Use mock data where integration is slow
- Choose one primary demo path and lock it

---

## Saturday Evening

**Primary goal:** Stabilize, polish, and build fallback demo safety nets.

**Key outputs:**

- Reliable demo state
- Seeded fallback content verified
- Backup pre-generated digest cached
- Graph readable and polished
- Script draft for final demo

**Must complete:**

- Offline-safe demo path works
- Error handling on core pages
- Visual cleanup on core pages
- Backup video recording begins

**Can delay:** Advanced recommendation display, sharing.

**Avoid failure:**

- No major refactors Saturday night
- No new external dependencies
- No last-minute schema changes

---

## Sunday Morning

**Primary goal:** Make the demo persuasive, not just functional.

**Key outputs:**

- Final polished demo flow
- Final demo script
- Final hosted build
- Backup recording
- Submission assets in progress

**Must complete:**

- App deployed
- Demo script rehearsed
- One compelling story path end-to-end
- Video backup ready

**Can delay:** Small UI polish, non-essential edge cases.

**Who must sync:**

- Whole team for end-to-end review
- Alex + Sunny on video
- Sam on narrative flow
- Steve on final deployment
- Harry/Liam on technical explanation snippets

**Avoid failure:**

- Do not let everyone work on separate improvements endlessly
- Freeze code once demo path is stable

---

## Sunday Afternoon / Submission Window

**Primary goal:** Submit confidently and protect against demo risk.

**Key outputs:**

- Submission complete
- Live demo rehearsed
- Backup video and screenshots ready
- Talking points memorized

**Must complete:**

- Final repository cleanliness
- Submission form
- Demo order locked
- Backup browser tabs / seeded data loaded

**Who must sync:**

- Sam coordinates final check
- Demo presenters rehearse twice
- Steve verifies deployed app
- Alex verifies video backup
- Sunny verifies digest quality
- Harry verifies graph
- Liam verifies personalization explanation

**Avoid failure:**

- No code changes after demo freeze unless absolutely necessary
- Use seeded demo account/session
- Have screenshots/video ready if live demo breaks

---

# Part 8: Risks, Trade-offs & Simplification Strategy

| Risk | Impact | Response | Simpler Fallback |
|---|---|---|---|
| Scraping is unstable | No content to show | Use seeded dataset + manual refresh scripts | Static curated JSON (15–20 items) |
| Content quality varies | Bad cards, bad summaries | Run preprocessing + LLM simplification | Curate only top 15 demo items manually |
| Recommendation takes too long | Wasted engineering time | Use keyword overlap + recency scoring | Mock "personalized" reorder |
| Graph merge becomes too complex | Harry/Alex get stuck | Use normalized label matching and small graph | Graph only for current basket, no merge |
| Frontend-backend integration drags | Core flow blocked | Use static mock endpoints first | Hardcode sample payloads in frontend |
| LLM output inconsistent | Digest quality weak | Strict prompt template + fallback cached outputs | Pre-generated digest for demo |
| Demo data is insufficient | Product looks empty | Seed 15–20 high-quality cards | Manual curated dataset |
| UI gesture bugs | Swipe feels unreliable | Use buttons with swipe-like animation | Save/Skip buttons only |
| Deployment fails late | No live demo | Deploy earlier Sunday morning | Local demo + recorded video |
| Video and live demo mismatch | Story feels messy | Lock final demo path before recording | One single canonical flow |
| API rate limits (GitHub, HF, LLM) | Pipeline breaks mid-demo | Pre-fetch all data; cache everything | All responses pre-cached |
| Team parallelizes incorrectly | Rework and conflicts | Linear dependencies + contract docs | Daily integration checkpoint |
| Scope creep | MVP incomplete | Assign P0/P1/P2 strictly; Sam enforces | Cut sharing, advanced recsys, multi-day graph |

### How to Avoid Common Hackathon Traps

**Doing too many features:**

- Freeze Must-Have by Friday night.
- Every new idea must answer: "Does this improve the demo path?"

**Integration failure:**

- Agree on contracts early (Sam's S2 is the first task).
- Use shared schemas. Test with fixed payloads before live integration.

**Demo crash:**

- Seed data. Cache digests. Record backup video. Prepare screenshots.

**Recommender/graph getting too heavy:**

- Use heuristics, not research-grade models.
- Optimize for explainability and visual effect.
- Current-basket graph is enough for MVP.

---

# Part 9: Demo Strategy & Final Recommendations

## 9.1 Recommended Demo Sequence

**Step 1 — Open with the pain:**

> "AI information is abundant, repetitive, and exhausting. We help users understand what matters in 10 minutes."

**Step 2 — Show the swipe feed:**

Open the app. Show 3–5 cards. Swipe right on interesting items, left to skip.

*Judge impact: instantly understandable, interactive, consumer-grade feel.*

**Step 3 — Show the basket:**

> "Now I've selected the topics I actually care about today."

*Judge impact: product feels personalized, not generic.*

**Step 4 — Generate the 10-minute briefing:**

Show digest generating (streaming). Highlight: low cognitive load, source grounding, industry impact, not too technical.

*Judge impact: clear AI value, obvious user utility.*

**Step 5 — Show the knowledge graph:**

> "This isn't just today's news — it becomes a map of what you're learning over time."

Show nodes/edges, clusters, concept overlap.

*Judge impact: strong visual "wow," future-product depth.*

**Step 6 — Mention personalization loop:**

> "Every swipe teaches the system what you care about."

*Judge impact: judges see retention and long-term product value.*

**Step 7 — Close with future vision:**

> "Today we help users consume AI news. Tomorrow this becomes a personalized AI learning memory system."

## 9.2 What Judges Will Remember

- Clean cards
- Smooth interaction
- Readable digest
- Attractive graph
- Confident storytelling

They will NOT reward an invisible recommender pipeline if the UI feels broken.

## 9.3 MVP Scope Snapshot

**P0 — Build this no matter what:**

- 15–20 curated AI cards from high-quality sources
- Save/skip interaction (swipe or buttons)
- Basket of 3–5 items
- Generated 10-minute digest
- Current-basket knowledge graph
- Clean, branded UI
- Seeded fallback data
- Demo video backup

**P1 — Add if stable:**

- Lightweight personalized reranking
- Graph merge with prior sessions
- Source enrichment for sparse items
- Nice UI motion polish
- Third+ scraping source

**P2 — Cut first:**

- Sharing
- Auth / user accounts
- Advanced recommender (embeddings, collaborative filtering)
- Cross-account graph persistence
- Advanced gesture micro-interactions

## 9.4 Making It Look Complete

**A. Lead with user pain, not tech.**
Start with the problem, not the architecture.

**B. Show one beautiful, coherent workflow.**
Not separate modules. One story: discover → choose → understand → remember.

**C. Make smart scoping look intentional.**

> "We deliberately used a lightweight recommendation layer and explainable graph logic to optimize reliability and user clarity in a high-speed environment."

That makes trade-offs look disciplined, not incomplete.

**D. Prioritize polish over hidden complexity.**
The swipe UI, the briefing readability, and the graph visual are what judges experience. Invest time there.

**E. Have a strong "future potential" line.**
Reframe from a news feed to a learning platform.

## 9.5 Immediate Next Actions (First 30 Minutes)

1. Freeze MVP scope: card feed + basket + digest + graph
2. Create Linear projects and labels
3. Define canonical content schema
4. Assign all P0 tickets
5. Decide fallback seeded data strategy
6. Lock frontend/backend contracts

## 9.6 First 2 Hours After Kickoff

1. Set up app shell and DB
2. Get sample content rendered
3. Get digest prompt working
4. Get graph payload format working
5. Start integration with mocked data first

---

*End of unified plan. For follow-ups (CSV export for Linear, detailed API contracts, system prompts for briefing, hour-by-hour schedule), ask and reference the relevant section.*
