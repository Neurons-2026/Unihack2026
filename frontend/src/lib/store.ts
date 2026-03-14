"use client";

import { create } from "zustand";
import { BasketItem, Briefing, Card } from "./types";

interface AppState {
  sessionId: string;
  basket: BasketItem[];
  cards: Card[];
  briefing: Briefing | null;
  setCards: (cards: Card[]) => void;
  addBasket: (item: BasketItem) => void;
  removeBasket: (id: string) => void;
  setBriefing: (briefing: Briefing) => void;
}

function createSessionId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `session-${Math.random().toString(36).slice(2, 10)}`;
}

export const useAppStore = create<AppState>((set) => ({
  sessionId: createSessionId(),
  basket: [],
  cards: [],
  briefing: null,
  setCards: (cards) => set({ cards }),
  addBasket: (item) => set((state) => ({ basket: [...state.basket, item] })),
  removeBasket: (id) => set((state) => ({ basket: state.basket.filter((b) => b.id !== id) })),
  setBriefing: (briefing) => set({ briefing }),
}));
