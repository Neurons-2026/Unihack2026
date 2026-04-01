'use client';
import { useRef, useCallback, useEffect } from 'react';

export type SwipeDir = 'left' | 'right' | 'up' | 'down';

interface GravityCardProps {
  onSwipe: (dir: SwipeDir) => void;
  onCardLeftScreen: () => void;
  onDrag?: (offsetX: number, offsetY: number) => void;
  className?: string;
  children: React.ReactNode;
}

const SWIPE_THRESHOLD = 70;
const GRAVITY = 2200;
const MIN_FLING_SPEED = 700;
const DRAG_ROTATION_FACTOR = 12;
const FALL_ROTATION_DAMPING = 0.06;

export default function GravityCard({
  onSwipe,
  onCardLeftScreen,
  onDrag,
  className,
  children,
}: GravityCardProps) {
  const elRef = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);
  const gone = useRef(false);
  const startX = useRef(0);
  const startY = useRef(0);
  const ox = useRef(0);
  const oy = useRef(0);
  const velX = useRef(0);
  const velY = useRef(0);
  const prevX = useRef(0);
  const prevY = useRef(0);
  const prevT = useRef(0);
  const rafId = useRef(0);

  const setTransform = useCallback(
    (x: number, y: number, rot: number) => {
      const el = elRef.current;
      if (el) el.style.transform = `translate3d(${x}px,${y}px,0) rotate(${rot}deg)`;
    },
    [],
  );

  const springBack = useCallback(() => {
    const el = elRef.current;
    if (!el) return;
    el.style.transition = 'transform 0.45s cubic-bezier(0.175,0.885,0.32,1.275)';
    setTransform(0, 0, 0);
    const tid = setTimeout(() => {
      if (el) el.style.transition = '';
    }, 460);
    return () => clearTimeout(tid);
  }, [setTransform]);

  const startGravity = useCallback(
    (dir: SwipeDir, vx: number, vy: number, x0: number, y0: number) => {
      gone.current = true;
      const isVertical = dir === 'up' || dir === 'down';
      let hVel: number;
      let vVel: number;

      if (isVertical) {
        const sign = dir === 'up' ? -1 : 1;
        hVel = vx;
        vVel = Math.abs(vy) < MIN_FLING_SPEED ? MIN_FLING_SPEED * sign : vy;
      } else {
        const sign = dir === 'right' ? 1 : -1;
        hVel = Math.abs(vx) < MIN_FLING_SPEED ? MIN_FLING_SPEED * sign : vx;
        vVel = vy;
      }

      let x = x0;
      let y = y0;
      let rot = (x0 / 300) * DRAG_ROTATION_FACTOR;
      let last = performance.now();

      const step = (now: number) => {
        const dt = Math.min((now - last) / 1000, 0.04);
        last = now;

        vVel += (dir === 'up' ? -GRAVITY : GRAVITY) * dt;
        hVel *= 0.997;
        x += hVel * dt;
        y += vVel * dt;
        rot += hVel * dt * FALL_ROTATION_DAMPING;

        setTransform(x, y, rot);

        const w = window.innerWidth;
        const h = window.innerHeight;
        if (Math.abs(x) > w * 1.5 || Math.abs(y) > h * 1.5) {
          onCardLeftScreen();
          return;
        }
        rafId.current = requestAnimationFrame(step);
      };

      rafId.current = requestAnimationFrame(step);
    },
    [setTransform, onCardLeftScreen],
  );

  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    if (gone.current) return;
    dragging.current = true;
    const el = elRef.current;
    if (el) {
      el.style.transition = '';
      el.setPointerCapture(e.pointerId);
    }
    startX.current = e.clientX;
    startY.current = e.clientY;
    ox.current = 0;
    oy.current = 0;
    prevX.current = e.clientX;
    prevY.current = e.clientY;
    prevT.current = performance.now();
    velX.current = 0;
    velY.current = 0;
  }, []);

  const handlePointerMove = useCallback(
    (e: React.PointerEvent) => {
      if (!dragging.current || gone.current) return;
      const now = performance.now();
      const dt = (now - prevT.current) / 1000;

      ox.current = e.clientX - startX.current;
      oy.current = e.clientY - startY.current;

      if (dt > 0.005) {
        velX.current = (e.clientX - prevX.current) / dt;
        velY.current = (e.clientY - prevY.current) / dt;
        prevX.current = e.clientX;
        prevY.current = e.clientY;
        prevT.current = now;
      }

      const rot = (ox.current / 300) * DRAG_ROTATION_FACTOR;
      setTransform(ox.current, oy.current, rot);
      onDrag?.(ox.current, oy.current);
    },
    [setTransform, onDrag],
  );

  const handlePointerUp = useCallback(() => {
    if (!dragging.current || gone.current) return;
    dragging.current = false;

    const absX = Math.abs(ox.current);
    const absY = Math.abs(oy.current);
    const isVertical = absY > absX;

    if (isVertical && absY > SWIPE_THRESHOLD) {
      const dir: SwipeDir = oy.current < 0 ? 'up' : 'down';
      onSwipe(dir);
      startGravity(dir, velX.current, velY.current, ox.current, oy.current);
    } else if (!isVertical && absX > SWIPE_THRESHOLD) {
      const dir: SwipeDir = ox.current > 0 ? 'right' : 'left';
      onSwipe(dir);
      startGravity(dir, velX.current, velY.current, ox.current, oy.current);
    } else {
      springBack();
      onDrag?.(0, 0);
    }
  }, [onSwipe, startGravity, springBack, onDrag]);

  useEffect(() => {
    return () => {
      if (rafId.current) cancelAnimationFrame(rafId.current);
    };
  }, []);

  return (
    <div
      ref={elRef}
      className={className}
      style={{ touchAction: 'none', willChange: 'transform', cursor: 'grab' }}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
    >
      {children}
    </div>
  );
}
