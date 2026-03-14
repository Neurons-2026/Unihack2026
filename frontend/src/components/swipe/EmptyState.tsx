'use client';
import { useRouter } from 'next/navigation';
import { useBasketStore } from '@/stores/useBasketStore';

export default function EmptyState() {
  const router = useRouter();
  const count = useBasketStore((s) => s.items.length);
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 4 }}>
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.3)" strokeWidth="1.5">
        <path d="M22 11.08V12a10 10 0 11-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" />
      </svg>
      <p style={{ fontSize: 18, fontWeight: 500, color: 'rgba(255,255,255,0.7)', marginTop: 12 }}>You're all caught up</p>
      <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.3)' }}>You've reviewed all today's signals</p>
      {count >= 1 ? (
        <button
          onClick={() => router.push('/briefing')}
          style={{
            marginTop: 24,
            padding: '12px 24px',
            background: 'rgba(255,255,255,0.9)',
            color: '#111',
            fontSize: 14,
            fontWeight: 500,
            borderRadius: 9999,
            border: 'none',
            cursor: 'pointer',
          }}
        >
          Generate my briefing →
        </button>
      ) : (
        <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.3)', marginTop: 16 }}>Come back tomorrow for fresh signals</p>
      )}
    </div>
  );
}
