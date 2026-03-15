import { BasketItem, Briefing, Card, GraphEdge, GraphNode, Interaction } from "./types";

const API_BASE = (globalThis as any).process?.env?.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function http<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Request failed: ${res.status}`);
  }
  return res.json();
}

export async function getCards(sessionId: string): Promise<Card[]> {
  return http<Card[]>(`/cards?session_id=${encodeURIComponent(sessionId)}`);
}

export async function postInteraction(payload: Interaction): Promise<{ status: string }> {
  return http<{ status: string }>(`/interactions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getBasket(sessionId: string): Promise<BasketItem[]> {
  return http<BasketItem[]>(`/basket?session_id=${encodeURIComponent(sessionId)}`);
}

export async function addToBasket(sessionId: string, cardId: string): Promise<BasketItem> {
  return http<BasketItem>(`/basket`, {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, card_id: cardId }),
  });
}

export async function generateBriefing(sessionId: string, cardIds: string[]): Promise<Briefing> {
  return http<Briefing>(`/briefing/generate`, {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, card_ids: cardIds }),
  });
}

export async function getGraph(sessionId: string): Promise<{ nodes: GraphNode[]; edges: GraphEdge[] }> {
  return http<{ nodes: GraphNode[]; edges: GraphEdge[] }>(`/graph?session_id=${encodeURIComponent(sessionId)}`);
}


export async function generateGraphFromCards(cardIds: string[], sessionId: string): Promise<{ nodes: GraphNode[]; edges: GraphEdge[] }> {
  return http<{ nodes: GraphNode[]; edges: GraphEdge[] }>(
    `/graph/generate?session_id=${encodeURIComponent(sessionId)}`,
    { method: "POST", body: JSON.stringify(cardIds) }
  );
}
