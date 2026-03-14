import { create } from 'zustand';

interface BasketState {
  items: string[];
  interactions: { cardId: string; action: 'save' | 'skip'; time: Date }[];
  topicTaps: Record<string, number>;
  addItem: (id: string) => void;
  removeItem: (id: string) => void;
  logInteraction: (id: string, action: 'save' | 'skip') => void;
  logTopicTap: (topic: string) => void;
}

export const useBasketStore = create<BasketState>((set, get) => ({
  items: [],
  interactions: [],
  topicTaps: {},
  addItem: (id) => {
    if (get().items.length >= 5) return;
    set((s) => ({ items: [...s.items, id] }));
  },
  removeItem: (id) => set((s) => ({ items: s.items.filter((i) => i !== id) })),
  logInteraction: (id, action) =>
    set((s) => ({ interactions: [...s.interactions, { cardId: id, action, time: new Date() }] })),
  logTopicTap: (topic) =>
    set((s) => ({ topicTaps: { ...s.topicTaps, [topic]: (s.topicTaps[topic] || 0) + 1 } })),
}));
