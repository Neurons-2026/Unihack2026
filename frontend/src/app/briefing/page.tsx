"use client";

import { useState } from "react";
import Link from "next/link";
import { BriefingView } from "../../components/BriefingView";
import { addToBasket, generateBriefing } from "../../lib/api";
import { useAppStore } from "../../lib/store";
import { Briefing } from "../../lib/types";

export default function BriefingPage() {
  const { sessionId, basket } = useAppStore();
  const [loading, setLoading] = useState(false);
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    setLoading(true);
    setError(null);
    try {
      const ids = basket.map((b) => b.card_id);
      const result = await generateBriefing(sessionId, ids);
      setBriefing(result);
    } catch (err) {
      setError("Failed to generate briefing");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Briefing</p>
          <h1 className="text-2xl font-bold text-slate-900">10-minute digest</h1>
        </div>
        <Link href="/" className="text-sm font-semibold text-blue-700 underline">
          Back to feed
        </Link>
      </div>

      <button
        className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:opacity-50"
        onClick={handleGenerate}
        disabled={loading || !basket.length}
      >
        {loading ? "Generating..." : "Generate briefing"}
      </button>

      {error && <p className="text-xs text-red-600">{error}</p>}

      <BriefingView briefing={briefing} />
    </main>
  );
}
