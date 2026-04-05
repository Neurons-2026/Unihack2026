-- ============================================================
-- 10min AI Daily — Supabase Schema
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- ============================================================

-- User accounts
create table if not exists users (
  id            uuid        primary key default gen_random_uuid(),
  username      text        not null unique,
  email         text        unique,
  password_hash text        not null,
  salt          text        not null,
  created_at    timestamptz not null default now()
);
create index if not exists users_username_idx on users(username);

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
  user_id       uuid        references users(id) on delete set null,
  card_id       text        not null references cards(id) on delete cascade,
  action        text        not null check (action in ('swipe_right', 'swipe_left', 'undo')),
  dwell_time_ms int,
  created_at    timestamptz not null default now()
);
create index if not exists interactions_session_idx on interactions(session_id);
create index if not exists interactions_user_idx on interactions(user_id);

-- Saved basket items (swipe right)
create table if not exists basket_items (
  id         uuid        primary key default gen_random_uuid(),
  session_id text        not null,
  user_id    uuid        references users(id) on delete set null,
  card_id    text        not null references cards(id) on delete cascade,
  added_at   timestamptz not null default now(),
  unique (session_id, card_id)
);
create index if not exists basket_session_idx on basket_items(session_id);
create index if not exists basket_user_idx on basket_items(user_id);

-- Generated briefings
create table if not exists briefings (
  id               uuid        primary key default gen_random_uuid(),
  session_id       text        not null,
  user_id          uuid        references users(id) on delete cascade,
  content          text        not null,
  reading_time_min float,
  created_at       timestamptz not null default now()
);
create index if not exists briefings_session_idx on briefings(session_id);
create index if not exists briefings_user_idx on briefings(user_id);

-- ============================================================
-- Migrations — add user_id to pre-existing tables
-- Safe to run on a fresh DB too (column won't exist yet there either,
-- but the CREATE TABLE above already includes it — so skip these if
-- creating from scratch).  On an existing DB these are required.
-- ============================================================
do $$
begin
  if not exists (
    select 1 from information_schema.columns
    where table_name='interactions' and column_name='user_id'
  ) then
    alter table interactions
      add column user_id uuid references users(id) on delete set null;
    create index if not exists interactions_user_idx on interactions(user_id);
  end if;

  if not exists (
    select 1 from information_schema.columns
    where table_name='basket_items' and column_name='user_id'
  ) then
    alter table basket_items
      add column user_id uuid references users(id) on delete set null;
    create index if not exists basket_user_idx on basket_items(user_id);
  end if;

  if not exists (
    select 1 from information_schema.columns
    where table_name='briefings' and column_name='user_id'
  ) then
    alter table briefings
      add column user_id uuid references users(id) on delete cascade;
    create index if not exists briefings_user_idx on briefings(user_id);
  end if;

  if not exists (
    select 1 from information_schema.columns
    where table_name='graph_nodes' and column_name='user_id'
  ) then
    alter table graph_nodes
      add column user_id uuid references users(id) on delete cascade;
    alter table graph_nodes
      add column session_id text;
    create index if not exists graph_nodes_user_idx on graph_nodes(user_id);
    create index if not exists graph_nodes_session_idx on graph_nodes(session_id);
  end if;
end $$;

-- Knowledge graph nodes
create table if not exists graph_nodes (
  id          text        primary key,
  label       text        not null,
  description text,
  frequency   int         default 1,
  user_id     uuid        references users(id) on delete cascade,
  session_id  text,
  created_at  timestamptz not null default now()
);
create index if not exists graph_nodes_user_idx on graph_nodes(user_id);
create index if not exists graph_nodes_session_idx on graph_nodes(session_id);

-- Knowledge graph edges
create table if not exists graph_edges (
  id             uuid  primary key default gen_random_uuid(),
  source_node_id text  not null references graph_nodes(id) on delete cascade,
  target_node_id text  not null references graph_nodes(id) on delete cascade,
  relationship   text  default 'related_to',
  weight         float default 1.0
);
