'use client';

import { useState, useEffect } from 'react';

interface MolNode {
  x: number;
  y: number;
  r: number;
  color: string;
  delay: number;
}

// Organic molecular cluster — varying sizes, cyan/teal/green palette
const CLUSTER_NODES: MolNode[] = [
  // Large central node
  { x: 230, y: 210, r: 28, color: '#5ec4c4', delay: 0 },
  // Medium nodes around center
  { x: 175, y: 150, r: 18, color: '#6ecfcf', delay: 1 },
  { x: 280, y: 140, r: 14, color: '#4a9e9e', delay: 2 },
  { x: 195, y: 280, r: 16, color: '#5ab8a0', delay: 3 },
  { x: 310, y: 240, r: 12, color: '#4c9a6e', delay: 4 },
  // Small accent nodes
  { x: 140, y: 210, r: 8,  color: '#5ec4c4', delay: 5 },
  { x: 280, y: 300, r: 10, color: '#4c9a6e', delay: 6 },
  { x: 320, y: 170, r: 7,  color: '#4a8e6a', delay: 7 },
  { x: 155, y: 290, r: 6,  color: '#4c9a6e', delay: 8 },
  // Tiny outer dots
  { x: 120, y: 160, r: 4,  color: '#6ecfcf', delay: 9 },
  { x: 340, y: 130, r: 4,  color: '#4a8e6a', delay: 10 },
  { x: 350, y: 280, r: 5,  color: '#4c9a6e', delay: 11 },
];

// Edges — gradient lines between connected nodes
const CLUSTER_EDGES: [number, number][] = [
  [0, 1], [0, 2], [0, 3], [0, 4], [0, 5],
  [1, 2], [1, 5], [2, 7], [3, 5], [3, 6], [4, 6], [4, 7],
  [1, 9], [2, 10], [5, 8], [6, 11], [3, 8], [7, 10],
  [1, 3], [2, 4], [5, 9], [6, 4],
];

