'use client';
import { getTagStyle } from '@/lib/tagColors';

export default function KeywordTags({ keywords }: { keywords: string[] }) {
  return (
    <div className="keyword-tags" style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
      {keywords.slice(0, 4).map((kw) => {
        const s = getTagStyle(kw);
        return (
          <span
            key={kw}
            className="keyword-tag"
            data-bg={s.bg}
            data-text={s.text}
            style={{
              fontSize: 11,
              padding: '4px 10px',
              borderRadius: 9999,
              backgroundColor: s.bg,
              color: s.text,
              transition: 'background-color 0.15s ease, color 0.15s ease',
            }}
          >
            {kw}
          </span>
        );
      })}
    </div>
  );
}
