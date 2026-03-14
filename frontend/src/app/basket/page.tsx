'use client';
import Link from 'next/link';
import { useBasketStore } from '@/stores/useBasketStore';
import { sourceThemes, SourceType } from '@/lib/sourceThemes';

export default function BasketPage() {
  const items = useBasketStore((s) => s.items);
  const savedCards = useBasketStore((s) => s.cards);
  const removeItem = useBasketStore((s) => s.removeItem);

  return (
    <div
      style={{
        maxWidth: 390,
        margin: '0 auto',
        height: '100dvh',
        background: '#111111',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <div style={{ padding: '52px 20px 0', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
          <Link
            href="/"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 7,
              padding: '6px 14px 6px 10px',
              borderRadius: 20,
              border: '1px solid rgba(255,255,255,0.1)',
              background: 'rgba(255,255,255,0.06)',
              color: 'rgba(255,255,255,0.5)',
              textDecoration: 'none',
              fontSize: 12,
              fontWeight: 500,
              transition: 'background 0.15s ease, color 0.15s ease',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.12)'; e.currentTarget.style.color = 'rgba(255,255,255,0.7)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.06)'; e.currentTarget.style.color = 'rgba(255,255,255,0.5)'; }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="15 18 9 12 15 6" />
            </svg>
            Back
          </Link>
          <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.35)', fontWeight: 500 }}>
            {items.length}/5 saved
          </span>
        </div>

        <div style={{ marginBottom: 6 }}>
          <span style={{ fontSize: 22, fontWeight: 600, color: '#fff', letterSpacing: -0.5 }}>
            Your Basket
          </span>
        </div>
        <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.35)', marginBottom: 20, lineHeight: 1.5 }}>
          Cards you&apos;ve saved. Remove any you don&apos;t need.
        </div>
      </div>

      {/* Card list */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '0 20px 32px' }}>
        {savedCards.length === 0 ? (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              gap: 12,
            }}
          >
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.15)" strokeWidth="1.5" strokeLinecap="round">
              <path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z" />
              <line x1="3" y1="6" x2="21" y2="6" />
              <path d="M16 10a4 4 0 01-8 0" />
            </svg>
            <span style={{ fontSize: 14, color: 'rgba(255,255,255,0.3)' }}>No cards saved yet</span>
            <Link
              href="/"
              style={{
                marginTop: 8,
                fontSize: 13,
                color: 'rgba(130,210,160,0.8)',
                textDecoration: 'none',
                fontWeight: 500,
              }}
            >
              Start swiping
            </Link>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {savedCards.map((card) => {
              if (!card) return null;
              const theme = sourceThemes[card.source as SourceType];
              return (
                <div
                  key={card.id}
                  style={{
                    display: 'flex',
                    gap: 14,
                    padding: 14,
                    borderRadius: 14,
                    background: 'rgba(255,255,255,0.04)',
                    border: '1px solid rgba(255,255,255,0.06)',
                  }}
                >
                  {/* Thumbnail */}
                  <div
                    style={{
                      width: 72,
                      height: 72,
                      borderRadius: 10,
                      overflow: 'hidden',
                      flexShrink: 0,
                      background: theme.fallbackBg,
                    }}
                  >
                    {card.imageUrl && (
                      <img
                        src={card.imageUrl}
                        alt=""
                        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                      />
                    )}
                  </div>

                  {/* Info */}
                  <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                      <div style={{ width: 6, height: 6, borderRadius: '50%', background: theme.dotColor, flexShrink: 0 }} />
                      <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.35)', fontWeight: 500, letterSpacing: 0.3 }}>
                        {theme.label}
                      </span>
                    </div>
                    <div
                      style={{
                        fontSize: 14,
                        fontWeight: 500,
                        color: '#fff',
                        lineHeight: 1.3,
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical' as const,
                        overflow: 'hidden',
                      }}
                    >
                      {card.title}
                    </div>
                    <div
                      style={{
                        fontSize: 11,
                        color: 'rgba(255,255,255,0.3)',
                        marginTop: 4,
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      {card.description}
                    </div>
                  </div>

                  {/* Remove button */}
                  <button
                    onClick={() => removeItem(card.id)}
                    style={{
                      alignSelf: 'center',
                      flexShrink: 0,
                      width: 32,
                      height: 32,
                      borderRadius: '50%',
                      border: 'none',
                      background: 'rgba(248,113,113,0.1)',
                      color: 'rgba(248,113,113,0.7)',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Actions */}
      {savedCards.length > 0 && (
        <div style={{ padding: '12px 20px 32px', flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 10 }}>
          <Link
            href="/briefing"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
              width: '100%',
              padding: '14px 0',
              borderRadius: 12,
              background: 'rgba(130,210,160,0.12)',
              border: '1px solid rgba(130,210,160,0.2)',
              color: 'rgba(130,210,160,1)',
              fontSize: 14,
              fontWeight: 600,
              textDecoration: 'none',
              letterSpacing: 0.2,
            }}
          >
            Generate Briefing
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </Link>
          <Link
            href="/graph"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
              width: '100%',
              padding: '13px 0',
              borderRadius: 12,
              background: 'rgba(100,180,255,0.08)',
              border: '1px solid rgba(100,180,255,0.15)',
              color: 'rgba(100,180,255,0.9)',
              fontSize: 14,
              fontWeight: 500,
              textDecoration: 'none',
              letterSpacing: 0.2,
            }}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="4" />
              <line x1="4.93" y1="4.93" x2="9.17" y2="9.17" /><line x1="14.83" y1="14.83" x2="19.07" y2="19.07" />
              <line x1="14.83" y1="9.17" x2="19.07" y2="4.93" /><line x1="4.93" y1="19.07" x2="9.17" y2="14.83" />
            </svg>
            Explore Knowledge Graph
          </Link>
        </div>
      )}
    </div>
  );
}
