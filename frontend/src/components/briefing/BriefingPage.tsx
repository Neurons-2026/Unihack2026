'use client';
import { useState, useEffect, useRef } from 'react';
import { sampleBriefing } from '@/data/sampleBriefing';
import { BriefingData, BriefingSignal } from '@/types/briefing';
import { CardData } from '@/types/card';
import { useBasketStore } from '@/stores/useBasketStore';
import { getTagStyle } from '@/lib/tagColors';
import BriefingHeader from './BriefingHeader';
import HeroImage from './HeroImage';
import SectionBar from './SectionBar';
import SignalCard from './SignalCard';
import InlineVisual from './InlineVisual';
import TrendItem from './TrendItem';
import TakeawayItem from './TakeawayItem';
import GraphButton from './GraphButton';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function buildBriefingFromCards(cards: CardData[]): BriefingData {
  const signals: BriefingSignal[] = cards.map((c, i) => ({
    id: `s${i + 1}`,
    source: c.source,
    title: c.title,
    summary: c.description,
    sourceUrl: c.sourceUrl,
    imageUrl: c.briefingImageUrl || c.imageUrl,
  }));

  const topicSet = new Set<string>();
  cards.forEach((c) => c.keywords.slice(0, 2).forEach((k) => topicSet.add(k)));

  return {
    id: `briefing-${Date.now()}`,
    generatedAt: new Date().toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    }),
    readingTimeMin: Math.max(5, cards.length * 2),
    headlineTitle: cards.length > 0 ? cards[0].title : 'Your AI Briefing',
    topicTags: Array.from(topicSet).slice(0, 3),
    heroImageUrl: cards.length > 0 ? (cards[0].briefingImageUrl || cards[0].imageUrl) : '',
    overview: cards
      .map((c) => c.description)
      .join(' ')
      .slice(0, 400) + '...',
    signals,
    whyItMatters:
      'These signals represent the latest developments across the AI landscape. ' +
      'Together they paint a picture of rapid progress in open-source tooling, ' +
      'model capabilities, and enterprise adoption.',
    inlineVisualUrl: cards.length > 1 ? (cards[1].briefingImageUrl || cards[1].imageUrl) : '',
    inlineVisualCaption: 'AI landscape trends',
    trends: cards.slice(0, 3).map((c) => c.title),
    takeaways: cards.slice(0, 3).map((c) => c.description.slice(0, 120)),
  };
}

export default function BriefingPage() {
  const [scrollProgress, setScrollProgress] = useState(0);
  const [briefing, setBriefing] = useState<BriefingData | null>(null);
  const [loading, setLoading] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const savedIds = useBasketStore((s) => s.items);

  // Fetch cards from API and build briefing from saved cards
  useEffect(() => {
    fetch(`${API_BASE}/api/v1/cards/feed`)
      .then((res) => res.json())
      .then((data: CardData[]) => {
        if (!data || data.length === 0) return;

        // Filter to saved cards if we have saved IDs, otherwise use all
        let selected = data;
        if (savedIds.length > 0) {
          const saved = data.filter((c) => savedIds.includes(c.id));
          if (saved.length > 0) selected = saved;
        }

        const validCards = selected.filter((c) => c.imageUrl && c.title);
        if (validCards.length > 0) {
          setBriefing(buildBriefingFromCards(validCards));
        }
      })
      .catch(() => {
        setBriefing(sampleBriefing);
      })
      .finally(() => setLoading(false));
  }, [savedIds]);

  const b = briefing ?? sampleBriefing;

  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const handleScroll = () => {
      const { scrollTop, scrollHeight, clientHeight } = el;
      const progress = scrollHeight <= clientHeight ? 100 : (scrollTop / (scrollHeight - clientHeight)) * 100;
      setScrollProgress(Math.min(100, Math.round(progress)));
    };
    el.addEventListener('scroll', handleScroll, { passive: true });
    return () => el.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <div
      style={{
        maxWidth: 390,
        margin: '0 auto',
        height: '100dvh',
        background: '#111111',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <BriefingHeader readingTimeMin={b.readingTimeMin} scrollProgress={scrollProgress} />

      {loading ? (
        <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: 14 }}>Loading...</div>
        </div>
      ) : (
      <div
        ref={scrollRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: '0 20px 40px',
        }}
        className="hide-scrollbar"
      >
        {/* Topic tags */}
        <div style={{ marginBottom: 8, display: 'flex', gap: 6 }}>
          {b.topicTags.map((tag) => {
            const s = getTagStyle(tag);
            return (
              <span
                key={tag}
                style={{
                  fontSize: 11,
                  padding: '3px 8px',
                  borderRadius: 20,
                  backgroundColor: s.bg,
                  color: s.text,
                }}
              >
                {tag}
              </span>
            );
          })}
        </div>

        {/* Headline — serif font for editorial feel */}
        <h1
          style={{
            fontSize: 26,
            fontWeight: 500,
            color: '#fff',
            lineHeight: 1.2,
            letterSpacing: -0.8,
            margin: '0 0 8px',
            fontFamily: 'Georgia, serif',
          }}
        >
          {b.headlineTitle}
        </h1>
        <p style={{ fontSize: 13, color: 'rgba(255,255,255,0.3)', margin: '0 0 20px' }}>
          {b.generatedAt} · {b.signals.length} signals
        </p>

        {/* Hero image */}
        <HeroImage imageUrl={b.heroImageUrl} />

        {/* Overview paragraph */}
        <div style={{ marginBottom: 28 }}>
          <p
            style={{
              fontSize: 15,
              color: 'rgba(255,255,255,0.62)',
              lineHeight: 1.75,
              margin: 0,
            }}
          >
            {b.overview}
          </p>
        </div>

        {/* WHAT HAPPENED — signal cards with images */}
        <div style={{ marginBottom: 28 }}>
          <SectionBar label="WHAT HAPPENED" color="#3fb950" />
          {b.signals.map((signal) => (
            <SignalCard key={signal.id} signal={signal} />
          ))}
        </div>

        {/* WHY IT MATTERS — with inline visual */}
        <div style={{ marginBottom: 28 }}>
          <SectionBar label="WHY IT MATTERS" color="rgba(234,179,8,0.8)" />
          <p
            style={{
              fontSize: 15,
              color: 'rgba(255,255,255,0.58)',
              lineHeight: 1.75,
              margin: 0,
            }}
          >
            {b.whyItMatters}
          </p>
          {b.inlineVisualUrl && (
            <InlineVisual imageUrl={b.inlineVisualUrl} caption={b.inlineVisualCaption} />
          )}
        </div>

        {/* TRENDS TO WATCH */}
        <div style={{ marginBottom: 28 }}>
          <SectionBar label="TRENDS TO WATCH" color="rgba(168,85,247,0.8)" />
          {b.trends.map((trend, i) => (
            <TrendItem key={i} index={i + 1} text={trend} />
          ))}
        </div>

        {/* KEY TAKEAWAYS */}
        <div
          style={{
            background: '#1c1c1e',
            borderRadius: 14,
            padding: 16,
            marginBottom: 28,
          }}
        >
          <span
            style={{
              fontSize: 12,
              fontWeight: 500,
              color: 'rgba(255,255,255,0.4)',
              letterSpacing: 0.5,
              display: 'block',
              marginBottom: 12,
            }}
          >
            KEY TAKEAWAYS
          </span>
          {b.takeaways.map((t, i) => (
            <TakeawayItem key={i} text={t} />
          ))}
        </div>

        {/* Knowledge graph button */}
        <GraphButton />
      </div>
      )}
    </div>
  );
}
