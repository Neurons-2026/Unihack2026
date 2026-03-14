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
    const timer = setTimeout(() => setVisible(false), 1500);
    return () => clearTimeout(timer);
  }, [trigger]);

  if (!action) return null;

  const isSave = action === 'save';

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 20,
        left: '50%',
        transform: visible
          ? 'translateX(-50%) translateY(0)'
          : 'translateX(-50%) translateY(20px)',
        padding: '9px 24px',
        borderRadius: 30,
        fontSize: 13,
        fontWeight: 500,
        letterSpacing: 0.5,
        whiteSpace: 'nowrap',
        pointerEvents: 'none',
        zIndex: 30,
        opacity: visible ? 1 : 0,
        transition: 'all 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        background: isSave ? 'rgba(160,210,175,0.1)' : 'rgba(210,160,160,0.08)',
        color: isSave ? 'rgba(160,210,175,0.8)' : 'rgba(210,160,160,0.6)',
        border: isSave
          ? '0.5px solid rgba(160,210,175,0.12)'
          : '0.5px solid rgba(210,160,160,0.08)',
      }}
    >
      {isSave ? 'Saved' : 'Skipped'}
    </div>
  );
}
