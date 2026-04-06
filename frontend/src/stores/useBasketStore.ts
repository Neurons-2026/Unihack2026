import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { CardData } from '@/types/card';

interface BasketState {
  items: string[];
  cards: CardData[];
  interactions: { cardId: string; action: 'save' | 'skip'; time: Date }[];
  topicTaps: Record<string, number>;
  keywordScores: Record<string, number>;
  addItem: (card: CardData) => void;
  removeItem: (id: string) => void;
  logInteraction: (id: string, action: 'save' | 'skip', keywords?: string[], dwellMs?: number) => void;
  logTopicTap: (topic: string) => void;
  reset: () => void;
}

export const useBasketStore = create<BasketState>()(
  persist(
    (set, get) => ({
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
      logInteraction: (id, action, keywords = [], dwellMs = 0) =>
        set((s) => {
          // Save = strong positive signal; skip with long dwell = mild positive; skip = small negative
          let delta: number;
          if (action === 'save') {
            delta = 2;
          } else if (dwellMs > 8000) {
            delta = 0.3; // lingered on it before skipping
          } else {
            delta = -0.5;
          }

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
    }),
    {
      name: 'basket-v1',
      // Only persist the preference signals — not the ephemeral session basket
      partialize: (state) => ({
        keywordScores: state.keywordScores,
        topicTaps: state.topicTaps,
      }),
    },
  ),
);
