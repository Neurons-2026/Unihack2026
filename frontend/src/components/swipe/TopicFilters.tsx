'use client';
import { useBasketStore } from '@/stores/useBasketStore';

const topics = ['All', 'Safety', 'Models', 'Open Source', 'Research', 'Agents', 'Tools'];

export default function TopicFilters({
  activeTopic,
  onTopicChange,
}: {
  activeTopic: string;
  onTopicChange: (t: string) => void;
}) {
  const logTopicTap = useBasketStore((s) => s.logTopicTap);

  return (
    <div
      className="hide-scrollbar"
      style={{
        display: 'flex',
        gap: 8,
        overflowX: 'auto',
        WebkitOverflowScrolling: 'touch',
        margin: '0 -20px',
        padding: '0 20px',
      }}
    >
      {topics.map((t) => {
        const active = t === activeTopic;
        return (
          <button
            key={t}
            onClick={() => {
              onTopicChange(t);
              logTopicTap(t);
            }}
            style={{
              flexShrink: 0,
              fontSize: 12,
              padding: '6px 14px',
              borderRadius: 9999,
              border: active ? 'none' : '0.5px solid rgba(255,255,255,0.1)',
              background: active ? 'rgba(255,255,255,0.95)' : 'rgba(255,255,255,0.08)',
              color: active ? '#111111' : 'rgba(255,255,255,0.55)',
              fontWeight: active ? 500 : 400,
              cursor: 'pointer',
            }}
          >
            {t}
          </button>
        );
      })}
    </div>
  );
}
