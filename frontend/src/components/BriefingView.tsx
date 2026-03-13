"use client";

import { Briefing } from "../lib/types";

interface BriefingViewProps {
  briefing: Briefing | null;
}

export function BriefingView({ briefing }: BriefingViewProps) {
  if (!briefing) {
    return <p className="text-sm text-slate-600">Generate a briefing to see it here.</p>;
  }

  return (
    <article className="prose prose-slate max-w-none rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">10-minute briefing</p>
      <div className="text-sm text-slate-700 whitespace-pre-line">{briefing.content}</div>
    </article>
  );
}
