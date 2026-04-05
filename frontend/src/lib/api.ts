import { BasketItem, Briefing, Card, GraphEdge, GraphNode, Interaction } from "./types";
import { StoredUser } from "./session";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

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

export async function getCardImages(cardIds: string[]): Promise<Record<string, string>> {
  return http<Record<string, string>>(`/cards/images`, {
    method: "POST",
    body: JSON.stringify(cardIds),
  });
}

export async function generateBriefing(sessionId: string, cardIds: string[]): Promise<Briefing> {
  return http<Briefing>(`/briefing/generate`, {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, card_ids: cardIds }),
  });
}

export async function generateBriefingStream(
  sessionId: string,
  cardIds: string[],
  onChunk: (text: string) => void,
): Promise<void> {
  const res = await fetch(`${API_BASE}/briefing/generate/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, card_ids: cardIds }),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  const reader = res.body?.getReader();
  if (!reader) throw new Error("No response body");
  const decoder = new TextDecoder();
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    onChunk(decoder.decode(value, { stream: true }));
  }
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

export async function registerUser(username: string, password: string, email?: string): Promise<StoredUser> {
  const data = await http<{ user_id: string; username: string }>(`/auth/register`, {
    method: "POST",
    body: JSON.stringify({ username, password, email }),
  });
  return { userId: data.user_id, username: data.username };
}

export async function loginUser(username: string, password: string): Promise<StoredUser> {
  const data = await http<{ user_id: string; username: string }>(`/auth/login`, {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  return { userId: data.user_id, username: data.username };
}
