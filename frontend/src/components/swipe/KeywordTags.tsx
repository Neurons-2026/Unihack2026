'use client';
import { getTagStyle } from '@/lib/tagColors';

export default function KeywordTags({ keywords }: { keywords: string[] }) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
      {keywords.slice(0, 4).map((kw) => {
        const s = getTagStyle(kw);
        return (
          <span
            key={kw}
            style={{
              fontSize: 11,
              padding: '4px 10px',
              borderRadius: 9999,
              backgroundColor: s.bg,
              color: s.text,
            }}
          >
            {kw}
          </span>
        );
      })}
    </div>
  );
}
