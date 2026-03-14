'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { GraphNode } from '@/types/graph';
import { buildSampleGraph, buildAdjMap } from '@/data/sampleGraph';

function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

export default function KnowledgeGraph() {
  const router = useRouter();
  const [detailNode, setDetailNode] = useState<GraphNode | null>(null);
  const cvRef = useRef<HTMLCanvasElement>(null);
  const dataReady = useRef(false);
  const nodesRef = useRef<GraphNode[]>([]);
  const edgesRef = useRef<any[]>([]);
  const adjMapRef = useRef<Record<string, string[]>>({});
  const alwaysShowRef = useRef<Set<string>>(new Set());
  const trailsRef = useRef<{ x: number; y: number; life: number; maxLife: number; sz: number }[]>([]);

  const stateRef = useRef({
    W: 0,
    H: 0,
    frame: 0,
    mouseX: -200,
    mouseY: -200,
    dragging: null as GraphNode | null,
    dragOff: { x: 0, y: 0 },
    moved: false,
    lastTapTime: 0,
    lastTapNodeId: '',
    tappedNodeId: '',
  });

  useEffect(() => {
    const cv = cvRef.current;
    if (!cv) return;
    const ctx = cv.getContext('2d');
    if (!ctx) return;

    const dpr = 2;
    const s = stateRef.current;

    // --- RESIZE ---
    function resize() {
      const rect = cv!.parentElement!.getBoundingClientRect();
      s.W = rect.width;
      s.H = rect.height;
      cv!.width = s.W * dpr;
      cv!.height = s.H * dpr;
      cv!.style.width = s.W + 'px';
      cv!.style.height = s.H + 'px';
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    resize();

    // --- BUILD DATA (needs canvas size) ---
    if (!dataReady.current) {
      const graphData = buildSampleGraph(s.W, s.H);
      nodesRef.current = graphData.nodes;
      edgesRef.current = graphData.edges;
      adjMapRef.current = buildAdjMap(graphData.nodes, graphData.edges);
      const sorted = [...graphData.nodes].sort((a, b) => b.r - a.r);
      alwaysShowRef.current = new Set(sorted.slice(0, 3).map((n) => n.id));
      dataReady.current = true;
    }

    const nodes = nodesRef.current;
    const edges = edgesRef.current;
    const adjMap = adjMapRef.current;
    const alwaysShowIds = alwaysShowRef.current;
    const trails = trailsRef.current;

    // --- STEP ---
    function step() {
      s.frame++;
      const W = s.W, H = s.H;

      // --- ENTRANCE ANIMATION ---
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];

        // Previous nodes: gentle fade in
        if (!n.isToday && n.opacity < 1) {
          n.opacity = Math.min(1, n.opacity + 0.025);
          continue;
        }

        // Today nodes: wait for delay, then start arc animation
        if (n.isToday && !n.entered) {
          if (s.frame >= n.delay) {
            n.entered = true;
            n.animating = true;
            n.animT = 0;
          }
          continue;
        }

        // Today nodes: animate along bezier arc
        if (n.isToday && n.animating) {
          n.animT += 0.025;
          n.opacity = Math.min(1, n.opacity + 0.06);
          n.scale = Math.min(1, n.scale + 0.04);
          const t = easeOutCubic(Math.min(1, n.animT));
          const sx = -20, sy = -20;
          // Quadratic bezier: start -> control point -> target
          n.x = sx * (1 - t) * (1 - t) + n.cpx * 2 * (1 - t) * t + n.tx * t * t;
          n.y = sy * (1 - t) * (1 - t) + n.cpy * 2 * (1 - t) * t + n.ty * t * t;
          // Comet trail
          if (n.animT < 1) {
            trails.push({
              x: n.x,
              y: n.y,
              life: 25,
              maxLife: 25,
              sz: n.r * n.scale * 0.5,
            });
          }
          if (n.animT >= 1) {
            n.animating = false;
            n.settled = true;
            n.x = n.tx;
            n.y = n.ty;
            n.vx = 0;
            n.vy = 0;
            n.scale = 1;
          }
          continue;
        }
      }

      // Decay trails
      for (let ti = trails.length - 1; ti >= 0; ti--) {
        trails[ti].life--;
        if (trails[ti].life <= 0) trails.splice(ti, 1);
      }

      // --- PHYSICS (settled nodes only) ---
      for (let ei = 0; ei < edges.length; ei++) {
        const edge = edges[ei];
        let a: GraphNode | undefined, b: GraphNode | undefined;
        for (let ni = 0; ni < nodes.length; ni++) {
          if (nodes[ni].id === edge.source) a = nodes[ni];
          if (nodes[ni].id === edge.target) b = nodes[ni];
        }
        if (!a || !b || !a.settled || !b.settled) continue;
        const dx = b.x - a.x, dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const target = (a.r + b.r) * 3;
        const f = (dist - target) * 0.002;
        const fx = (dx / dist) * f, fy = (dy / dist) * f;
        if (a !== s.dragging) { a.vx += fx; a.vy += fy; }
        if (b !== s.dragging) { b.vx -= fx; b.vy -= fy; }
      }

      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        if (n === s.dragging || !n.settled) continue;

        for (let j = 0; j < nodes.length; j++) {
          if (j === i) continue;
          const m = nodes[j];
          if (!m.settled) continue;
          const dx2 = n.x - m.x, dy2 = n.y - m.y;
          const dist2 = Math.sqrt(dx2 * dx2 + dy2 * dy2) || 1;
          const minDist = n.r + m.r + 25;
          if (dist2 < minDist) {
            const rep = ((minDist - dist2) / minDist) * 0.8;
            n.vx += (dx2 / dist2) * rep;
            n.vy += (dy2 / dist2) * rep;
          }
          if (dist2 < 150) {
            n.vx += (dx2 * 0.02) / dist2;
            n.vy += (dy2 * 0.02) / dist2;
          }
        }

        n.vx += (W / 2 - n.x) * 0.0002;
        n.vy += (H / 2 - n.y) * 0.0002;
        const pad = n.r + 8;
        if (n.x < pad) n.vx += (pad - n.x) * 0.05;
        if (n.x > W - pad) n.vx += (W - pad - n.x) * 0.05;
        if (n.y < pad) n.vy += (pad - n.y) * 0.05;
        if (n.y > H - pad) n.vy += (H - pad - n.y) * 0.05;
        n.vx *= 0.95;
        n.vy *= 0.95;
        n.x += n.vx;
        n.y += n.vy;
        n.breathPhase += n.breathSpeed;

        // --- LABEL ALPHA ---
        const isAlways = alwaysShowIds.has(n.id);
        let isConnectedToTap = false;
        if (s.tappedNodeId !== '') {
          if (n.id === s.tappedNodeId) isConnectedToTap = true;
          const neighbors = adjMap[s.tappedNodeId];
          if (neighbors) {
            for (let k = 0; k < neighbors.length; k++) {
              if (neighbors[k] === n.id) { isConnectedToTap = true; break; }
            }
          }
        }
        const distMouse = Math.sqrt(
          (n.x - s.mouseX) * (n.x - s.mouseX) + (n.y - s.mouseY) * (n.y - s.mouseY)
        );
        const proximity = distMouse < 60 ? 1 : distMouse < 100 ? 1 - (distMouse - 60) / 40 : 0;
        if (isAlways || isConnectedToTap) {
          n.targetLabelAlpha = 1;
        } else if (proximity > 0) {
          n.targetLabelAlpha = proximity;
        } else {
          n.targetLabelAlpha = 0;
        }
        n.labelAlpha += (n.targetLabelAlpha - n.labelAlpha) * 0.12;
      }
    }

    // --- DRAW ---
    function draw() {
      step();
      const W = s.W, H = s.H;
      ctx!.clearRect(0, 0, W, H);

      // COMET TRAILS (behind everything)
      for (let ti = 0; ti < trails.length; ti++) {
        const tr = trails[ti];
        const trAlpha = (tr.life / tr.maxLife) * 0.25;
        const trSize = tr.sz * (tr.life / tr.maxLife);
        ctx!.beginPath();
        ctx!.arc(tr.x, tr.y, trSize, 0, Math.PI * 2);
        ctx!.fillStyle = 'rgba(100,220,220,' + trAlpha + ')';
        ctx!.fill();
      }

      // EDGES
      for (let ei = 0; ei < edges.length; ei++) {
        const edge = edges[ei];
        let a: GraphNode | undefined, b: GraphNode | undefined;
        for (let ni = 0; ni < nodes.length; ni++) {
          if (nodes[ni].id === edge.source) a = nodes[ni];
          if (nodes[ni].id === edge.target) b = nodes[ni];
        }
        if (!a || !b || !a.entered || !b.entered) continue;
        if (a.opacity < 0.1 || b.opacity < 0.1) continue;

        let edgeAlpha = Math.min(a.opacity, b.opacity);
        // Dim edges while nodes are still animating
        if (a.animating || b.animating) edgeAlpha *= 0.3;

        const dx = b.x - a.x, dy = b.y - a.y;
        const mx = (a.x + b.x) / 2 + dy * 0.04;
        const my = (a.y + b.y) / 2 - dx * 0.04;
        const bothToday = a.isToday && b.isToday;
        const bothPrev = !a.isToday && !b.isToday;
        const connToTap =
          s.tappedNodeId !== '' &&
          (a.id === s.tappedNodeId || b.id === s.tappedNodeId);

        ctx!.globalAlpha = edgeAlpha;
        ctx!.beginPath();
        ctx!.moveTo(a.x, a.y);
        ctx!.quadraticCurveTo(mx, my, b.x, b.y);
        if (bothToday) {
          ctx!.strokeStyle = 'rgba(100,220,220,' + (connToTap ? 0.2 : 0.09) + ')';
          ctx!.lineWidth = connToTap ? 1.6 : 1;
        } else if (bothPrev) {
          ctx!.strokeStyle = 'rgba(100,210,130,' + (connToTap ? 0.18 : 0.07) + ')';
          ctx!.lineWidth = connToTap ? 1.4 : 0.7;
        } else {
          ctx!.strokeStyle = 'rgba(100,218,175,' + (connToTap ? 0.17 : 0.06) + ')';
          ctx!.lineWidth = connToTap ? 1.3 : 0.8;
        }
        ctx!.stroke();

        // Energy dots — only when both nodes are settled
        if (a.settled && b.settled) {
          const spd = bothToday ? 0.008 : bothPrev ? 0.004 : 0.006;
          const dotR = bothToday ? 1.8 : 1.3;
          const dotA = bothToday ? 0.3 : bothPrev ? 0.18 : 0.2;
          const dotCol = bothToday ? '100,220,220' : bothPrev ? '100,210,130' : '100,218,175';
          const t = ((s.frame * spd + a.id.charCodeAt(1) * 0.3) % 1);
          const px = a.x * (1 - t) * (1 - t) + mx * 2 * (1 - t) * t + b.x * t * t;
          const py = a.y * (1 - t) * (1 - t) + my * 2 * (1 - t) * t + b.y * t * t;
          ctx!.beginPath();
          ctx!.arc(px, py, dotR, 0, Math.PI * 2);
          ctx!.fillStyle = 'rgba(' + dotCol + ',' + dotA + ')';
          ctx!.fill();
        }
        ctx!.globalAlpha = 1;
      }

      // NODES
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        if (!n.entered || n.opacity < 0.01) continue;

        const breath = n.settled ? 1 + Math.sin(n.breathPhase) * 0.06 : 1;
        const r = n.r * breath * n.scale;
        const col = n.isToday ? '100,220,220' : '100,210,130';

        ctx!.globalAlpha = n.opacity;

        // Glow
        const glowBoost = 1 + n.labelAlpha * 0.3;
        const g1 = ctx!.createRadialGradient(n.x, n.y, r * 0.3, n.x, n.y, r * 2.8 * glowBoost);
        g1.addColorStop(0, 'rgba(' + col + ',' + (0.12 + n.labelAlpha * 0.06) + ')');
        g1.addColorStop(1, 'rgba(' + col + ',0)');
        ctx!.beginPath();
        ctx!.arc(n.x, n.y, r * 2.8 * glowBoost, 0, Math.PI * 2);
        ctx!.fillStyle = g1;
        ctx!.fill();

        // Core
        ctx!.beginPath();
        ctx!.arc(n.x, n.y, r, 0, Math.PI * 2);
        ctx!.fillStyle = 'rgba(' + col + ',' + (0.55 + n.labelAlpha * 0.15) + ')';
        ctx!.fill();

        // Bright center
        const bright = n.isToday ? '200,255,255' : '180,240,190';
        ctx!.beginPath();
        ctx!.arc(n.x, n.y, r * 0.3, 0, Math.PI * 2);
        ctx!.fillStyle = 'rgba(' + bright + ',' + (0.25 + n.labelAlpha * 0.15) + ')';
        ctx!.fill();

        // Label pill — only when settled and alpha above threshold
        if (n.labelAlpha > 0.03 && n.settled) {
          ctx!.font = '500 10px system-ui, sans-serif';
          const tw = ctx!.measureText(n.label).width;
          const pw = tw + 12, ph = 17;
          const lpx = n.x - pw / 2, lpy = n.y + r + 6;
          ctx!.beginPath();
          ctx!.roundRect(lpx, lpy, pw, ph, 8);
          ctx!.fillStyle = 'rgba(' + col + ',' + (n.labelAlpha * 0.1) + ')';
          ctx!.fill();
          ctx!.strokeStyle = 'rgba(' + col + ',' + (n.labelAlpha * 0.12) + ')';
          ctx!.lineWidth = 0.5;
          ctx!.stroke();
          ctx!.fillStyle = 'rgba(255,255,255,' + (n.labelAlpha * 0.85) + ')';
          ctx!.textAlign = 'center';
          ctx!.textBaseline = 'middle';
          ctx!.fillText(n.label, n.x, lpy + ph / 2);
        }

        // Orbiting particles — today nodes, only when settled
        if (n.isToday && n.orbiters && n.settled) {
          for (let oi = 0; oi < n.orbiters.length; oi++) {
            const o = n.orbiters[oi];
            o.angle += o.speed;
            const ox = n.x + Math.cos(o.angle) * o.dist * breath;
            const oy = n.y + Math.sin(o.angle) * o.dist * breath;
            ctx!.beginPath();
            ctx!.arc(ox, oy, o.size, 0, Math.PI * 2);
            ctx!.fillStyle = 'rgba(150,240,240,0.35)';
            ctx!.fill();
            const trx = n.x + Math.cos(o.angle - 0.3) * o.dist * breath;
            const try2 = n.y + Math.sin(o.angle - 0.3) * o.dist * breath;
            ctx!.beginPath();
            ctx!.moveTo(ox, oy);
            ctx!.lineTo(trx, try2);
            ctx!.strokeStyle = 'rgba(150,240,240,0.1)';
            ctx!.lineWidth = o.size * 0.7;
            ctx!.stroke();
          }
        }
        ctx!.globalAlpha = 1;
      }

      raf = requestAnimationFrame(draw);
    }

    let raf = requestAnimationFrame(draw);

    // --- INTERACTION HANDLERS ---
    function getXY(e: MouseEvent | TouchEvent) {
      const rect = cv!.getBoundingClientRect();
      const src = 'touches' in e
        ? (e.touches[0] || (e as TouchEvent).changedTouches[0])
        : (e as MouseEvent);
      return { x: src.clientX - rect.left, y: src.clientY - rect.top };
    }
    function hitTest(p: { x: number; y: number }): GraphNode | null {
      let hit: GraphNode | null = null;
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        if (n.settled && Math.sqrt((n.x - p.x) * (n.x - p.x) + (n.y - p.y) * (n.y - p.y)) < n.r + 12) {
          hit = n;
        }
      }
      return hit;
    }
    function onDown(e: MouseEvent | TouchEvent) {
      e.preventDefault();
      const p = getXY(e);
      s.moved = false;
      const hit = hitTest(p);
      if (hit) {
        s.dragging = hit;
        s.dragOff = { x: hit.x - p.x, y: hit.y - p.y };
        hit.vx = 0;
        hit.vy = 0;
      } else {
        s.tappedNodeId = '';
        setDetailNode(null);
      }
    }
    function onMove(e: MouseEvent | TouchEvent) {
      const p = getXY(e);
      s.mouseX = p.x;
      s.mouseY = p.y;
      if (!s.dragging) return;
      e.preventDefault();
      s.moved = true;
      s.dragging.x = p.x + s.dragOff.x;
      s.dragging.y = p.y + s.dragOff.y;
      s.dragging.vx = 0;
      s.dragging.vy = 0;
    }
    function onUp() {
      if (s.dragging && !s.moved) {
        const node = s.dragging;
        const now = Date.now();
        const isDoubleTap =
          now - s.lastTapTime < 350 && s.lastTapNodeId === node.id;
        if (isDoubleTap) {
          setDetailNode(node);
          s.tappedNodeId = '';
          s.lastTapTime = 0;
          s.lastTapNodeId = '';
        } else {
          s.tappedNodeId = node.id;
          setDetailNode(null);
          s.lastTapTime = now;
          s.lastTapNodeId = node.id;
        }
      } else if (s.dragging && s.moved) {
        s.dragging.vx *= 2;
        s.dragging.vy *= 2;
      }
      s.dragging = null;
    }
    function onLeave() {
      s.mouseX = -200;
      s.mouseY = -200;
    }

    cv!.addEventListener('mousedown', onDown as any);
    cv!.addEventListener('touchstart', onDown as any, { passive: false });
    window.addEventListener('mousemove', onMove as any);
    window.addEventListener('touchmove', onMove as any, { passive: false });
    window.addEventListener('mouseup', onUp);
    window.addEventListener('touchend', onUp);
    cv!.addEventListener('mouseleave', onLeave);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', resize);
      cv!.removeEventListener('mousedown', onDown as any);
      cv!.removeEventListener('touchstart', onDown as any);
      window.removeEventListener('mousemove', onMove as any);
      window.removeEventListener('touchmove', onMove as any);
      window.removeEventListener('mouseup', onUp);
      window.removeEventListener('touchend', onUp);
      cv!.removeEventListener('mouseleave', onLeave);
    };
  }, []);

  const adjMap = adjMapRef.current;
  const graphNodes = nodesRef.current;

  return (
    <div
      style={{
        maxWidth: 390,
        margin: '0 auto',
        height: '100dvh',
        background: '#111111',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        position: 'relative',
      }}
    >
      {/* HEADER */}
      <div style={{ padding: '48px 20px 0', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
          <div onClick={() => router.push('/briefing')} style={{ display: 'flex', alignItems: 'center', gap: 10, cursor: 'pointer' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.5)" strokeWidth="2" strokeLinecap="round"><path d="M19 12H5M12 19l-7-7 7-7" /></svg>
            <span style={{ fontSize: 15, fontWeight: 500, color: 'rgba(255,255,255,0.9)' }}>Knowledge graph</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10, marginBottom: 6 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'rgba(100,220,220,0.9)', boxShadow: '0 0 8px rgba(100,220,220,0.5)' }} />
            <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)' }}>Today</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{ width: 8, height: 8, borderRadius: '50%', background: 'rgba(100,210,130,0.8)', boxShadow: '0 0 6px rgba(100,210,130,0.3)' }} />
            <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)' }}>Previous</span>
          </div>
        </div>
        <div style={{ fontSize: 10, color: 'rgba(255,255,255,0.2)', marginBottom: 4 }}>
          Tap = reveal connections · Double-tap = details · Drag = move
        </div>
      </div>

      {/* CANVAS */}
      <div style={{ flex: 1, position: 'relative', minHeight: 0 }}>
        <canvas ref={cvRef} style={{ width: '100%', height: '100%', display: 'block', touchAction: 'none' }} />

        {/* DETAIL BOTTOM SHEET */}
        <div
          style={{
            position: 'absolute',
            bottom: 0,
            left: 0,
            right: 0,
            background: '#1c1c1e',
            borderRadius: '18px 18px 0 0',
            padding: 20,
            paddingBottom: 28,
            transform: detailNode ? 'translateY(0)' : 'translateY(100%)',
            transition: 'transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
            zIndex: 10,
          }}
        >
          {detailNode && (
            <>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 10, height: 10, borderRadius: '50%', background: detailNode.isToday ? 'rgba(100,220,220,0.8)' : 'rgba(100,210,130,0.8)', boxShadow: detailNode.isToday ? '0 0 6px rgba(100,220,220,0.4)' : '0 0 6px rgba(100,210,130,0.4)' }} />
                  <span style={{ fontSize: 16, fontWeight: 500, color: '#fff' }}>{detailNode.label}</span>
                </div>
                <span onClick={() => setDetailNode(null)} style={{ fontSize: 12, color: 'rgba(255,255,255,0.3)', cursor: 'pointer', padding: '4px 8px' }}>Close</span>
              </div>
              <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.35)', marginBottom: 8 }}>
                {detailNode.isToday ? 'Added today' : 'Previous session'} · Seen {detailNode.frequency}x · {(adjMap[detailNode.id] || []).length} connections
              </div>
              <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.5)', lineHeight: 1.55 }}>{detailNode.description}</div>
              <div style={{ marginTop: 12 }}>
                <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.25)', marginBottom: 6, letterSpacing: 0.5 }}>CONNECTED TO</div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {(adjMap[detailNode.id] || []).map((connId: string) => {
                    const connNode = graphNodes.find((nd: GraphNode) => nd.id === connId);
                    if (!connNode) return null;
                    const isT = connNode.isToday;
                    return (
                      <span key={connId} style={{ fontSize: 11, padding: '3px 8px', borderRadius: 20, backgroundColor: isT ? 'rgba(100,220,220,0.1)' : 'rgba(100,210,130,0.1)', color: isT ? 'rgba(100,220,220,0.7)' : 'rgba(100,210,130,0.7)' }}>
                        {connNode.label}
                      </span>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
