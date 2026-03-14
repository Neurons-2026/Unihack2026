'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { GraphNode, GraphEdge, GraphData } from '@/types/graph';
import { buildAdjMap } from '@/data/sampleGraph';
import { getGraph, generateGraphFromCards, mergeGraph } from '@/lib/api';
import { getSessionId } from '@/lib/session';
import { useBasketStore } from '@/stores/useBasketStore';
import { GraphNode as ApiGraphNode, GraphEdge as ApiGraphEdge } from '@/lib/types';

function buildGraphFromAPI(
  apiNodes: ApiGraphNode[],
  apiEdges: ApiGraphEdge[],
  W: number,
  H: number,
): GraphData {
  const todayNodeIds = new Set(apiNodes.filter((n) => (n.is_today ?? true)).map((n) => n.id));
  let todayIdx = 0;

  const nodes: GraphNode[] = apiNodes.map((raw) => {
    const freq = raw.frequency ?? 1;
    const baseR = 8 + Math.min(freq, 5) * 2.5;
    const isToday = raw.is_today ?? true;
    const todayTx = W * 0.3 + Math.random() * W * 0.4;
    const todayTy = H * 0.3 + Math.random() * H * 0.4;
    const fullTx = W * 0.1 + Math.random() * W * 0.8;
    const fullTy = H * 0.08 + Math.random() * H * 0.84;
    const delay = isToday ? 20 + todayIdx * 12 : 0;
    if (isToday) todayIdx++;
    return {
      id: raw.id,
      label: raw.label,
      description: raw.description || '',
      frequency: freq,
      isToday,
      r: baseR,
      x: isToday ? -20 : fullTx,
      y: isToday ? -20 : fullTy,
      vx: 0, vy: 0,
      todayTx, todayTy, fullTx, fullTy,
      tx: isToday ? todayTx : fullTx,
      ty: isToday ? todayTy : fullTy,
      startX: -20, startY: -20,
      cpx: todayTx * 0.5 + Math.random() * 60,
      cpy: -20 + todayTy * 0.3,
      animT: isToday ? 0 : 1,
      animating: false,
      entered: !isToday,
      settled: !isToday,
      opacity: 0,
      scale: isToday ? 0.3 : 1,
      delay,
      breathPhase: Math.random() * Math.PI * 2,
      breathSpeed: 0.015 + Math.random() * 0.01,
      labelAlpha: 0,
      targetLabelAlpha: 0,
      orbiters: isToday
        ? Array.from({ length: 2 + Math.floor(Math.random() * 2) }, () => ({
            angle: Math.random() * Math.PI * 2,
            speed: 0.02 + Math.random() * 0.02,
            dist: baseR * 1.8 + Math.random() * 6,
            size: 1.2 + Math.random(),
          }))
        : [],
    };
  });

  const allEdges: GraphEdge[] = apiEdges.map((e) => ({
    source: e.source_node_id,
    target: e.target_node_id,
  }));
  const todayEdges = allEdges.filter(
    (e) => todayNodeIds.has(e.source) && todayNodeIds.has(e.target),
  );

  return { nodes, todayEdges, fullEdges: allEdges };
}

function easeOutCubic(t: number): number {
  return 1 - Math.pow(1 - t, 3);
}

