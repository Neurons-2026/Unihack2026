-- ============================================================
-- 10min AI Daily — Supabase Schema
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- ============================================================

-- Cards (populated by the ingest worker)
create table if not exists cards (
  id               text        primary key,
  card_title       text        not null,
  card_summary     text        not null,
  keywords         text[]      not null default '{}',
  source           text        not null,
  source_url       text        not null,
  thumbnail_keyword text,
  trending_score   float,
  image_url        text,
  created_at       timestamptz not null default now()
);

-- Content items (preprocessing output — cleaned data)
create table if not exists content_items (
  id                text        primary key,
  source            text        not null,
  source_url        text        not null,
  title             text        not null,
  raw_content       text,
  cleaned_text      text,
  preview_text      text,
  quality_score     float,
  quality_notes     text[]      default '{}',
  enrichment_used   boolean     default false,
  keywords          text[]      default '{}',
  pipeline_state    text        not null default 'raw_scraped'
                    check (pipeline_state in ('raw_scraped','keywords_enriched','preprocessed','card_ready')),
  fetched_at        timestamptz,
  created_at        timestamptz not null default now()
);

-- Original PDFs (e.g. HuggingFace papers)
create table if not exists paper_pdfs (
  id                text        primary key,
  content_item_id   text        references content_items(id) on delete cascade,
  filename          text        not null,
  pdf_data          bytea       not null,
  page_count        int,
  uploaded_at       timestamptz not null default now()
);

-- Extracted concepts (Harry's concept extraction output)
create table if not exists concepts (
  id                uuid        primary key default gen_random_uuid(),
  content_item_id   text        not null references content_items(id) on delete cascade,
  label             text        not null,
  description       text,
  why_innovative    text,
  impact_on_applications text,
  category          text        check (category in ('technique','architecture','application','dataset','tool','benchmark','theory')),
  relevance_score   float,
  created_at        timestamptz not null default now()
);
create index if not exists concepts_content_item_idx on concepts(content_item_id);

-- User swipe interactions
create table if not exists interactions (
  id            uuid        primary key default gen_random_uuid(),
  session_id    text        not null,
  card_id       text        not null references cards(id) on delete cascade,
  action        text        not null check (action in ('swipe_right', 'swipe_left', 'undo')),
  dwell_time_ms int,
  created_at    timestamptz not null default now()
);
create index if not exists interactions_session_idx on interactions(session_id);

-- Saved basket items (swipe right)
create table if not exists basket_items (
  id         uuid        primary key default gen_random_uuid(),
  session_id text        not null,
  card_id    text        not null references cards(id) on delete cascade,
  added_at   timestamptz not null default now(),
  unique (session_id, card_id)
);
create index if not exists basket_session_idx on basket_items(session_id);

-- Generated briefings
create table if not exists briefings (
  id               uuid        primary key default gen_random_uuid(),
  session_id       text        not null,
  content          text        not null,
  reading_time_min float,
  created_at       timestamptz not null default now()
);
create index if not exists briefings_session_idx on briefings(session_id);

-- Knowledge graph nodes
create table if not exists graph_nodes (
  id          text        primary key,
  label       text        not null,
  description text,
  frequency   int         default 1,
  created_at  timestamptz not null default now()
);

-- Knowledge graph edges
create table if not exists graph_edges (
  id             uuid  primary key default gen_random_uuid(),
  source_node_id text  not null references graph_nodes(id) on delete cascade,
  target_node_id text  not null references graph_nodes(id) on delete cascade,
  relationship   text  default 'related_to',
  weight         float default 1.0
);
