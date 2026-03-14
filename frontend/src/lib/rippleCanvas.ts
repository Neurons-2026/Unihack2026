interface Ring {
  x: number;
  y: number;
  radius: number;
  maxRadius: number;
  speed: number;
  lineWidth: number;
  col: string;
  delay: number;
}

let rings: Ring[] = [];
let raf: number | null = null;
let canvas: HTMLCanvasElement | null = null;
let ctx: CanvasRenderingContext2D | null = null;

export function initCanvas(cv: HTMLCanvasElement): void {
  canvas = cv;
  ctx = cv.getContext('2d');
  resizeCanvas();
}

export function resizeCanvas(): void {
  if (!canvas) return;
  const parent = canvas.parentElement;
  if (!parent) return;
  const rect = parent.getBoundingClientRect();
  // 2x for retina sharpness
  canvas.width = (rect.width + 60) * 2;
  canvas.height = (rect.height + 60) * 2;
  canvas.style.width = (rect.width + 60) + 'px';
  canvas.style.height = (rect.height + 60) + 'px';
}

/**
 * Emit 4 concentric rings from center of canvas.
 * Each ring is delayed by 8 frames from the previous one.
 * Save rings: desaturated sage green rgba(160,210,175)
 * Skip rings: desaturated muted rose rgba(210,160,160)
 */
export function emitRipples(saved: boolean): void {
  if (!canvas) return;
  const cx = canvas.width / 2;
  const cy = canvas.height / 2;
  const col = saved ? '160,210,175' : '210,160,160';

  for (let i = 0; i < 4; i++) {
    rings.push({
      x: cx,
      y: cy,
      radius: 10,
      maxRadius: canvas.width * 0.45,
      speed: 2.2 + i * 0.4,
      lineWidth: 1.5,
      col: col,
      delay: i * 8,
    });
  }

  if (!raf) animate();
}

function animate(): void {
  if (!ctx || !canvas) return;
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  for (let i = rings.length - 1; i >= 0; i--) {
    const r = rings[i];

    // Wait for delay frames before starting
    if (r.delay > 0) {
      r.delay--;
      continue;
    }

    r.radius += r.speed;
    const life = 1 - r.radius / r.maxRadius;

    if (life <= 0) {
      rings.splice(i, 1);
      continue;
    }

    const alpha = life * 0.35;
    ctx.beginPath();
    ctx.arc(r.x, r.y, r.radius, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(' + r.col + ',' + alpha + ')';
    ctx.lineWidth = r.lineWidth * life * 2;
    ctx.stroke();
  }

  if (rings.length > 0) {
    raf = requestAnimationFrame(animate);
  } else {
    raf = null;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }
}

export function clearRipples(): void {
  rings = [];
  if (raf) {
    cancelAnimationFrame(raf);
    raf = null;
  }
  if (ctx && canvas) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }
}
