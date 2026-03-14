'use client';
import { useEffect, useRef } from 'react';
import { initCanvas, resizeCanvas } from '@/lib/rippleCanvas';

export default function RippleCanvas() {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (ref.current) {
      initCanvas(ref.current);
    }
    const handleResize = () => resizeCanvas();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <canvas
      ref={ref}
      style={{
        position: 'absolute',
        inset: -30,
        pointerEvents: 'none',
        zIndex: 25,
      }}
    />
  );
}
