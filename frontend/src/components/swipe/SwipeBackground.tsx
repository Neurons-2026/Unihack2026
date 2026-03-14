'use client';

interface Props {
  direction: 'left' | 'right' | null;
  intensity: number;
  reveal: { dir: 'left' | 'right'; fading: boolean } | null;
}

const SAVE = 'radial-gradient(ellipse at 55% 45%, rgb(30,90,58) 0%, rgb(15,52,35) 60%, rgb(8,30,18) 100%)';
const SKIP = 'radial-gradient(ellipse at 45% 45%, rgb(90,30,38) 0%, rgb(52,15,22) 60%, rgb(30,8,12) 100%)';

function bg(dir: 'left' | 'right') {
  return dir === 'right' ? SAVE : SKIP;
}

const CLIP: React.CSSProperties = {
  position: 'absolute',
  top: 10,
  left: 10,
  right: 10,
  bottom: 16,
  borderRadius: 18,
  overflow: 'hidden',
  pointerEvents: 'none',
};

export default function SwipeBackground({ direction, intensity, reveal }: Props) {
  const dragOpacity = direction ? Math.min(intensity * 0.65, 0.65) : 0;

  return (
    <>
      {/* Live drag — clipped to card shape */}
      <div style={{ ...CLIP, zIndex: 5 }}>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: direction ? bg(direction) : SAVE,
            opacity: dragOpacity,
          }}
        />
      </div>

      {/* Post-swipe reveal — clipped to card shape */}
      <div style={{ ...CLIP, zIndex: 5 }}>
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: reveal ? bg(reveal.dir) : SAVE,
            opacity: reveal ? (reveal.fading ? 0 : 0.65) : 0,
            transition: reveal?.fading
              ? 'opacity 0.7s cubic-bezier(0.4, 0, 0.2, 1)'
              : 'none',
          }}
        />
      </div>
    </>
  );
}
