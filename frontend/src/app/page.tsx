import { FeedClient } from "../components/FeedClient";
import { Card } from "../lib/types";

async function loadCards(): Promise<Card[]> {
  const apiBase = (globalThis as any).process?.env?.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
  try {
    const res = await fetch(`${apiBase}/cards?session_id=demo`, { cache: "no-store" });
    if (!res.ok) {
      throw new Error("bad status");
    }
    const data = await res.json();
    return (data as any[]).map((item) => ({
      id: item.id ?? "demo",
      card_title: item.card_title ?? item.title ?? "Untitled",
      card_summary: item.card_summary ?? item.summary ?? "",
      keywords: item.keywords ?? [],
      source: item.source ?? "unknown",
      source_url: item.source_url ?? item.url ?? "#",
      thumbnail_keyword: item.thumbnail_keyword ?? undefined,
    }));
  } catch (err) {
    return [
      {
        id: "fallback-1",
        card_title: "New model tops long-context benchmark",
        card_summary: "A lightweight transformer variant improves efficiency for 32k tokens.",
        keywords: ["transformer", "long context", "research"],
        source: "huggingface",
        source_url: "https://huggingface.co/papers",
      },
      {
        id: "fallback-2",
        card_title: "GitHub trending: eval toolkit",
        card_summary: "Open-source harness to benchmark small LLMs quickly.",
        keywords: ["github", "eval", "tooling"],
        source: "github",
        source_url: "https://github.com/trending",
      },
    ];
  }
}

export default async function HomePage() {
  const cards = await loadCards();

  return (
    <main className="space-y-8">
      <section className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">10min AI Daily</p>
        <h1 className="text-3xl font-bold leading-tight text-slate-900">Swipe today’s AI drops</h1>
        <p className="max-w-2xl text-sm text-slate-600">Swipe cards, cap your basket, auto-generate a 10-minute briefing, and visualize your knowledge graph.</p>
      </section>
      <FeedClient initialCards={cards} />
    </main>
  );
}
