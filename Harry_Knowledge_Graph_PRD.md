# Harry — Knowledge Graph (Primary Owner)

**Project:** 10min AI Daily — Hackathon PRD Extract

---

## 1. Your Mission

Own the knowledge graph generation logic and data model so the product has a strong **"second wow moment."** The knowledge graph is the feature that transforms 10min AI Daily from a news reader into a **learning memory system** — it's what judges will remember after the digest.

---

## 2. Feature Specification — Lightweight Knowledge Graph (P1)

**Purpose:** Visualize how selected topics connect over time.

**User interaction:** Opens graph after digest generation.

### 2.1 Sub-Features You Own

1. **Create Nodes:** Extract key concepts from each basket card (via NLP or LLM).
2. **Connect Nodes:** Identify relationships between nodes — co-occurrence in same card = connected; optionally LLM-labeled edge types (related_to, mentions, overlaps_with, builds_on).
3. **Merge Graph:** Each time new content is added, merge the new subgraph with the user's accumulated graph — find matching existing nodes (fuzzy label match), update edge weights, add new nodes/edges.
4. **Interactive Visualization (with Alex):** Zoom, pan, click-to-inspect node details. Today's additions visually highlighted.

### 2.2 Success Criteria

- Each card generates at least 3 concept nodes
- Users can clearly see concept clusters and relationships
- Graph looks visually impressive
- Connection logic is understandable enough for demo
- Graph renders within 2 seconds for up to 200 nodes

### 2.3 Downgrade Path

Only generate graph from current basket (no historical merge). Connect nodes by shared keywords/theme similarity. Use normalized lowercase label matching only.

---

## 3. Data Model — Your Tables

### 3.1 graph_nodes

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id / session_id | string | User or session identifier |
| label | string | Concept name (normalized lowercase) |
| description | string | Short definition |
| first_seen | datetime | When first added |
| last_seen | datetime | Most recent card referencing this |
| frequency | int | How many cards contributed |

### 3.2 graph_edges

| Field | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| user_id / session_id | string | User or session identifier |
| source_node_id | UUID | FK → graph_nodes |
| target_node_id | UUID | FK → graph_nodes |
| relationship | string | Edge label (related_to, mentions, overlaps_with, builds_on) |
| weight | float | Strength (incremented on re-encounter) |
| created_at | datetime | Timestamp |

### Entity Relationships

- User 1:N graph_nodes, 1:N graph_edges
- graph_nodes N:M graph_nodes (via graph_edges)
- Graph nodes are extracted from cards; cards come from basket_items

---

## 4. Complete Task List

| # | Task Title | Description | Priority | Est. Time | Dependencies | Labels |
|---|---|---|---|---|---|---|
| H1 | Define graph node + edge schema | Document node/edge fields, relationship types, merge rules. | P0 | 1h | Sam's S2 | `docs`, `graph` |
| H2 | Decide extraction strategy | Choose: keyword/entity extraction via spaCy NER, LLM labeling, or KeyBERT. Document decision. | P0 | 45min | None | `research`, `graph` |
| H3 | Build concept extraction pipeline | Extract key concepts from card text as graph nodes. At least 3 nodes per card. | P1 | 3h | Liam's L3, Sunny's SU3 | `backend`, `graph` |
| H4 | Build edge creation logic | Connect nodes: co-occurrence in same card = connected. Optionally LLM-labeled relationship type. Edge types: related_to, mentions, overlaps_with. | P1 | 2.5h | H3 | `backend`, `graph` |
| H5 | Build graph generation API endpoint | POST /graph/generate — accepts basket card IDs, returns nodes + edges JSON. GET /graph?session_id=X — returns full graph. | P1 | 2h | H4, Steve's ST3 | `backend`, `graph` |
| H6 | Build lightweight merge algorithm | Find matching existing nodes (normalized lowercase label match), merge duplicates, update edge weights, add new nodes/edges. | P1 | 2h | H4 | `backend`, `graph` |
| H7 | Build node normalization function | Lowercase, stem/lemmatize, deduplicate near-identical concept labels. | P1 | 1h | H3 | `backend`, `graph` |
| H8 | Test graph quality with 3–5 sample baskets | Feed sample cards through pipeline, verify: nodes make sense, duplicates merged, edges meaningful. | P1 | 1.5h | H5 | `testing`, `graph` |
| H9 | Simplify graph density for readability | If graph is too dense, filter to top-N nodes by frequency, prune weak edges. | P1 | 1h | H8 | `backend`, `graph` |
| H10 | Work with Alex on layout/styling | Coordinate visualization: node sizes, colors, labels, edge rendering. | P1 | 1h | Alex's A3 | `frontend`, `graph` |
| H11 | Write judge explanation: "how graph grows" | Short paragraph for demo showing long-term vision. | P1 | 30min | H6 | `demo`, `docs` |
| H12 | Build graph export (JSON) | Export user's full graph as portable JSON. | P2 | 1h | H5 | `backend`, `graph`, `sharing` |

