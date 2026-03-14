const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function fetchCards() {
  const res = await fetch(`${API_BASE}/cards`, { cache: "no-store" });
  if (!res.ok) return [];
  return res.json();
}

export default async function HomePage() {
  const cards = await fetchCards();

  return (
    <main className="page">
      <section className="hero">
        <h1>10min AI Daily</h1>
        <p>Fast-track your AI updates in 10 minutes.</p>
      </section>
      <section className="cards">
        {cards.map((card: any) => (
          <article key={card.id} className="card">
            <header>
              <p className="source">{card.source}</p>
              <h2>{card.title}</h2>
            </header>
            <p className="summary">{card.summary}</p>
            <a href={card.url} target="_blank" rel="noreferrer">
              View source
            </a>
          </article>
        ))}
        {!cards.length && <p>No cards yet. Worker will populate soon.</p>}
      </section>
    </main>
  );
}
