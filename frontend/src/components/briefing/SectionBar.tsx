'use client';

export default function SectionBar({ label, color }: { label: string; color: string }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14 }}>
      <div style={{ width: 3, height: 16, borderRadius: 2, background: color }} />
      <span
        style={{
          fontSize: 12,
          fontWeight: 500,
          color: 'rgba(255,255,255,0.45)',
          letterSpacing: 0.5,
        }}
      >
        {label}
      </span>
    </div>
  );
}
