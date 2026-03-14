import { FeedClient } from "../components/FeedClient";

export default function HomePage() {
  return (
    <main className="space-y-8">
      <section className="space-y-3">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">10min AI Daily</p>
        <h1 className="text-3xl font-bold leading-tight text-slate-900">Swipe today’s AI drops</h1>
        <p className="max-w-2xl text-sm text-slate-600">Swipe cards, cap your basket, auto-generate a 10-minute briefing, and visualize your knowledge graph.</p>
      </section>
      <FeedClient initialCards={[]} />
    </main>
  );
}
