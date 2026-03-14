'use client';
import { CardData } from '@/types/card';
import { formatCount } from '@/lib/sourceThemes';

export default function MetadataBadges({ metadata, source }: { metadata: CardData['metadata']; source: CardData['source'] }) {
  const badges: { icon?: string; label: string }[] = [];

  if (source === 'github') {
    if (metadata.stars != null) badges.push({ icon: 'star', label: formatCount(metadata.stars) });
    if (metadata.forks != null) badges.push({ icon: 'fork', label: formatCount(metadata.forks) });
    if (metadata.language) badges.push({ label: metadata.language });
  } else if (source === 'huggingface') {
    if (metadata.likes != null) badges.push({ icon: 'heart', label: formatCount(metadata.likes) });
    if (metadata.downloads != null) badges.push({ icon: 'download', label: formatCount(metadata.downloads) });
    if (metadata.taskType) badges.push({ label: metadata.taskType });
  } else {
    if (metadata.category) badges.push({ label: metadata.category });
    if (metadata.readTimeMin) badges.push({ icon: 'clock', label: `${metadata.readTimeMin}min` });
  }

  const starSvg = (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="rgba(255,255,255,0.5)">
      <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
    </svg>
  );
  const forkSvg = (
    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.5)" strokeWidth="2">
      <circle cx="12" cy="18" r="3" /><circle cx="6" cy="6" r="3" /><circle cx="18" cy="6" r="3" />
      <line x1="18" y1="9" x2="12" y2="15" /><path d="M12 15L6 9" />
    </svg>
  );

  const iconMap: Record<string, React.ReactNode> = { star: starSvg, fork: forkSvg, heart: starSvg, download: forkSvg, clock: starSvg };

  return (
    <div style={{ display: 'flex', gap: 8 }}>
      {badges.map((b, i) => (
        <div
          key={i}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 3,
            background: 'rgba(0,0,0,0.4)',
            backdropFilter: 'blur(8px)',
            WebkitBackdropFilter: 'blur(8px)',
            borderRadius: 6,
            padding: '4px 10px',
          }}
        >
          {b.icon && iconMap[b.icon]}
          <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.7)' }}>{b.label}</span>
        </div>
      ))}
    </div>
  );
}
