'use client';

interface Props {
  direction: 'left' | 'right' | null;
  intensity: number; // 0 to 1
}

export default function SwipeBackground({ direction, intensity }: Props) {
  let bg = 'transparent';
  if (direction === 'right' && intensity > 0) {
    bg = 'rgba(160,210,175,' + (intensity * 0.07) + ')';
  } else if (direction === 'left' && intensity > 0) {
    bg = 'rgba(210,160,160,' + (intensity * 0.06) + ')';
  }

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        borderRadius: 18,
        background: bg,
        transition: 'background 0.2s ease',
        zIndex: 0,
      }}
    />
  );
}
