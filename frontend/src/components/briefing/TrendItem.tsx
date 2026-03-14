'use client';

export default function TrendItem({ index, text }: { index: number; text: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 10 }}>
      <div
        style={{
          width: 20,
          height: 20,
          borderRadius: '50%',
          background: 'rgba(255,255,255,0.06)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 11,
          color: 'rgba(255,255,255,0.3)',
          flexShrink: 0,
          marginTop: 2,
        }}
      >
        {index}
      </div>
      <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.52)', lineHeight: 1.55, margin: 0 }}>
        {text}
      </p>
    </div>
  );
}
