'use client';

import { useState, useEffect, useMemo } from 'react';

interface MolNode {
  x: number;
  y: number;
  r: number;
  color: string;
  delay: number;
}

// Organic molecular cluster — like the reference image
// Varying sizes, cyan/teal/green palette, asymmetric layout
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

// Edges connecting the molecular structure — subtle grey lines
const CLUSTER_EDGES: [number, number][] = [
  // Central hub connections
  [0, 1], [0, 2], [0, 3], [0, 4], [0, 5],
  // Ring connections
  [1, 2], [1, 5], [2, 7], [3, 5], [3, 6], [4, 6], [4, 7],
  // Outer connections
  [1, 9], [2, 10], [5, 8], [6, 11], [3, 8], [7, 10],
  // Cross links
  [1, 3], [2, 4], [5, 9], [6, 4],
];

export default function SplashScreen({ onComplete }: { onComplete: () => void }) {
  const [phase, setPhase] = useState<number>(0);
  // 0 = dark
  // 1 = central node + inner nodes appear
  // 2 = edges draw + outer nodes
  // 3 = all visible, subtle pulse
  // 4 = "neurons" text
  // 5 = tagline
  // 6 = fade out

  useEffect(() => {
    const timers = [
      setTimeout(() => setPhase(1), 300),
      setTimeout(() => setPhase(2), 900),
      setTimeout(() => setPhase(3), 1500),
      setTimeout(() => setPhase(4), 2100),
      setTimeout(() => setPhase(5), 2700),
      setTimeout(() => setPhase(6), 3600),
      setTimeout(() => onComplete(), 4300),
    ];
    return () => timers.forEach(clearTimeout);
  }, [onComplete]);

  return (
    <div
      className="fixed inset-0 z-[9999] flex flex-col items-center justify-center"
      style={{
        background: '#1a1a1a',
        opacity: phase >= 6 ? 0 : 1,
        transition: 'opacity 0.7s ease-in-out',
        pointerEvents: phase >= 6 ? 'none' : 'auto',
      }}
    >
      {/* Subtle ambient glow behind cluster */}
      <div
        className="absolute rounded-full"
        style={{
          width: 350,
          height: 350,
          background: 'radial-gradient(circle, rgba(94,196,196,0.06) 0%, transparent 70%)',
          opacity: phase >= 1 ? 1 : 0,
          transition: 'opacity 1s ease-out',
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
          <filter id="node-shadow">
            <feGaussianBlur stdDeviation="2" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Edges — subtle grey connecting lines */}
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
              stroke="rgba(120,130,130,0.4)"
              strokeWidth={1.5}
              strokeDasharray={length}
              strokeDashoffset={visible ? 0 : length}
              style={{
                transition: `stroke-dashoffset 0.7s ease-out ${i * 0.03}s`,
              }}
            />
          );
        })}

        {/* Nodes — colored circles with inner highlight */}
        {CLUSTER_NODES.map((node, i) => {
          const isInner = node.delay < 5;
          const showPhase = isInner ? 1 : 2;
          const visible = phase >= showPhase;

          return (
            <g key={`n-${i}`}>
              {/* Main circle */}
              <circle
                cx={node.x}
                cy={node.y}
                r={node.r}
                fill={node.color}
                filter="url(#node-shadow)"
                style={{
                  opacity: visible ? 0.9 : 0,
                  transform: visible ? 'scale(1)' : 'scale(0)',
                  transformOrigin: `${node.x}px ${node.y}px`,
                  transition: `all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) ${node.delay * 0.07}s`,
                  animation: phase >= 3 ? `mol-breathe 4s ease-in-out ${node.delay * 0.3}s infinite` : 'none',
                }}
              />
              {/* Inner bright highlight — gives depth/glass feel */}
              {node.r >= 10 && (
                <circle
                  cx={node.x - node.r * 0.2}
                  cy={node.y - node.r * 0.25}
                  r={node.r * 0.45}
                  fill="rgba(255,255,255,0.25)"
                  style={{
                    opacity: visible ? 1 : 0,
                    transition: `opacity 0.5s ease-out ${node.delay * 0.07}s`,
                  }}
                />
              )}
              {/* Small center dot for tiny nodes */}
              {node.r < 10 && (
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={node.r * 0.35}
                  fill="rgba(255,255,255,0.2)"
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

      {/* "neurons" text */}
      <h1
        style={{
          marginTop: 32,
          fontSize: 'clamp(32px, 7vw, 48px)',
          fontWeight: 300,
          color: 'rgba(255,255,255,0.92)',
          letterSpacing: '6px',
          fontFamily: 'system-ui, -apple-system, sans-serif',
          opacity: phase >= 4 ? 1 : 0,
          transform: phase >= 4 ? 'translateY(0)' : 'translateY(12px)',
          transition: 'all 0.7s ease-out',
        }}
      >
        Neurons
      </h1>

      {/* Tagline */}
      <p
        style={{
          marginTop: 14,
          fontSize: 'clamp(10px, 2.5vw, 14px)',
          fontWeight: 400,
          color: 'rgba(160,165,165,0.7)',
          letterSpacing: '5px',
          fontFamily: 'system-ui, -apple-system, sans-serif',
          textTransform: 'uppercase',
          opacity: phase >= 5 ? 1 : 0,
          transform: phase >= 5 ? 'translateY(0)' : 'translateY(8px)',
          transition: 'all 0.6s ease-out',
        }}
      >
        your ai &middot; your pace
      </p>
    </div>
  );
}
