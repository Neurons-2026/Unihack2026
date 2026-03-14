'use client';

export default function TakeawayItem({ text }: { text: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 8 }}>
      <div
        style={{
          width: 4,
          height: 4,
          borderRadius: '50%',
          background: 'rgba(255,255,255,0.2)',
          flexShrink: 0,
          marginTop: 8,
        }}
      />
      <p style={{ fontSize: 14, color: 'rgba(255,255,255,0.52)', lineHeight: 1.55, margin: 0 }}>
        {text}
      </p>
    </div>
  );
}
