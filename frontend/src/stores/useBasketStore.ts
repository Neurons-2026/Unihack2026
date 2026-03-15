import { create } from 'zustand';
import { CardData } from '@/types/card';

interface BasketState {
  items: string[];
  cards: CardData[];
  interactions: { cardId: string; action: 'save' | 'skip'; time: Date }[];
  topicTaps: Record<string, number>;
  keywordScores: Record<string, number>;
  addItem: (card: CardData) => void;
  removeItem: (id: string) => void;
  logInteraction: (id: string, action: 'save' | 'skip', keywords?: string[]) => void;
  logTopicTap: (topic: string) => void;
  reset: () => void;
}

export const useBasketStore = create<BasketState>((set, get) => ({
  items: [],
  cards: [],
  interactions: [],
  topicTaps: {},
  keywordScores: {},
  addItem: (card) => {
    if (get().items.length >= 3) return;
    if (get().items.includes(card.id)) return;
    set((s) => ({ items: [...s.items, card.id], cards: [...s.cards, card] }));
  },
  removeItem: (id) => set((s) => ({
    items: s.items.filter((i) => i !== id),
    cards: s.cards.filter((c) => c.id !== id),
  })),
  logInteraction: (id, action, keywords = []) =>
    set((s) => {
      const delta = action === 'save' ? 1 : -1;
      const updated = { ...s.keywordScores };
      for (const kw of keywords) {
        const key = kw.toLowerCase();
        updated[key] = (updated[key] ?? 0) + delta;
      }
      return {
        interactions: [...s.interactions, { cardId: id, action, time: new Date() }],
        keywordScores: updated,
      };
    }),
  logTopicTap: (topic) =>
    set((s) => ({ topicTaps: { ...s.topicTaps, [topic]: (s.topicTaps[topic] || 0) + 1 } })),
  reset: () => set({ items: [], cards: [], interactions: [], topicTaps: {}, keywordScores: {} }),
}));
