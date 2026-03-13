"use client";

import Link from "next/link";

interface BasketBarProps {
  count: number;
  limit: number;
}

export function BasketBar({ count, limit }: BasketBarProps) {
  return (
    <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
      <div className="flex items-center gap-2 text-sm font-medium text-slate-700">
        <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-blue-600 text-xs font-semibold text-white">
          {count}
        </span>
        <span>
          Basket ({count}/{limit})
        </span>
      </div>
      <Link
        href="/basket"
        className="rounded-xl bg-slate-900 px-3 py-2 text-sm font-semibold text-white transition hover:bg-slate-800"
      >
        Review
      </Link>
    </div>
  );
}
