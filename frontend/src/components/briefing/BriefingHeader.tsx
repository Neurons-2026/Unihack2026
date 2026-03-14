'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function BriefingHeader({
  readingTimeMin,
  scrollProgress,
}: {
  readingTimeMin: number;
  scrollProgress: number;
}) {
  const router = useRouter();
  const [copied, setCopied] = useState(false);

  async function shareBriefing() {
    const title = '10min AI Daily — Today\'s Briefing';
    const url = typeof window !== 'undefined' ? window.location.href : '';
    if (navigator.share) {
      try { await navigator.share({ title, text: title, url }); } catch {}
    } else {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  }

  return (
    <div
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 20,
        background: 'linear-gradient(to bottom, #111111 0%, #111111 70%, transparent 100%)',
        padding: '48px 20px 20px',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 12,
        }}
      >
        <button
          onClick={() => router.push('/')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 7,
            padding: '6px 14px 6px 10px',
            borderRadius: 20,
            border: '1px solid rgba(255,255,255,0.1)',
            background: 'rgba(255,255,255,0.06)',
            color: 'rgba(255,255,255,0.5)',
            cursor: 'pointer',
            transition: 'background 0.15s ease, color 0.15s ease',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.12)'; e.currentTarget.style.color = 'rgba(255,255,255,0.7)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.06)'; e.currentTarget.style.color = 'rgba(255,255,255,0.5)'; }}
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          >
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          <span style={{ fontSize: 12, fontWeight: 500 }}>Back</span>
        </button>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)' }}>
            {readingTimeMin} min read
          </span>
          <button
            onClick={shareBriefing}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 28,
              height: 28,
              borderRadius: '50%',
              border: 'none',
              background: 'rgba(255,255,255,0.06)',
              color: copied ? 'rgba(130,210,160,0.8)' : 'rgba(255,255,255,0.35)',
              cursor: 'pointer',
              transition: 'color 0.2s ease',
            }}
          >
            {copied ? (
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            ) : (
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 12v8a2 2 0 002 2h12a2 2 0 002-2v-8" />
                <polyline points="16 6 12 2 8 6" />
                <line x1="12" y1="2" x2="12" y2="15" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Scroll progress bar */}
      <div
        style={{
          height: 2,
          background: 'rgba(255,255,255,0.06)',
          borderRadius: 1,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            height: 2,
            width: `${scrollProgress}%`,
            background: 'rgba(255,255,255,0.4)',
            borderRadius: 1,
            transition: 'width 0.1s ease-out',
          }}
        />
      </div>
    </div>
  );
}