**Total estimated time: ~18.25 hours**

---

## 5. Collaboration Interfaces

### 5.1 What You Need From Others

- **From Sunny:** Cleaned text (SU3 output) — your concept extraction pipeline runs on this.
- **From Liam:** Keywords per card (L3 output) — feeds into your graph node extraction.
- **From Steve:** DB access and graph tables (ST3), graph page container (ST11).
- **From Alex:** Graph visualization component (A3) that consumes your API data.

### 5.2 What You Deliver To Others

- **To Alex:** Graph data via API (nodes + edges JSON format).
- **To Steve:** Graph endpoints for frontend routing (POST /graph/generate, GET /graph).

### 5.3 Cross-References — Tasks From Others That Touch You

| Person | Their Task | How It Affects You |
|---|---|---|
| Sam (S2) | Define canonical content_item schema | Your graph schema (H1) must align with this |
| Sam (S11) | Produce sample dataset | You can use this to test your extraction pipeline |
| Sunny (SU3) | Build text cleaning pipeline | Your H3 depends on this cleaned text output |
| Sunny (SU12) | Review keyword quality for graph readability | She coordinates with you on keyword → node quality |
| Liam (L3) | Build keyword extraction pipeline | Your H3 can use these keywords as input |
| Steve (ST3) | Create DB schema | Must include your graph_nodes and graph_edges tables |
| Steve (ST11) | Build graph page/container | Depends on your H5 endpoint being ready |
| Alex (A3) | Build knowledge graph visualization component | Depends on your H5 data format |
| Alex (A7) | Support graph visualization styling with Harry | Joint work session on readability |

---

## 6. Milestones & Timeline

| Checkpoint | Tasks | Goal |
|---|---|---|
| **Friday Night** | H1, H2 | Graph schema + extraction strategy decided |
| **Saturday Morning** | H3 | Concept extraction working on test data |
| **Saturday Afternoon** | H4, H7 | Edge creation + node normalization |
| **Saturday Evening** | H5, H6 | API endpoints + merge algorithm |
| **Sunday Morning** | H8, H9, H10 | Quality tested; density simplified; styling coordinated |
| **Sunday Afternoon** | H11, H12 (if time) | Judge explanation; export if time permits |

### Critical Path

```
H1 (schema) → H2 (strategy) → H3 (extraction) → H4 (edges) → H5 (API) → H8 (test)
                                      ↓                ↓
                                   H7 (normalize)    H6 (merge)
                                                        ↓
                                                    H9 (simplify) → H10 (styling w/ Alex)
                                                                       ↓
                                                                   H11 (demo explanation)
```

---

## 7. Your Tech Stack

| Module | Primary Choice | Alternative | Reasoning |
|---|---|---|---|
| **Concept Extraction** | spaCy (NER) + NetworkX + LLM for relationship labeling | KeyBERT + simple co-occurrence | spaCy provides fast NER, NetworkX handles graph operations in-memory. LLM calls label relationships. |
| **Keyword Extraction** | KeyBERT / YAKE + spaCy noun chunks | LLM extraction (slower) | Fast enough for hackathon, visually useful for tags. |
| **KG Visualization** | react-force-graph (2D) | Cytoscape.js; vis-network; React Flow | React-native, performant, supports zoom/pan/click with minimal config. |

### Quick-Start Install

```bash
pip install spacy networkx keybert anthropic supabase
python -m spacy download en_core_web_sm
```

---

## 8. API Endpoints You Build

### POST /graph/generate

