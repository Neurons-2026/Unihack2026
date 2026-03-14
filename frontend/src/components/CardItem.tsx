"use client";

import { Card } from "../lib/types";

type SwipeDir = "left" | "right";

interface CardItemProps {
  card: Card;
  onSwipe: (direction: SwipeDir, card: Card) => void;
}

export function CardItem({ card, onSwipe }: CardItemProps) {
  return (
    <article className="flex flex-col gap-3 rounded-2xl bg-white p-6 shadow-lg ring-1 ring-slate-200">
      <header className="flex items-start justify-between gap-2">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">{card.source}</p>
          <h2 className="text-lg font-semibold leading-tight">{card.card_title}</h2>
        </div>
        {card.thumbnail_keyword && (
          <span className="rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600">{card.thumbnail_keyword}</span>
        )}
      </header>
      <p className="text-sm text-slate-600">{card.card_summary}</p>
      <div className="flex flex-wrap gap-2">
        {card.keywords.map((kw) => (
          <span key={kw} className="rounded-full bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700">
            {kw}
          </span>
        ))}
      </div>
      <div className="mt-2 flex gap-2">
        <button
          className="flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm font-medium text-slate-700 transition hover:border-slate-300 hover:bg-slate-50"
          onClick={() => onSwipe("left", card)}
        >
          Skip
        </button>
        <button
          className="flex-1 rounded-xl bg-blue-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-blue-700"
          onClick={() => onSwipe("right", card)}
        >
          Add to Basket
        </button>
      </div>
    </article>
  );
}
