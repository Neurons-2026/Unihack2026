'use client';

type Dir = 'left' | 'right' | 'up' | 'down';

interface Props {
  direction: Dir | null;
  intensity: number;
}

const SaveIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
  </svg>
);

const SkipIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18" />
    <line x1="6" y1="6" x2="18" y2="18" />
  </svg>
);

export default function SwipeIndicator({ direction, intensity }: Props) {
  if (!direction || intensity < 0.1) return null;

  const isSave = direction === 'right' || direction === 'up';
  const isVertical = direction === 'up' || direction === 'down';
  const progress = Math.min(Math.max((intensity - 0.1) / 0.5, 0), 1);
  const committed = intensity > 0.46;
  const accent = isSave ? '180,230,200' : '230,170,170';
  const pillScale = 0.85 + progress * 0.15;

  const posStyle: React.CSSProperties = isVertical
    ? {
        top: isSave ? 18 : undefined,
        bottom: isSave ? undefined : 18,
        left: '50%',
        transform: `translateX(-50%) scale(${pillScale})`,
        transformOrigin: isSave ? 'top center' : 'bottom center',
      }
    : {
        top: 18,
        left: isSave ? undefined : 18,
        right: isSave ? 18 : undefined,
        transform: `scale(${pillScale})`,
        transformOrigin: isSave ? 'top right' : 'top left',
      };

  return (
    <div
      style={{
        position: 'absolute',
        display: 'flex',
        alignItems: 'center',
        gap: 7,
        padding: '8px 16px',
        borderRadius: 40,
        pointerEvents: 'none',
        zIndex: 20,
        opacity: 0.15 + progress * 0.85,
        background: `rgba(0,0,0,0.35)`,
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        border: `1.5px solid rgba(${accent},${committed ? 0.55 : 0.2})`,
        color: `rgba(${accent},1)`,
        fontSize: 13,
        fontWeight: 700,
        letterSpacing: 1.2,
        boxShadow: committed
          ? `0 0 18px rgba(${accent},0.2), 0 4px 12px rgba(0,0,0,0.35)`
          : `0 4px 12px rgba(0,0,0,0.25)`,
        transition: 'box-shadow 0.15s ease, border-color 0.15s ease',
        ...posStyle,
      }}
    >
      {isSave ? <SaveIcon /> : <SkipIcon />}
      <span>{isSave ? 'SAVE' : 'SKIP'}</span>
    </div>
  );
}