export default function SplashScreen({ onComplete }: { onComplete: () => void }) {
  const [phase, setPhase] = useState<number>(0);
  // 0 = dark
  // 1 = central node + inner nodes bounce in
  // 2 = edges draw + outer nodes
  // 3 = all visible, breathing
  // 4 = "NEURONS" text with glow
  // 5 = tagline + loading bar
  // 6 = scale-down fade out

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 300),
      setTimeout(() => setPhase(2), 900),
      setTimeout(() => setPhase(3), 1500),
      setTimeout(() => setPhase(4), 2100),
      setTimeout(() => setPhase(5), 2700),
      setTimeout(() => setPhase(6), 3600),
      setTimeout(() => onComplete(), 4400),
    ];
    return () => timers.forEach(clearTimeout);
  }, [onComplete]);

  return (
    <div
      className="fixed inset-0 z-[9999] flex flex-col items-center justify-center"
      style={{
        background: '#1a1a1a',
        opacity: phase >= 6 ? 0 : 1,
        transform: phase >= 6 ? 'scale(0.95)' : 'scale(1)',
        transition: 'opacity 0.8s ease-in-out, transform 0.8s ease-in-out',
        pointerEvents: phase >= 6 ? 'none' : 'auto',
      }}
    >
      {/* Ambient glow behind cluster */}
      <div
        className="absolute rounded-full"
        style={{
          width: 400,
          height: 400,
          background: 'radial-gradient(circle, rgba(94,196,196,0.1) 0%, rgba(76,154,110,0.04) 40%, transparent 70%)',
          opacity: phase >= 1 ? 1 : 0,
          transform: phase >= 3 ? 'scale(1.3)' : 'scale(0.8)',
          transition: 'all 1.5s ease-out',
        }}
      />

      {/* Molecular cluster SVG */}
      <svg
        viewBox="0 0 460 420"
        style={{
          width: 'min(75vw, 340px)',
          height: 'min(65vh, 310px)',
        }}
      >
        <defs>
          {/* Drop shadow for lifted feel */}
          <filter id="node-lift" x="-50%" y="-50%" width="200%" height="200%">
            <feDropShadow dx="0" dy="3" stdDeviation="4" floodColor="rgba(0,0,0,0.4)" />
          </filter>
          {/* Soft glow for nodes */}
          <filter id="node-glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          {/* Gradient definitions for edges */}
          {CLUSTER_EDGES.map(([from, to], i) => (
            <linearGradient
              key={`grad-${i}`}
              id={`edge-grad-${i}`}
              x1={CLUSTER_NODES[from].x}
              y1={CLUSTER_NODES[from].y}
              x2={CLUSTER_NODES[to].x}
              y2={CLUSTER_NODES[to].y}
              gradientUnits="userSpaceOnUse"
            >
              <stop offset="0%" stopColor={CLUSTER_NODES[from].color} stopOpacity={0.35} />
              <stop offset="50%" stopColor="rgba(120,140,140,0.25)" />
              <stop offset="100%" stopColor={CLUSTER_NODES[to].color} stopOpacity={0.35} />
            </linearGradient>
          ))}
        </defs>

        {/* Edges — gradient lines from node to node */}
        {CLUSTER_EDGES.map(([from, to], i) => {
          const n1 = CLUSTER_NODES[from];
          const n2 = CLUSTER_NODES[to];
          const length = Math.sqrt(
            Math.pow(n2.x - n1.x, 2) + Math.pow(n2.y - n1.y, 2)
          );
          const visible = phase >= 2;

          return (
            <line
              key={`e-${i}`}
              x1={n1.x}
              y1={n1.y}
              x2={n2.x}
              y2={n2.y}
              stroke={`url(#edge-grad-${i})`}
              strokeWidth={1.5}
              strokeDasharray={length}
              strokeDashoffset={visible ? 0 : length}
              style={{
                transition: `stroke-dashoffset 0.7s ease-out ${i * 0.03}s`,
              }}
            />
          );
        })}

        {/* Nodes — colored circles with shadow, highlight, and bounce */}
        {CLUSTER_NODES.map((node, i) => {
          const isInner = node.delay < 5;
          const showPhase = isInner ? 1 : 2;
          const visible = phase >= showPhase;
          // Larger nodes get more bounce overshoot
          const bounce = node.r >= 14 ? 'cubic-bezier(0.34, 1.8, 0.64, 1)' : 'cubic-bezier(0.34, 1.4, 0.64, 1)';

          return (
            <g key={`n-${i}`}>
              {/* Shadow underneath — gives "lifted" depth */}
              <ellipse
                cx={node.x + 2}
                cy={node.y + node.r * 0.6}
                rx={node.r * 0.7}
                ry={node.r * 0.25}
                fill="rgba(0,0,0,0.25)"
                style={{
                  opacity: visible ? 1 : 0,
                  transition: `opacity 0.5s ease-out ${node.delay * 0.07}s`,
                }}
              />
              {/* Main circle with glow */}
              <circle
                cx={node.x}
                cy={node.y}
                r={node.r}
                fill={node.color}
                filter="url(#node-glow)"
                style={{
                  opacity: visible ? 0.92 : 0,
                  transform: visible ? 'scale(1)' : 'scale(0)',
                  transformOrigin: `${node.x}px ${node.y}px`,
                  transition: `opacity 0.4s ease-out ${node.delay * 0.07}s, transform 0.6s ${bounce} ${node.delay * 0.07}s`,
                  animation: phase >= 3 ? `mol-breathe 4s ease-in-out ${node.delay * 0.3}s infinite` : 'none',
                }}
              />
              {/* Glass highlight — top-left specular */}
              {node.r >= 10 && (
                <ellipse
                  cx={node.x - node.r * 0.22}
                  cy={node.y - node.r * 0.28}
                  rx={node.r * 0.38}
                  ry={node.r * 0.3}
                  fill="rgba(255,255,255,0.28)"
                  style={{
                    opacity: visible ? 1 : 0,
                    transition: `opacity 0.5s ease-out ${node.delay * 0.07 + 0.1}s`,
                  }}
                />
              )}
              {/* Center dot for small nodes */}
              {node.r < 10 && (
                <circle
                  cx={node.x - node.r * 0.15}
                  cy={node.y - node.r * 0.15}
                  r={node.r * 0.3}
                  fill="rgba(255,255,255,0.25)"
                  style={{
                    opacity: visible ? 1 : 0,
                    transition: `opacity 0.5s ease-out ${node.delay * 0.07}s`,
                  }}
                />
              )}
            </g>
          );
        })}
      </svg>

      {/* "NEURONS" text with glow */}
      <h1
        style={{
          marginTop: 32,
          fontSize: 'clamp(34px, 8vw, 52px)',
          fontWeight: 700,
          color: 'rgba(255,255,255,0.95)',
          letterSpacing: '10px',
          fontFamily: '"SF Mono", "Fira Code", "JetBrains Mono", "Cascadia Code", ui-monospace, monospace',
          textTransform: 'uppercase' as const,
          textShadow: '0 0 30px rgba(94,196,196,0.3), 0 0 60px rgba(94,196,196,0.1)',
          textAlign: 'center' as const,
          width: '100%',
          paddingLeft: '16px',
          opacity: phase >= 4 ? 1 : 0,
          transform: phase >= 4 ? 'translateY(0)' : 'translateY(12px)',
          transition: 'all 0.7s ease-out',
        }}
      >
        NEURONS
      </h1>

      {/* Tagline — matching monospace */}
      <p
        style={{
          marginTop: 14,
          fontSize: 'clamp(9px, 2.2vw, 12px)',
          fontWeight: 500,
          color: 'rgba(160,170,170,0.6)',
          letterSpacing: '5px',
          fontFamily: '"SF Mono", "Fira Code", "JetBrains Mono", "Cascadia Code", ui-monospace, monospace',
          textTransform: 'uppercase' as const,
          textAlign: 'center' as const,
          width: '100%',
          paddingLeft: '8px',
          opacity: phase >= 5 ? 1 : 0,
          transform: phase >= 5 ? 'translateY(0)' : 'translateY(8px)',
          transition: 'all 0.6s ease-out',
        }}
      >
        YOUR AI &middot; YOUR PACE
      </p>

      {/* Loading bar */}
      <div
        style={{
          position: 'absolute',
          bottom: 'max(60px, 8vh)',
          width: 140,
          height: 2,
          background: 'rgba(255,255,255,0.06)',
          borderRadius: 2,
          overflow: 'hidden',
          opacity: phase >= 5 ? 1 : 0,
          transition: 'opacity 0.5s ease-out',
        }}
      >
        <div
          style={{
            height: '100%',
            background: 'linear-gradient(90deg, #4a9e9e, #5ec4c4, #6ecfcf)',
            borderRadius: 2,
            width: phase >= 6 ? '100%' : phase >= 5 ? '50%' : '0%',
            transition: 'width 1s ease-out',
            boxShadow: '0 0 8px rgba(94,196,196,0.4)',
          }}
        />
      </div>
    </div>
  );
}
