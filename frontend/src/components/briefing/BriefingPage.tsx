'use client';
import { useState, useEffect, useRef, ReactNode } from 'react';
import { useBasketStore } from '@/stores/useBasketStore';
import { generateBriefingStream, getCardImages } from '@/lib/api';
import { getSessionId } from '@/lib/session';
import BriefingHeader from './BriefingHeader';
import GraphButton from './GraphButton';


function preloadImages(urls: string[]): Promise<void> {
  if (urls.length === 0) return Promise.resolve();
  return Promise.all(
    urls.map(
      (url) =>
        new Promise<void>((resolve) => {
          const img = new Image();
          img.onload = () => resolve();
          img.onerror = () => resolve(); // don't block on failure
          img.src = url;
        }),
    ),
  ).then(() => {});
}

// Minimal markdown renderer — handles the backend's output format
function renderMarkdown(md: string, imageUrls: string[] = []): ReactNode[] {
  const lines = md.split('\n');
  const nodes: ReactNode[] = [];
  let key = 0;
  let h3Index = 0;

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
      // Insert landscape image before each card section
      const imgUrl = imageUrls[h3Index];
      if (imgUrl) {
        nodes.push(
          <div key={key++} style={{ borderRadius: 14, overflow: 'hidden', margin: '16px 0 12px' }}>
            <img
              src={imgUrl}
              alt=""
              style={{ width: '100%', height: 180, objectFit: 'cover', display: 'block' }}
            />
          </div>
        );
      }
      h3Index++;
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
  const [streamedContent, setStreamedContent] = useState('');
  const [done, setDone] = useState(false);
  const [cardImages, setCardImages] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scrollProgress, setScrollProgress] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);
  const chunkQueueRef = useRef('');
  const streamFinishedRef = useRef(false);
  const flushTimerRef = useRef<number | null>(null);
  const items = useBasketStore((s) => s.items);

  useEffect(() => {
    const sessionId = getSessionId();
    let cancelled = false;

    const startFlushLoop = () => {
      if (flushTimerRef.current !== null) return;
      flushTimerRef.current = window.setInterval(() => {
        if (cancelled) return;

        const queued = chunkQueueRef.current;
        if (queued.length > 0) {
          const take = Math.min(queued.length, 2);
          const next = queued.slice(0, take);
          chunkQueueRef.current = queued.slice(take);
          setLoading(false);
          setStreamedContent((prev) => prev + next);
          return;
        }

        if (streamFinishedRef.current) {
          setDone(true);
          setLoading(false);
          if (flushTimerRef.current !== null) {
            window.clearInterval(flushTimerRef.current);
            flushTimerRef.current = null;
          }
        }
      }, 45);
    };

    startFlushLoop();

    // Fetch images in parallel
    getCardImages(items)
      .then((imageMap) => {
        const ordered = items.map((id) => imageMap[id] ?? '').filter(Boolean);
        return preloadImages(ordered).then(() => ordered);
      })
      .then((imgs) => { if (!cancelled) setCardImages(imgs); })
      .catch(() => {});

    // Stream briefing content
    generateBriefingStream(sessionId, items, (chunk) => {
      if (cancelled) return;
      chunkQueueRef.current += chunk;
    })
      .then(() => {
        if (!cancelled) {
          streamFinishedRef.current = true;
        }
      })
      .catch(() => {
        if (!cancelled) {
          setError('Failed to generate briefing. Please try again.');
          setLoading(false);
          if (flushTimerRef.current !== null) {
            window.clearInterval(flushTimerRef.current);
            flushTimerRef.current = null;
          }
        }
      });

    return () => {
      cancelled = true;
      if (flushTimerRef.current !== null) {
        window.clearInterval(flushTimerRef.current);
        flushTimerRef.current = null;
      }
    };
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

  // Auto-scroll to bottom while streaming
  useEffect(() => {
    if (done) return;
    const el = scrollRef.current;
    if (!el) return;
    const { scrollTop, scrollHeight, clientHeight } = el;
    const distFromBottom = scrollHeight - clientHeight - scrollTop;
    // Only auto-scroll if user is near the bottom (within 120px)
    if (distFromBottom < 120) {
      el.scrollTop = scrollHeight;
    }
  }, [streamedContent, done]);

  const readingTimeMin = done ? Math.round(streamedContent.split(/\s+/).length / 200) : undefined;

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
      <style>{`
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
        .stream-cursor {
          display: inline-block; width: 2px; height: 0.85em;
          background: rgba(130,210,160,0.85); margin-left: 2px;
          vertical-align: text-bottom; animation: blink 0.6s step-start infinite;
        }
      `}</style>
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

        {streamedContent && (
          <>
            <div style={{ paddingTop: 8 }}>
              {renderMarkdown(streamedContent, cardImages)}
              {!done && <span className="stream-cursor" />}
            </div>
            {done && (
              <div style={{ marginTop: 32 }}>
                <GraphButton />
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
