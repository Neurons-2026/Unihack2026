export interface Card {
  id: string;
  card_title: string;
  card_summary: string;
  keywords: string[];
  source: string;
  source_url: string;
  thumbnail_keyword?: string;
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
}

export interface GraphNode {
  id: string;
  label: string;
  frequency?: number;
}

export interface GraphEdge {
  id: string;
  source_node_id: string;
  target_node_id: string;
  relationship?: string;
  weight?: number;
}
