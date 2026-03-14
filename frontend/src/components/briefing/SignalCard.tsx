'use client';
import { useState } from 'react';
import { BriefingSignal } from '@/types/briefing';
import { sourceThemes } from '@/lib/sourceThemes';

async function shareSignal(signal: BriefingSignal) {
  const text = `${signal.title}\n${signal.summary}`;
  if (navigator.share) {
    try { await navigator.share({ title: signal.title, text, url: signal.sourceUrl }); return true; } catch { return false; }
  }
  await navigator.clipboard.writeText(`${signal.title}\n${signal.sourceUrl}`);
  return true;
}

export default function SignalCard({ signal }: { signal: BriefingSignal }) {
  const theme = sourceThemes[signal.source];
  const [copied, setCopied] = useState(false);

  return (
    <div
      style={{
        background: '#1c1c1e',
        borderRadius: 14,
        overflow: 'hidden',
        marginBottom: 10,
      }}
    >
      {/* Signal image */}
      <div style={{ height: 120, position: 'relative', overflow: 'hidden' }}>
        <img
          src={signal.imageUrl}
          alt=""
          style={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: 'linear-gradient(to bottom, transparent 30%, #1c1c1e 100%)',
          }}
        />
        {/* Source badge on image */}
        <div
          style={{
            position: 'absolute',
            top: 10,
            left: 12,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          <div
            style={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              backgroundColor: theme.dotColor,
            }}
          />
          <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)' }}>
            {signal.source === 'github'
              ? 'GITHUB'
              : signal.source === 'huggingface'
                ? 'HUGGINGFACE'
                : signal.source === 'openai_blog'
                  ? 'OPENAI'
                  : 'ANTHROPIC'}
          </span>
        </div>
      </div>

      {/* Text content */}
      <div style={{ padding: '12px 16px 16px' }}>
        <div
          style={{
            fontSize: 16,
            fontWeight: 500,
            color: 'rgba(255,255,255,0.9)',
            lineHeight: 1.3,
            marginBottom: 8,
          }}
        >
          {signal.title}
        </div>
        <p
          style={{
            fontSize: 14,
            color: 'rgba(255,255,255,0.48)',
            lineHeight: 1.6,
            margin: 0,
          }}
        >
          {signal.summary}
        </p>
        <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <a
            href={signal.sourceUrl}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: 12,
              color: 'rgba(59,130,246,0.7)',
              textDecoration: 'none',
            }}
          >
            View source →
          </a>
          <button
            onClick={async () => {
              const ok = await shareSignal(signal);
              if (ok && !navigator.share) { setCopied(true); setTimeout(() => setCopied(false), 1500); }
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 5,
              padding: '5px 10px',
              borderRadius: 20,
              border: 'none',
              background: 'rgba(255,255,255,0.06)',
              color: copied ? 'rgba(130,210,160,0.8)' : 'rgba(255,255,255,0.35)',
              fontSize: 11,
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'color 0.2s ease, background 0.2s ease',
            }}
          >
            {copied ? (
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="20 6 9 17 4 12" />
              </svg>
            ) : (
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M4 12v8a2 2 0 002 2h12a2 2 0 002-2v-8" />
                <polyline points="16 6 12 2 8 6" />
                <line x1="12" y1="2" x2="12" y2="15" />
              </svg>
            )}
            {copied ? 'Copied' : 'Share'}
          </button>
        </div>
      </div>
    </div>
  );
}
