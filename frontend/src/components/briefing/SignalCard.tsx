'use client';
import { BriefingSignal } from '@/types/briefing';
import { sourceThemes } from '@/lib/sourceThemes';

export default function SignalCard({ signal }: { signal: BriefingSignal }) {
  const theme = sourceThemes[signal.source];

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
        <div style={{ marginTop: 10 }}>
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
        </div>
      </div>
    </div>
  );
}
