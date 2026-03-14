'use client';
import { useState, useEffect, useRef, ReactNode } from 'react';
import { useBasketStore } from '@/stores/useBasketStore';
import { generateBriefing } from '@/lib/api';
import { getSessionId } from '@/lib/session';
import { Briefing } from '@/lib/types';
import BriefingHeader from './BriefingHeader';
import GraphButton from './GraphButton';

// Minimal markdown renderer — handles the backend's output format
function renderMarkdown(md: string): ReactNode[] {
  const lines = md.split('\n');
  const nodes: ReactNode[] = [];
  let key = 0;

  function renderInline(text: string): ReactNode {
    const parts: ReactNode[] = [];
    const regex = /\*\*(.*?)\*\*|\*(.*?)\*|\[([^\]]+)\]\(([^)]+)\)/g;
    let last = 0;
    let m: RegExpExecArray | null;
    while ((m = regex.exec(text)) !== null) {
      if (m.index > last) parts.push(text.slice(last, m.index));
      if (m[1] !== undefined) {
        parts.push(<strong key={key++}>{m[1]}</strong>);
      } else if (m[2] !== undefined) {
        parts.push(<em key={key++}>{m[2]}</em>);
      } else if (m[3] !== undefined) {
        parts.push(
          <a key={key++} href={m[4]} target="_blank" rel="noopener noreferrer"
            style={{ color: 'rgba(130,210,160,0.9)', textDecoration: 'none' }}>
            {m[3]}
          </a>
        );
      }
      last = regex.lastIndex;
    }
    if (last < text.length) parts.push(text.slice(last));
    return parts.length === 1 ? parts[0] : parts;
  }

  for (const line of lines) {
    if (line.startsWith('# ')) {
      nodes.push(
        <h1 key={key++} style={{ fontSize: 22, fontWeight: 500, color: '#fff', lineHeight: 1.25,
          letterSpacing: -0.6, margin: '24px 0 6px', fontFamily: 'Georgia, serif' }}>
          {renderInline(line.slice(2))}
        </h1>
      );
    } else if (line.startsWith('## ')) {
      nodes.push(
        <h2 key={key++} style={{ fontSize: 13, fontWeight: 600, color: 'rgba(255,255,255,0.5)',
          letterSpacing: 0.6, margin: '28px 0 10px', textTransform: 'uppercase' }}>
          {renderInline(line.slice(3))}
        </h2>
      );
    } else if (line.startsWith('### ')) {
      nodes.push(
        <h3 key={key++} style={{ fontSize: 17, fontWeight: 600, color: '#fff',
          margin: '20px 0 4px', letterSpacing: -0.3 }}>
          {renderInline(line.slice(4))}
        </h3>
      );
    } else if (line.startsWith('---')) {
      nodes.push(
        <hr key={key++} style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.08)',
          margin: '24px 0' }} />
      );
    } else if (line.startsWith('- ') || line.startsWith('* ')) {
      nodes.push(
        <p key={key++} style={{ fontSize: 14, color: 'rgba(255,255,255,0.6)', lineHeight: 1.65,
          margin: '4px 0', paddingLeft: 14, position: 'relative' }}>
          <span style={{ position: 'absolute', left: 0, color: 'rgba(130,210,160,0.7)' }}>•</span>
          {renderInline(line.slice(2))}
        </p>
      );
    } else if (line.trim() === '') {
      nodes.push(<div key={key++} style={{ height: 8 }} />);
    } else {
      nodes.push(
        <p key={key++} style={{ fontSize: 14, color: 'rgba(255,255,255,0.58)', lineHeight: 1.75,
          margin: '4px 0' }}>
          {renderInline(line)}
        </p>
      );
    }
  }

  return nodes;
}

export default function BriefingPage() {
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scrollProgress, setScrollProgress] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);
  const items = useBasketStore((s) => s.items);

  useEffect(() => {
    const sessionId = getSessionId();
    generateBriefing(sessionId, items)
      .then(setBriefing)
      .catch(() => setError('Failed to generate briefing. Please try again.'))
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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

  const readingTimeMin = briefing?.reading_time_min ?? 10;

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
      <BriefingHeader readingTimeMin={readingTimeMin} scrollProgress={scrollProgress} />

      <div
        ref={scrollRef}
        style={{ flex: 1, overflowY: 'auto', padding: '0 20px 40px' }}
        className="hide-scrollbar"
      >
        {loading && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center',
            justifyContent: 'center', height: '60%', gap: 12 }}>
            <div style={{ color: 'rgba(255,255,255,0.3)', fontSize: 14 }}>
              Generating your briefing…
            </div>
            <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.18)' }}>
              This may take a moment
            </div>
          </div>
        )}

        {error && (
          <div style={{ color: 'rgba(248,113,113,0.8)', fontSize: 14, marginTop: 40,
            textAlign: 'center' }}>
            {error}
          </div>
        )}

        {briefing && (
          <>
            <div style={{ paddingTop: 8 }}>
              {renderMarkdown(briefing.content)}
            </div>
            <div style={{ marginTop: 32 }}>
              <GraphButton />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
