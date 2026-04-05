'use client';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useBasketStore } from '@/stores/useBasketStore';
import { useAppStore } from '@/lib/store';

export default function Header() {
  const count = useBasketStore((s) => s.items.length);
  const user = useAppStore((s) => s.user);
  const logout = useAppStore((s) => s.logout);
  const router = useRouter();

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
      <span style={{ fontSize: 15, fontWeight: 500, color: 'rgba(255,255,255,0.9)', letterSpacing: -0.2 }}>
        10min AI Daily
      </span>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {user ? (
          <button
            onClick={() => logout()}
            style={{
              fontSize: 12,
              fontWeight: 500,
              color: 'rgba(255,255,255,0.5)',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '5px 8px',
            }}
            title={`Signed in as ${user.username}`}
          >
            {user.username} · out
          </button>
        ) : (
          <button
            onClick={() => router.push('/login')}
            style={{
              fontSize: 12,
              fontWeight: 500,
              color: 'rgba(255,255,255,0.5)',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: '5px 8px',
            }}
          >
            Sign in
          </button>
        )}
        <Link
          href="/basket"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            background: 'rgba(255,255,255,0.08)',
            borderRadius: 9999,
            padding: '5px 12px',
            textDecoration: 'none',
          }}
        >
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.6)" strokeWidth="2.2" strokeLinecap="round">
            <path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z" />
            <line x1="3" y1="6" x2="21" y2="6" />
            <path d="M16 10a4 4 0 01-8 0" />
          </svg>
          <span style={{ fontSize: 12, fontWeight: 500, color: 'rgba(255,255,255,0.7)' }}>{count}/3</span>
        </Link>
      </div>
    </div>
  );
}
