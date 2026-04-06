-- ============================================================
-- 10min AI Daily — Supabase Schema
-- Run this in: Supabase Dashboard → SQL Editor → New Query
-- Tables are ordered by dependency so this is safe to run fresh.
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

-- Content items (preprocessing output — cleaned data)
-- Must come before cards since cards.id references it.
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

-- Cards (populated by the ingest worker; id matches content_items.id)
create table if not exists cards (
  id               text        primary key references content_items(id) on delete cascade,
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

-- Original PDFs (e.g. HuggingFace papers)
create table if not exists paper_pdfs (
  id                text        primary key,
  content_item_id   text        references content_items(id) on delete cascade,
  filename          text        not null,
  pdf_data          bytea       not null,
  page_count        int,
  uploaded_at       timestamptz not null default now()
);

-- Extracted concepts (concept extraction output)
create table if not exists concepts (
  id                     uuid primary key default gen_random_uuid(),
  content_item_id        text not null references content_items(id) on delete cascade,
  label                  text not null,
  description            text,
  why_innovative         text,
  impact_on_applications text,
  category               text check (category in ('technique','architecture','application','dataset','tool','benchmark','theory')),
  relevance_score        float,
  created_at             timestamptz not null default now()
);
create index if not exists concepts_content_item_idx on concepts(content_item_id);

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
create index if not exists graph_nodes_user_idx    on graph_nodes(user_id);
create index if not exists graph_nodes_session_idx on graph_nodes(session_id);

-- Knowledge graph edges
create table if not exists graph_edges (
  id             uuid        primary key default gen_random_uuid(),
  source_node_id text        not null references graph_nodes(id) on delete cascade,
  target_node_id text        not null references graph_nodes(id) on delete cascade,
  relationship   text        default 'related_to',
  weight         float       default 1.0,
  created_at     timestamptz not null default now()
);

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
create index if not exists interactions_user_idx    on interactions(user_id);

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
create index if not exists basket_user_idx    on basket_items(user_id);

-- Generated briefings
create table if not exists briefings (
  id               uuid        primary key default gen_random_uuid(),
  session_id       text        not null,
  user_id          uuid        references users(id) on delete cascade,
  cache_key        text        not null,   -- sha1(session_id:sorted_card_ids) for dedup lookup
  card_ids         text[]      not null default '{}',
  content          text        not null,
  reading_time_min float,
  created_at       timestamptz not null default now()
);
create index if not exists briefings_session_idx   on briefings(session_id);
create index if not exists briefings_user_idx      on briefings(user_id);
create unique index if not exists briefings_cache_key_idx on briefings(cache_key);

-- Per-session swipe totals (maintained automatically via trigger).
-- user_id is populated for logged-in users so stats can be queried
-- across devices/sessions by user rather than just by session_id.
create table if not exists user_stats (
  session_id     text        primary key,
  user_id        uuid        references users(id) on delete set null,
  total_swipes   int         not null default 0,
  swipes_right   int         not null default 0,
  swipes_left    int         not null default 0,
  last_swiped_at timestamptz,
  updated_at     timestamptz not null default now()
);
create index if not exists user_stats_user_idx on user_stats(user_id);

-- Trigger: keep user_stats in sync on every interaction insert
create or replace function update_user_stats()
returns trigger language plpgsql as $$
begin
  if NEW.action in ('swipe_right', 'swipe_left') then
    insert into user_stats (session_id, user_id, total_swipes, swipes_right, swipes_left, last_swiped_at, updated_at)
    values (
      NEW.session_id,
      NEW.user_id,
      1,
      case when NEW.action = 'swipe_right' then 1 else 0 end,
      case when NEW.action = 'swipe_left'  then 1 else 0 end,
      NEW.created_at,
      now()
    )
    on conflict (session_id) do update set
      user_id        = coalesce(NEW.user_id, user_stats.user_id),
      total_swipes   = user_stats.total_swipes + 1,
      swipes_right   = user_stats.swipes_right + (case when NEW.action = 'swipe_right' then 1 else 0 end),
      swipes_left    = user_stats.swipes_left  + (case when NEW.action = 'swipe_left'  then 1 else 0 end),
      last_swiped_at = NEW.created_at,
      updated_at     = now();
  end if;
  return NEW;
end;
$$;

drop trigger if exists trg_update_user_stats on interactions;
create trigger trg_update_user_stats
  after insert on interactions
  for each row execute function update_user_stats();

-- ============================================================
-- Migrations — safe to run on an existing DB.
-- CREATE TABLE IF NOT EXISTS above handles fresh installs;
-- these ALTER TABLE blocks handle DBs created before these
-- columns were added.
-- ============================================================
do $$
begin
  -- interactions.user_id
  if not exists (
    select 1 from information_schema.columns
    where table_name='interactions' and column_name='user_id'
  ) then
    alter table interactions add column user_id uuid references users(id) on delete set null;
    create index if not exists interactions_user_idx on interactions(user_id);
  end if;

  -- basket_items.user_id
  if not exists (
    select 1 from information_schema.columns
    where table_name='basket_items' and column_name='user_id'
  ) then
    alter table basket_items add column user_id uuid references users(id) on delete set null;
    create index if not exists basket_user_idx on basket_items(user_id);
  end if;

  -- briefings.user_id
  if not exists (
    select 1 from information_schema.columns
    where table_name='briefings' and column_name='user_id'
  ) then
    alter table briefings add column user_id uuid references users(id) on delete cascade;
    create index if not exists briefings_user_idx on briefings(user_id);
  end if;

  -- briefings.cache_key
  if not exists (
    select 1 from information_schema.columns
    where table_name='briefings' and column_name='cache_key'
  ) then
    alter table briefings add column cache_key text;
    alter table briefings add column card_ids text[] not null default '{}';
    -- Back-fill existing rows with a placeholder key so the unique index can be created
    update briefings set cache_key = id::text where cache_key is null;
    alter table briefings alter column cache_key set not null;
    create unique index if not exists briefings_cache_key_idx on briefings(cache_key);
  end if;

  -- graph_nodes.user_id + session_id
  if not exists (
    select 1 from information_schema.columns
    where table_name='graph_nodes' and column_name='user_id'
  ) then
    alter table graph_nodes add column user_id uuid references users(id) on delete cascade;
    alter table graph_nodes add column session_id text;
    create index if not exists graph_nodes_user_idx    on graph_nodes(user_id);
    create index if not exists graph_nodes_session_idx on graph_nodes(session_id);
  end if;

  -- graph_edges.created_at
  if not exists (
    select 1 from information_schema.columns
    where table_name='graph_edges' and column_name='created_at'
  ) then
    alter table graph_edges add column created_at timestamptz not null default now();
  end if;

  -- user_stats.user_id
  if not exists (
    select 1 from information_schema.columns
    where table_name='user_stats' and column_name='user_id'
  ) then
    alter table user_stats add column user_id uuid references users(id) on delete set null;
    create index if not exists user_stats_user_idx on user_stats(user_id);
  end if;
end $$;
