export interface Card {
  id: string;
  card_title: string;
  card_summary: string;
  why_it_matters?: string;
  keywords: string[];
  source: string;
  source_url: string;
  thumbnail_keyword?: string;
  image_url?: string;
  published_at?: string;
  metadata?: {
    stars?: number;
    forks?: number;
    language?: string;
    likes?: number;
    citations?: number;
    reading_time?: number;
  };
}

export interface Interaction {
  session_id: string;
  card_id: string;
  action: "swipe_right" | "swipe_left" | "undo";
  dwell_time_ms?: number;
}

export interface BasketItem {
  id: string;
  session_id: string;
  card_id: string;
  added_at?: string;
}

export interface Briefing {
  id: string;
  content: string;
  reading_time_min?: number;
  card_images?: Record<string, string>;
}

export interface GraphNode {
  id: string;
  label: string;
  description?: string;
  frequency?: number;
  is_today?: boolean;
}

export interface GraphEdge {
  id: string;
  source_node_id: string;
  target_node_id: string;
  relationship?: string;
  weight?: number;
}
