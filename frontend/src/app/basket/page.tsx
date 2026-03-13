"use client";

import Link from "next/link";
import { useAppStore } from "../../lib/store";

export default function BasketPage() {
  const { basket, cards } = useAppStore();

  const cardsMap = new Map(cards.map((c) => [c.id, c]));

  return (
    <main className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Basket</p>
          <h1 className="text-2xl font-bold text-slate-900">Your picks</h1>
        </div>
        <Link href="/" className="text-sm font-semibold text-blue-700 underline">
          Back to feed
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {basket.map((item) => {
          const card = cardsMap.get(item.card_id);
          return (
            <article key={item.id} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">{card?.source ?? "card"}</p>
              <h2 className="text-lg font-semibold">{card?.card_title ?? "Card"}</h2>
              <p className="text-sm text-slate-600">{card?.card_summary ?? ""}</p>
            </article>
          );
        })}
      </div>

      {!basket.length && <p className="text-sm text-slate-600">No items yet. Add cards from the feed.</p>}
    </main>
  );
}
