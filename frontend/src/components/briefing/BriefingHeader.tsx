'use client';
import { useRouter } from 'next/navigation';

export default function BriefingHeader({
  readingTimeMin,
  scrollProgress,
}: {
  readingTimeMin: number;
  scrollProgress: number;
}) {
  const router = useRouter();

  return (
    <div
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 20,
        background: 'linear-gradient(to bottom, #111111 0%, #111111 70%, transparent 100%)',
        padding: '48px 20px 20px',
      }}
    >
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: 12,
        }}
      >
        <div
          onClick={() => router.push('/')}
          style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="rgba(255,255,255,0.5)"
            strokeWidth="2"
            strokeLinecap="round"
          >
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          <span style={{ fontSize: 13, color: 'rgba(255,255,255,0.5)' }}>Back</span>
        </div>
        <span style={{ fontSize: 11, color: 'rgba(255,255,255,0.3)' }}>
          {readingTimeMin} min read
        </span>
      </div>

      {/* Scroll progress bar */}
      <div
        style={{
          height: 2,
          background: 'rgba(255,255,255,0.06)',
          borderRadius: 1,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            height: 2,
            width: `${scrollProgress}%`,
            background: 'rgba(255,255,255,0.4)',
            borderRadius: 1,
            transition: 'width 0.1s ease-out',
          }}
        />
      </div>
    </div>
  );
}