export default function KnowledgeGraph() {
  const router = useRouter();
  const [detailNode, setDetailNode] = useState<GraphNode | null>(null);
  const [copiedNode, setCopiedNode] = useState(false);
  const [viewMode, setViewMode] = useState<'today' | 'full'>('today');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dataLoaded, setDataLoaded] = useState(false);
  const [merging, setMerging] = useState(false);
  const apiDataRef = useRef<{ nodes: ApiGraphNode[]; edges: ApiGraphEdge[] } | null>(null);
  const basketItems = useBasketStore((s) => s.items);
  const cvRef = useRef<HTMLCanvasElement>(null);
  const dataReady = useRef(false);
  const nodesRef = useRef<GraphNode[]>([]);
  const todayEdgesRef = useRef<GraphEdge[]>([]);
  const fullEdgesRef = useRef<GraphEdge[]>([]);
  const activeEdgesRef = useRef<GraphEdge[]>([]);
  const todayAdjRef = useRef<Record<string, string[]>>({});
  const fullAdjRef = useRef<Record<string, string[]>>({});
  const activeAdjRef = useRef<Record<string, string[]>>({});
  const alwaysShowRef = useRef<Set<string>>(new Set());
  const trailsRef = useRef<{ x: number; y: number; life: number; maxLife: number; sz: number; today: boolean }[]>([]);

  const stateRef = useRef({
    W: 0, H: 0, frame: 0,
    mouseX: -200, mouseY: -200,
    dragging: null as GraphNode | null,
    dragOff: { x: 0, y: 0 },
    moved: false,
    lastTapTime: 0, lastTapNodeId: '',
    selectedNodeIds: new Set<string>(), // Multiple selected nodes
    camScale: 1.7, camTargetScale: 1.7,
    camCx: 0, camCy: 0, camTargetCx: 0, camTargetCy: 0,
    transitioning: false,
    viewMode: 'today' as 'today' | 'full',
  });

  useEffect(() => {
    const sessionId = getSessionId();
    const fetch = basketItems.length > 0
      ? generateGraphFromCards(basketItems, sessionId)
      : getGraph(sessionId);
    fetch
      .then((data) => { apiDataRef.current = data; setDataLoaded(true); })
      .catch(() => setError('Failed to load graph'))
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!dataLoaded || !apiDataRef.current) return;
    const cv = cvRef.current;
    if (!cv) return;
    const ctx = cv.getContext('2d');
    if (!ctx) return;
    const dpr = 2;
    const s = stateRef.current;

    function resize() {
      const rect = cv!.parentElement!.getBoundingClientRect();
      s.W = rect.width; s.H = rect.height;
      cv!.width = s.W * dpr; cv!.height = s.H * dpr;
      cv!.style.width = s.W + 'px'; cv!.style.height = s.H + 'px';
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    resize();
    window.addEventListener('resize', resize);

    if (!dataReady.current) {
      const gd = buildGraphFromAPI(apiDataRef.current!.nodes, apiDataRef.current!.edges, s.W, s.H);
      nodesRef.current = gd.nodes;
      todayEdgesRef.current = gd.todayEdges;
      fullEdgesRef.current = gd.fullEdges;
      activeEdgesRef.current = gd.todayEdges;
      todayAdjRef.current = buildAdjMap(gd.todayEdges);
      fullAdjRef.current = buildAdjMap(gd.fullEdges);
      activeAdjRef.current = todayAdjRef.current;
      s.camCx = s.W / 2; s.camCy = s.H / 2;
      s.camTargetCx = s.W / 2; s.camTargetCy = s.H / 2;
      dataReady.current = true;
    }

    const nodes = nodesRef.current;
    const trails = trailsRef.current;

    function findNode(id: string): GraphNode | undefined {
      for (let i = 0; i < nodes.length; i++) if (nodes[i].id === id) return nodes[i];
      return undefined;
    }
    function updateAlways() {
      const sorted = nodes.filter((n) => n.settled && n.opacity > 0.3).sort((a, b) => b.r - a.r);
      alwaysShowRef.current = new Set(sorted.slice(0, 3).map((n) => n.id));
    }
    // CRITICAL: compute visible world-space boundaries from camera
    // IMPORTANT: Reduce bottom boundary to protect button area from node coverage
    function getVisibleBounds() {
      const halfW = s.W / (2 * s.camScale);
      const halfH = s.H / (2 * s.camScale);
      const buttonSafeZone = 120 / s.camScale; // Prevent nodes from reaching toggle button
      return { left: s.camCx - halfW, right: s.camCx + halfW, top: s.camCy - halfH, bottom: s.camCy + halfH - buttonSafeZone };
    }

    function step() {
      s.frame++;
      const edges = activeEdgesRef.current;
      // Camera interpolation
      s.camScale += (s.camTargetScale - s.camScale) * 0.03;
      s.camCx += (s.camTargetCx - s.camCx) * 0.03;
      s.camCy += (s.camTargetCy - s.camCy) * 0.03;
      // Get visible bounds THIS FRAME
      const vb = getVisibleBounds();

      // Entrance + animation
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        if (!n.isToday && n.fadeIn) { n.opacity = Math.min(1, n.opacity + 0.018); if (n.opacity >= 1) n.fadeIn = false; }
        if (!n.isToday && n.fadeOut) { n.opacity = Math.max(0, n.opacity - 0.025); if (n.opacity <= 0) n.fadeOut = false; }
        if (!n.entered) { if (s.frame >= n.delay) { n.entered = true; n.animating = true; n.animT = 0; } continue; }
        if (n.animating) {
          if (s.frame < n.delay) continue;
          n.animT += 0.022; n.opacity = Math.min(1, n.opacity + 0.05); n.scale = Math.min(1, n.scale + 0.035);
          const t = easeOutCubic(Math.min(1, n.animT));
          n.x = n.startX * (1 - t) * (1 - t) + n.cpx * 2 * (1 - t) * t + n.tx * t * t;
          n.y = n.startY * (1 - t) * (1 - t) + n.cpy * 2 * (1 - t) * t + n.ty * t * t;
          if (n.animT < 1) trails.push({ x: n.x, y: n.y, life: 22, maxLife: 22, sz: n.r * n.scale * 0.4, today: n.isToday });
          if (n.animT >= 1) { n.animating = false; n.settled = true; n.x = n.tx; n.y = n.ty; n.vx = 0; n.vy = 0; n.scale = 1; updateAlways(); }
          continue;
        }
      }
      // Decay trails
      for (let ti = trails.length - 1; ti >= 0; ti--) { trails[ti].life--; if (trails[ti].life <= 0) trails.splice(ti, 1); }

      // Edge springs
      for (let ei = 0; ei < edges.length; ei++) {
        const edge = edges[ei];
        const a = findNode(edge.source), b = findNode(edge.target);
        if (!a || !b || !a.settled || !b.settled) continue;
        const dx = b.x - a.x, dy = b.y - a.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;
        const target = (a.r + b.r) * 3;
        const f = (dist - target) * 0.002;
        if (a !== s.dragging) { a.vx += (dx / dist) * f; a.vy += (dy / dist) * f; }
        if (b !== s.dragging) { b.vx -= (dx / dist) * f; b.vy -= (dy / dist) * f; }
      }
      // Node physics
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        if (n === s.dragging || !n.settled || n.opacity < 0.1) continue;
        // Repulsion
        for (let j = 0; j < nodes.length; j++) {
          if (j === i) continue;
          const m = nodes[j];
          if (!m.settled || m.opacity < 0.1) continue;
          const dx = n.x - m.x, dy = n.y - m.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const minDist = n.r + m.r + 22;
          if (dist < minDist) { const rep = ((minDist - dist) / minDist) * 0.8; n.vx += (dx / dist) * rep; n.vy += (dy / dist) * rep; }
          if (dist < 140) { n.vx += (dx * 0.018) / dist; n.vy += (dy * 0.018) / dist; }
        }
        // Center gravity toward VISIBLE center
        n.vx += ((vb.left + vb.right) / 2 - n.x) * 0.0003;
        n.vy += ((vb.top + vb.bottom) / 2 - n.y) * 0.0003;
        // VIEWPORT BOUNDARY — nodes bounce against the VISIBLE screen edge
        const pad = n.r + 10;
        if (n.x < vb.left + pad) n.vx += (vb.left + pad - n.x) * 0.08;
        if (n.x > vb.right - pad) n.vx += (vb.right - pad - n.x) * 0.08;
        if (n.y < vb.top + pad) n.vy += (vb.top + pad - n.y) * 0.08;
        if (n.y > vb.bottom - pad) n.vy += (vb.bottom - pad - n.y) * 0.08;
        // Friction
        n.vx *= 0.95; n.vy *= 0.95;
        n.x += n.vx; n.y += n.vy;
        n.breathPhase += n.breathSpeed;
        // Label alpha
        const adj = activeAdjRef.current;
        const isAlways = alwaysShowRef.current.has(n.id);
        let isSelected = false;
        // Check if this node is selected
        if (stateRef.current.selectedNodeIds.has(n.id)) {
          isSelected = true;
        } else {
          // Check if this node is connected to ANY selected node
          const selectedArray = Array.from(stateRef.current.selectedNodeIds);
          for (let si = 0; si < selectedArray.length; si++) {
            const selId = selectedArray[si];
            const nb = adj[selId];
            if (nb && nb.includes(n.id)) { isSelected = true; break; }
          }
        }
        const wmx = (s.mouseX - s.W / 2) / s.camScale + s.camCx;
        const wmy = (s.mouseY - s.H / 2) / s.camScale + s.camCy;
        const dm = Math.hypot(n.x - wmx, n.y - wmy);
        const proxR = 60 / s.camScale;
        const prox = dm < proxR ? 1 : dm < proxR + 40 / s.camScale ? 1 - (dm - proxR) / (40 / s.camScale) : 0;
        n.targetLabelAlpha = (isAlways || isSelected) ? 1 : prox > 0 ? prox : 0;
        n.labelAlpha += (n.targetLabelAlpha - n.labelAlpha) * 0.12;
      }
    }

    function draw() {
      step();
      ctx!.clearRect(0, 0, s.W, s.H);
      ctx!.save();
      ctx!.translate(s.W / 2, s.H / 2);
      ctx!.scale(s.camScale, s.camScale);
      ctx!.translate(-s.camCx, -s.camCy);
      const edges = activeEdgesRef.current;

      // Trails
      for (let ti = 0; ti < trails.length; ti++) {
        const tr = trails[ti]; const a = (tr.life / tr.maxLife) * 0.22;
        ctx!.beginPath(); ctx!.arc(tr.x, tr.y, tr.sz * (tr.life / tr.maxLife), 0, Math.PI * 2);
        ctx!.fillStyle = tr.today ? 'rgba(100,220,220,' + a + ')' : 'rgba(100,210,130,' + a + ')'; ctx!.fill();
      }
      // Edges
      for (let ei = 0; ei < edges.length; ei++) {
        const edge = edges[ei];
        const a = findNode(edge.source), b = findNode(edge.target);
        if (!a || !b || !a.entered || !b.entered || a.opacity < 0.05 || b.opacity < 0.05) continue;
        let al = Math.min(a.opacity, b.opacity);
        if (a.animating || b.animating) al *= 0.25;
        const dx = b.x - a.x, dy = b.y - a.y;
        const emx = (a.x + b.x) / 2 + dy * 0.04, emy = (a.y + b.y) / 2 - dx * 0.04;
        const bt = a.isToday && b.isToday; const bp = !a.isToday && !b.isToday;
        let connSelected = false;
        // Check if either endpoint is selected or connected to any selected node
        if (stateRef.current.selectedNodeIds.has(a.id) || stateRef.current.selectedNodeIds.has(b.id)) {
          connSelected = true;
        } else {
          const adj = activeAdjRef.current;
          const selectedArray = Array.from(stateRef.current.selectedNodeIds);
          for (let si = 0; si < selectedArray.length; si++) {
            const selId = selectedArray[si];
            const nb = adj[selId];
            if ((nb && nb.includes(a.id)) || (nb && nb.includes(b.id))) { connSelected = true; break; }
          }
        }
        ctx!.globalAlpha = al;
        ctx!.beginPath(); ctx!.moveTo(a.x, a.y); ctx!.quadraticCurveTo(emx, emy, b.x, b.y);
        if (bt) { ctx!.strokeStyle = 'rgba(100,220,220,' + (connSelected ? 0.2 : 0.09) + ')'; ctx!.lineWidth = (connSelected ? 1.6 : 1) / s.camScale; }
        else if (bp) { ctx!.strokeStyle = 'rgba(100,210,130,' + (connSelected ? 0.18 : 0.07) + ')'; ctx!.lineWidth = (connSelected ? 1.4 : 0.7) / s.camScale; }
        else { ctx!.strokeStyle = 'rgba(100,218,175,' + (connSelected ? 0.17 : 0.06) + ')'; ctx!.lineWidth = (connSelected ? 1.3 : 0.8) / s.camScale; }
        ctx!.stroke();
        if (a.settled && b.settled) {
          const spd = bt ? 0.008 : 0.005;
          const t = ((s.frame * spd + a.id.charCodeAt(1) * 0.3) % 1);
          const px = a.x * (1 - t) * (1 - t) + emx * 2 * (1 - t) * t + b.x * t * t;
          const py = a.y * (1 - t) * (1 - t) + emy * 2 * (1 - t) * t + b.y * t * t;
          ctx!.beginPath(); ctx!.arc(px, py, (bt ? 1.5 : 1.1) / s.camScale, 0, Math.PI * 2);
          ctx!.fillStyle = bt ? 'rgba(100,220,220,0.25)' : bp ? 'rgba(100,210,130,0.15)' : 'rgba(100,218,175,0.18)'; ctx!.fill();
        }
        ctx!.globalAlpha = 1;
      }
      // Nodes
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        if (!n.entered || n.opacity < 0.01) continue;
        const breath = n.settled ? 1 + Math.sin(n.breathPhase) * 0.06 : 1;
        const r = n.r * breath * n.scale;
        const col = n.isToday ? '100,220,220' : '100,210,130';
        ctx!.globalAlpha = n.opacity;
        const gb = 1 + n.labelAlpha * 0.3;
        const g = ctx!.createRadialGradient(n.x, n.y, r * 0.3, n.x, n.y, r * 2.8 * gb);
        g.addColorStop(0, 'rgba(' + col + ',' + (0.12 + n.labelAlpha * 0.06) + ')');
        g.addColorStop(1, 'rgba(' + col + ',0)');
        ctx!.beginPath(); ctx!.arc(n.x, n.y, r * 2.8 * gb, 0, Math.PI * 2); ctx!.fillStyle = g; ctx!.fill();
        ctx!.beginPath(); ctx!.arc(n.x, n.y, r, 0, Math.PI * 2);
        ctx!.fillStyle = 'rgba(' + col + ',' + (0.55 + n.labelAlpha * 0.15) + ')'; ctx!.fill();
        const bright = n.isToday ? '200,255,255' : '180,240,190';
        ctx!.beginPath(); ctx!.arc(n.x, n.y, r * 0.3, 0, Math.PI * 2);
        ctx!.fillStyle = 'rgba(' + bright + ',' + (0.25 + n.labelAlpha * 0.15) + ')'; ctx!.fill();
        // Label pill
        if (n.labelAlpha > 0.03 && n.settled) {
          const fs = 10 / s.camScale;
          ctx!.font = '500 ' + fs + 'px system-ui, sans-serif';
          const tw = ctx!.measureText(n.label).width;
          const pw = tw + 12 / s.camScale, ph = 17 / s.camScale;
          const lpx = n.x - pw / 2, lpy = n.y + r + 5 / s.camScale;
          ctx!.beginPath(); ctx!.roundRect(lpx, lpy, pw, ph, 8 / s.camScale);
          ctx!.fillStyle = 'rgba(' + col + ',' + (n.labelAlpha * 0.1) + ')'; ctx!.fill();
          ctx!.strokeStyle = 'rgba(' + col + ',' + (n.labelAlpha * 0.12) + ')';
          ctx!.lineWidth = 0.5 / s.camScale; ctx!.stroke();
          ctx!.fillStyle = 'rgba(255,255,255,' + (n.labelAlpha * 0.85) + ')';
          ctx!.textAlign = 'center'; ctx!.textBaseline = 'middle';
          ctx!.fillText(n.label, n.x, lpy + ph / 2);
        }
        // Orbiting particles
        if (n.isToday && n.orbiters && n.settled) {
          for (let oi = 0; oi < n.orbiters.length; oi++) {
            const o = n.orbiters[oi]; o.angle += o.speed;
            const ox = n.x + Math.cos(o.angle) * o.dist * breath;
            const oy = n.y + Math.sin(o.angle) * o.dist * breath;
            ctx!.beginPath(); ctx!.arc(ox, oy, o.size, 0, Math.PI * 2);
            ctx!.fillStyle = 'rgba(150,240,240,0.3)'; ctx!.fill();
            const trx = n.x + Math.cos(o.angle - 0.3) * o.dist * breath;
            const try2 = n.y + Math.sin(o.angle - 0.3) * o.dist * breath;
            ctx!.beginPath(); ctx!.moveTo(ox, oy); ctx!.lineTo(trx, try2);
            ctx!.strokeStyle = 'rgba(150,240,240,0.08)'; ctx!.lineWidth = o.size * 0.7 / s.camScale; ctx!.stroke();
          }
        }
        ctx!.globalAlpha = 1;
      }
      ctx!.restore();
      raf = requestAnimationFrame(draw);
    }
    let raf = requestAnimationFrame(draw);

    // Interaction handlers
    function getXY(e: MouseEvent | TouchEvent) {
      const rect = cv!.getBoundingClientRect();
      const src = 'touches' in e ? (e.touches[0] || (e as TouchEvent).changedTouches[0]) : (e as MouseEvent);
      return { x: src.clientX - rect.left, y: src.clientY - rect.top };
    }
    function screenToWorld(sx: number, sy: number) {
      return { x: (sx - s.W / 2) / s.camScale + s.camCx, y: (sy - s.H / 2) / s.camScale + s.camCy };
    }
    function hitTest(p: { x: number; y: number }): GraphNode | null {
      const wp = screenToWorld(p.x, p.y);
      let hit: GraphNode | null = null;
      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        if (n.settled && n.opacity > 0.3 && Math.hypot(n.x - wp.x, n.y - wp.y) < n.r + 12) hit = n;
      }
      return hit;
    }
    function onDown(e: MouseEvent | TouchEvent) {
      e.preventDefault(); const p = getXY(e); s.moved = false;
      const hit = hitTest(p);
      if (hit) { s.dragging = hit; const wp = screenToWorld(p.x, p.y); s.dragOff = { x: hit.x - wp.x, y: hit.y - wp.y }; hit.vx = 0; hit.vy = 0; }
      else { s.selectedNodeIds.clear(); setDetailNode(null); setCopiedNode(false); }
    }
    function onMove(e: MouseEvent | TouchEvent) {
      const p = getXY(e); s.mouseX = p.x; s.mouseY = p.y;
      if (!s.dragging) return; e.preventDefault(); s.moved = true;
      const wp = screenToWorld(p.x, p.y);
      s.dragging.x = wp.x + s.dragOff.x; s.dragging.y = wp.y + s.dragOff.y;
      s.dragging.vx = 0; s.dragging.vy = 0;
    }
    function onUp() {
      if (s.dragging && !s.moved) {
        const node = s.dragging; const now = Date.now();
        const isDbl = now - s.lastTapTime < 350 && s.lastTapNodeId === node.id;
        if (isDbl) {
          // Double click: show detail sheet, keep label selection active
          setDetailNode(node);
          s.lastTapTime = 0; s.lastTapNodeId = '';
        } else {
          // Single click: toggle selectedNodeIds for persistent label display
          if (s.selectedNodeIds.has(node.id)) {
            s.selectedNodeIds.delete(node.id); // Remove from selection
          } else {
            s.selectedNodeIds.add(node.id); // Add to selection
          }
          setDetailNode(null);
          s.lastTapTime = now; s.lastTapNodeId = node.id;
        }
      } else if (s.dragging && s.moved) { s.dragging.vx *= 2; s.dragging.vy *= 2; }
      s.dragging = null;
    }
    function onLeave() { s.mouseX = -200; s.mouseY = -200; }

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
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataLoaded]);

  async function handleMerge() {
    if (merging) return;
    setMerging(true);
    try {
      const sessionId = getSessionId();
      const data = await mergeGraph(sessionId);
      apiDataRef.current = data;
      dataReady.current = false;
      setDataLoaded(false);
      setTimeout(() => setDataLoaded(true), 50);
    } finally {
      setMerging(false);
    }
  }

  // Toggle handler
  function handleToggle() {
    const s = stateRef.current;
    if (s.transitioning) return;
    s.transitioning = true;
    s.selectedNodeIds.clear(); // Clear all selections on mode toggle
    setDetailNode(null);
    const nodes = nodesRef.current;

    if (s.viewMode === 'today') {
      s.viewMode = 'full'; setViewMode('full');
      s.camTargetScale = 1.0; s.camTargetCx = s.W / 2; s.camTargetCy = s.H / 2;
      nodes.forEach((n) => { if (!n.isToday) { n.fadeIn = true; n.fadeOut = false; } });
      let delay = 0;
      nodes.forEach((n) => {
        if (!n.isToday) return;
        n.startX = n.x; n.startY = n.y;
        n.cpx = (n.x + n.fullTx) / 2 + (Math.random() - 0.5) * 80;
        n.cpy = (n.y + n.fullTy) / 2 + (Math.random() - 0.5) * 60;
        n.tx = n.fullTx; n.ty = n.fullTy;
        n.animT = 0; n.animating = true; n.settled = false;
        n.delay = s.frame + 15 + delay; delay += 8; n.entered = true;
      });
      activeEdgesRef.current = fullEdgesRef.current;
      activeAdjRef.current = fullAdjRef.current;
      setTimeout(() => { s.transitioning = false; }, 3500);
    } else {
      s.viewMode = 'today'; setViewMode('today');
      s.camTargetScale = 1.7; s.camTargetCx = s.W / 2; s.camTargetCy = s.H / 2;
      nodes.forEach((n) => { if (!n.isToday) { n.fadeOut = true; n.fadeIn = false; } });
      let delay = 0;
      nodes.forEach((n) => {
        if (!n.isToday) return;
        n.startX = n.x; n.startY = n.y;
        n.cpx = (n.x + n.todayTx) / 2 + (Math.random() - 0.5) * 60;
        n.cpy = (n.y + n.todayTy) / 2 + (Math.random() - 0.5) * 50;
        n.tx = n.todayTx; n.ty = n.todayTy;
        n.animT = 0; n.animating = true; n.settled = false;
        n.delay = s.frame + 15 + delay; delay += 8; n.entered = true;
      });
      activeEdgesRef.current = todayEdgesRef.current;
      activeAdjRef.current = todayAdjRef.current;
      setTimeout(() => { s.transitioning = false; }, 3500);
    }
  }

  const adj = activeAdjRef.current;
  const graphNodes = nodesRef.current;

  return (
    <div style={{ maxWidth: 390, margin: '0 auto', height: '100dvh', background: '#111111', overflow: 'hidden', display: 'flex', flexDirection: 'column', position: 'relative' }}>
      {/* HEADER */}
      <div style={{ padding: '48px 20px 0', flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 8 }}>
          <button
            onClick={() => router.push('/briefing')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 7,
              padding: '6px 14px 6px 10px',
              borderRadius: 20,
              border: '1px solid rgba(255,255,255,0.1)',
              background: 'rgba(255,255,255,0.06)',
              color: 'rgba(255,255,255,0.5)',
              cursor: 'pointer',
              transition: 'background 0.15s ease, color 0.15s ease',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.12)'; e.currentTarget.style.color = 'rgba(255,255,255,0.7)'; }}
            onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(255,255,255,0.06)'; e.currentTarget.style.color = 'rgba(255,255,255,0.5)'; }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M19 12H5M12 19l-7-7 7-7" /></svg>
            <span style={{ fontSize: 12, fontWeight: 500 }}>Back</span>
          </button>
          <span style={{ fontSize: 15, fontWeight: 500, color: 'rgba(255,255,255,0.9)', marginLeft: 10 }}>Your knowledge</span>
        </div>
        <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.35)', lineHeight: 1.5, marginBottom: 6 }}>
          {loading ? 'Loading your knowledge graph…' : error ? error : (() => {
            const todayCount = (apiDataRef.current?.nodes ?? []).filter(n => n.is_today).length;
            const prevCount = (apiDataRef.current?.nodes ?? []).filter(n => !n.is_today).length;
            return viewMode === 'today'
              ? <>Today you discovered <span style={{ color: 'rgba(100,220,220,0.8)' }}>{todayCount} concept{todayCount !== 1 ? 's' : ''}</span></>
              : <>Your AI knowledge is growing — <span style={{ color: 'rgba(100,220,220,0.8)' }}>{todayCount} new</span>{prevCount > 0 && <> connecting to <span style={{ color: 'rgba(100,210,130,0.8)' }}>{prevCount} previous</span></>}</>;
          })()}
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
            <div style={{ width: 7, height: 7, borderRadius: '50%', background: 'rgba(100,220,220,0.9)', boxShadow: '0 0 6px rgba(100,220,220,0.4)' }} />
            <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)' }}>Today</span>
          </div>
          {viewMode === 'full' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
              <div style={{ width: 7, height: 7, borderRadius: '50%', background: 'rgba(100,210,130,0.8)', boxShadow: '0 0 6px rgba(100,210,130,0.3)' }} />
              <span style={{ fontSize: 10, color: 'rgba(255,255,255,0.3)' }}>Previous</span>
            </div>
          )}
        </div>
      </div>

      {/* CANVAS */}
      <div style={{ flex: 1, position: 'relative', minHeight: 0, overflow: 'hidden' }}>
        <canvas ref={cvRef} style={{ width: '100%', height: '100%', display: 'block', touchAction: 'none' }} />
        {(loading || error) && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <span style={{ fontSize: 14, color: error ? 'rgba(248,113,113,0.7)' : 'rgba(255,255,255,0.25)' }}>
              {error ?? 'Building graph…'}
            </span>
          </div>
        )}

        {/* MERGE BUTTON */}
        <div style={{ position: 'absolute', bottom: 24, right: 20, zIndex: 5 }}>
          <button
            onClick={handleMerge}
            disabled={merging}
            style={{
              backgroundColor: merging ? 'rgba(100,180,255,0.15)' : 'rgba(100,180,255,0.12)',
              color: 'rgba(100,180,255,0.9)',
              fontSize: 12,
              fontWeight: 500,
              padding: '10px 16px',
              borderRadius: 30,
              cursor: merging ? 'default' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              border: '1px solid rgba(100,180,255,0.2)',
              outline: 'none',
              boxShadow: '0 2px 12px rgba(0,0,0,0.2)',
            }}
          >
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
              <circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/>
              <path d="M6 9v6M18 15a6 6 0 00-6-6H9"/>
            </svg>
            {merging ? 'Merging…' : 'Merge Graph'}
          </button>
        </div>

        {/* TOGGLE BUTTON — white bg, grey on hover */}
        <div style={{ position: 'absolute', bottom: 24, left: '50%', transform: 'translateX(-50%)', zIndex: 5 }}>
          <button
            onClick={handleToggle}
            style={{
              backgroundColor: '#ffffff',
              color: '#111111',
              fontSize: 13,
              fontWeight: 500,
              padding: '12px 24px',
              borderRadius: 30,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              border: 'none',
              outline: 'none',
              boxShadow: '0 2px 12px rgba(0,0,0,0.25)',
              transition: 'background-color 0.15s ease',
            }}
            onMouseEnter={(e) => { (e.target as HTMLElement).style.backgroundColor = '#d1d1d1'; }}
            onMouseLeave={(e) => { (e.target as HTMLElement).style.backgroundColor = '#ffffff'; }}
            onMouseDown={(e) => { (e.target as HTMLElement).style.backgroundColor = '#b8b8b8'; }}
            onMouseUp={(e) => { (e.target as HTMLElement).style.backgroundColor = '#d1d1d1'; }}
          >
            {viewMode === 'today' ? (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#111111" strokeWidth="2" strokeLinecap="round"><path d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" /></svg>
                See the full picture
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#111111" strokeWidth="2" strokeLinecap="round"><path d="M4 14h6v6M14 4h6v6M10 14l-7 7M20 4l-7 7" /></svg>
                Today&apos;s additions
              </>
            )}
          </button>
        </div>

        {/* DETAIL BOTTOM SHEET */}
        <div style={{
          position: 'absolute', bottom: 0, left: 0, right: 0,
          background: '#1c1c1e', borderRadius: '18px 18px 0 0',
          padding: 20, paddingBottom: 28,
          transform: detailNode ? 'translateY(0)' : 'translateY(100%)',
          transition: 'transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
          zIndex: 12,
        }}>
          {detailNode && (
            <>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{
                    width: 10, height: 10, borderRadius: '50%',
                    background: detailNode.isToday ? 'rgba(100,220,220,0.8)' : 'rgba(100,210,130,0.8)',
                    boxShadow: detailNode.isToday ? '0 0 6px rgba(100,220,220,0.4)' : '0 0 6px rgba(100,210,130,0.4)',
                  }} />
                  <span style={{ fontSize: 16, fontWeight: 500, color: '#fff' }}>{detailNode.label}</span>
                </div>
                <button
                  onClick={() => setDetailNode(null)}
                  style={{
                    fontSize: 11,
                    fontWeight: 500,
                    color: 'rgba(255,255,255,0.45)',
                    cursor: 'pointer',
                    padding: '5px 14px',
                    borderRadius: 20,
                    border: '1px solid rgba(255,255,255,0.1)',
                    background: 'rgba(255,255,255,0.06)',
                    transition: 'background 0.15s ease, color 0.15s ease',
                  }}
                  onMouseEnter={(e) => { (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.12)'; (e.currentTarget as HTMLElement).style.color = 'rgba(255,255,255,0.7)'; }}
                  onMouseLeave={(e) => { (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.06)'; (e.currentTarget as HTMLElement).style.color = 'rgba(255,255,255,0.45)'; }}
                >Close</button>
              </div>
              <div style={{ fontSize: 12, color: 'rgba(255,255,255,0.35)', marginBottom: 8 }}>
                {detailNode.isToday ? 'Added today' : 'Previous session'} · Seen {detailNode.frequency}x · {(adj[detailNode.id] || []).length} connections
              </div>
              <div style={{ fontSize: 13, color: 'rgba(255,255,255,0.5)', lineHeight: 1.55 }}>{detailNode.description}</div>
              <div style={{ marginTop: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 6 }}>
                  <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.25)', letterSpacing: 0.5 }}>CONNECTED TO</div>
                  <button
                    onClick={async () => {
                      const text = `${detailNode.label}: ${detailNode.description}`;
                      const connections = (adj[detailNode.id] || [])
                        .map((id: string) => graphNodes.find((n: GraphNode) => n.id === id)?.label)
                        .filter(Boolean)
                        .join(', ');
                      const full = `${text}\nConnected to: ${connections}`;
                      if (navigator.share) {
                        try { await navigator.share({ title: detailNode.label, text: full }); } catch {}
                      } else {
                        await navigator.clipboard.writeText(full);
                        setCopiedNode(true);
                        setTimeout(() => setCopiedNode(false), 1500);
                      }
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 5,
                      padding: '4px 10px',
                      borderRadius: 20,
                      border: 'none',
                      background: 'rgba(255,255,255,0.06)',
                      color: copiedNode ? 'rgba(100,220,220,0.8)' : 'rgba(255,255,255,0.3)',
                      fontSize: 11,
                      fontWeight: 500,
                      cursor: 'pointer',
                      transition: 'color 0.2s ease',
                    }}
                  >
                    {copiedNode ? (
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    ) : (
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M4 12v8a2 2 0 002 2h12a2 2 0 002-2v-8" />
                        <polyline points="16 6 12 2 8 6" />
                        <line x1="12" y1="2" x2="12" y2="15" />
                      </svg>
                    )}
                    {copiedNode ? 'Copied' : 'Share'}
                  </button>
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                  {(adj[detailNode.id] || []).map((connId: string) => {
                    const cn = graphNodes.find((nd: GraphNode) => nd.id === connId);
                    if (!cn || cn.opacity < 0.3) return null;
                    return (
                      <span key={connId} style={{
                        fontSize: 11, padding: '3px 8px', borderRadius: 20,
                        backgroundColor: cn.isToday ? 'rgba(100,220,220,0.1)' : 'rgba(100,210,130,0.1)',
                        color: cn.isToday ? 'rgba(100,220,220,0.7)' : 'rgba(100,210,130,0.7)',
                      }}>{cn.label}</span>
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
