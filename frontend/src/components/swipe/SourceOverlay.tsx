'use client';
import { sourceThemes, SourceType } from '@/lib/sourceThemes';
import LogoIcon from './LogoIcon';

export default function SourceOverlay({ source, date }: { source: SourceType; date: string }) {
  const theme = sourceThemes[source] ?? { dotColor: '#888888', label: source, fallbackBg: '#1c1c1e' };
  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: 48,
        background: 'linear-gradient(to bottom, rgba(0,0,0,0.55) 0%, rgba(0,0,0,0) 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 18px',
        zIndex: 5,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <div
          style={{
            width: 6,
            height: 6,
            borderRadius: '50%',
            backgroundColor: theme.dotColor,
          }}
        />
        <LogoIcon source={source} size={16} />
        <span style={{ fontSize: 12, fontWeight: 500, color: 'rgba(255,255,255,0.8)' }}>
          {theme.label}
        </span>
      </div>
      <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.45)' }}>{date}</span>
    </div>
  );
}
