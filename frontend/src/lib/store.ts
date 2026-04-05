"use client";

import { create } from "zustand";
import { BasketItem, Briefing, Card } from "./types";
import { StoredUser, getStoredUser, setStoredUser, clearStoredUser } from "./session";

interface AppState {
  sessionId: string;
  user: StoredUser | null;
  basket: BasketItem[];
  cards: Card[];
  briefing: Briefing | null;
  setCards: (cards: Card[]) => void;
  addBasket: (item: BasketItem) => void;
  removeBasket: (id: string) => void;
  setBriefing: (briefing: Briefing) => void;
  login: (user: StoredUser) => void;
  logout: () => void;
}

function createSessionId() {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `session-${Math.random().toString(36).slice(2, 10)}`;
}

export const useAppStore = create<AppState>((set) => ({
  sessionId: getStoredUser()?.userId ?? createSessionId(),
  user: getStoredUser(),
  basket: [],
  cards: [],
  briefing: null,
  setCards: (cards) => set({ cards }),
  addBasket: (item) => set((state) => ({ basket: [...state.basket, item] })),
  removeBasket: (id) => set((state) => ({ basket: state.basket.filter((b) => b.id !== id) })),
  setBriefing: (briefing) => set({ briefing }),
  login: (user) => {
    setStoredUser(user);
    set({ user, sessionId: user.userId });
  },
  logout: () => {
    clearStoredUser();
    const newSessionId = createSessionId();
    set({ user: null, sessionId: newSessionId, basket: [], briefing: null });
  },
}));
