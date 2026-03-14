'use client';
import { useEffect, useState } from 'react';

interface Props {
  action: 'save' | 'skip' | null;
  trigger: number; // increment to show toast
}

export default function SwipeToast({ action, trigger }: Props) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (trigger === 0) return;
    setVisible(true);
    const timer = setTimeout(() => setVisible(false), 700);
    return () => clearTimeout(timer);
  }, [trigger]);

  if (!action) return null;

  const isSave = action === 'save';

  return (
    <div
      style={{
        position: 'absolute',
        top: '50%',
        left: '50%',
        transform: visible
          ? 'translateX(-50%) translateY(-50%) scale(1)'
          : 'translateX(-50%) translateY(-50%) scale(0.8)',
        padding: '16px 32px',
        borderRadius: 12,
        fontSize: 18,
        fontWeight: 600,
        letterSpacing: 0.3,
        whiteSpace: 'nowrap',
        pointerEvents: 'none',
        zIndex: 35,
        opacity: visible ? 1 : 0,
        transition: 'all 0.35s cubic-bezier(0.16, 1, 0.3, 1)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        background: isSave ? 'rgba(160,210,175,0.15)' : 'rgba(210,160,160,0.12)',
        color: isSave ? 'rgba(160,210,175,1)' : 'rgba(210,160,160,0.9)',
        border: isSave
          ? '1px solid rgba(160,210,175,0.2)'
          : '1px solid rgba(210,160,160,0.15)',
        boxShadow: isSave
          ? '0 8px 32px rgba(160,210,175,0.08)'
          : '0 8px 32px rgba(210,160,160,0.08)',
      }}
    >
      {isSave ? '✓ Saved' : '✕ Skipped'}
    </div>
  );
}