- **Input:** Basket card IDs (array of UUIDs)
- **Process:** Retrieves cleaned text for each card → extracts concepts as nodes → creates edges from co-occurrence → merges with existing graph → stores to DB
- **Output:** JSON with `{ nodes: [...], edges: [...] }`

### GET /graph?session_id=X

- **Output:** Full accumulated graph for the session/user as nodes + edges JSON

### Expected Node JSON Shape

```json
{
  "id": "uuid",
  "label": "transformer architecture",
  "description": "A neural network architecture based on self-attention mechanisms",
  "frequency": 3,
  "first_seen": "2025-03-10T10:00:00Z",
  "last_seen": "2025-03-13T10:00:00Z",
  "is_new": true
}
```

### Expected Edge JSON Shape

```json
{
  "id": "uuid",
  "source_node_id": "uuid",
  "target_node_id": "uuid",
  "relationship": "related_to",
  "weight": 2.0
}
```

---

## 9. Where You Fit in the User Journey

Your work powers **Step 4 (partial)** and **Step 6** of the core flow:

- **Step 4 — Digest Generation:** Module 5 (Knowledge Graph) extracts concepts, creates nodes/edges, merges with history. Runs alongside Sunny's briefing generation.
- **Step 6 — Knowledge Graph Exploration:** Interactive graph shows today's additions highlighted. User can explore historical connections, zoom, pan, click-to-inspect.

### Full Journey Context

```
Step 1: Landing / Home        → (not you)
Step 2: Card Selection         → (not you)
Step 3: Basket Review          → (not you)
Step 4: Digest Generation      → ⭐ YOU: extract concepts, create graph
Step 5: Briefing Display       → (not you)
Step 6: Knowledge Graph        → ⭐ YOU: serve graph data, Alex renders
Step 7: Sharing (optional)     → H12 if time permits
```

---

## 10. Risks & Fallbacks Specific to You

| Risk | Impact | Fallback |
|---|---|---|
| Graph merge becomes too complex | You / Alex get stuck | Use normalized label matching and small graph. Graph only for current basket, no merge. |
| Concept extraction quality is poor | Graph looks meaningless | Use Liam's keyword tags directly as nodes instead of NER extraction. |
| Graph is too dense / unreadable | Demo impact weakened | Filter to top-N nodes by frequency; prune weak edges (H9). |
| Alex's visualization delayed | No visual graph for demo | Export JSON and show raw data; or use a simple static rendering. |
| spaCy NER misses domain-specific terms | AI concepts not captured | Supplement with KeyBERT or LLM-based extraction. |
| LLM relationship labeling is slow | Edge creation bottleneck | Fall back to simple co-occurrence (no labeled edges). |

---

## 11. Your Demo Moment

**Step 5 of the demo sequence:** Show the knowledge graph.

**Key narrative:** "This isn't just today's news — it becomes a map of what you're learning over time."

**Show:** Nodes/edges, clusters, concept overlap.

**Judge impact:** Strong visual "wow," future-product depth.

**Task H11:** Prepare a short paragraph explaining "how graph grows" for the judge-facing explanation.

**Sunday afternoon:** Verify graph renders correctly and coordinate with Liam on the technical explanation snippets.

---

## 12. Standup Participation

| Time | Your Focus |
|---|---|
| Friday Night 7:00 PM | Confirm schema with Sam; confirm extraction strategy (H1, H2) |
| Saturday 9:00 AM | Report on H3 progress; flag if Sunny's cleaned text isn't ready |
| Saturday 1:00 PM | Confirm edge logic working; check if Steve's DB has graph tables |
| Saturday 6:00 PM | API endpoints ready; merge algorithm status |
| Sunday 9:00 AM | Quality test results; coordinate with Alex on visualization |
| Sunday 2:00 PM | Verify graph in final demo flow; confirm explanation ready |

---

## 13. Definition of Done

Your work is **demo-ready** when:

1. Concept extraction produces 3+ meaningful nodes per card
2. Edges connect related concepts logically
3. API returns valid JSON that Alex's visualization can render
4. Graph renders in < 2 seconds
5. No duplicate/near-duplicate nodes visible
6. Judge explanation paragraph is written (H11)
7. At least one sample basket has been tested end-to-end through the graph pipeline
