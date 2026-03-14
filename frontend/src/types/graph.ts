export interface GraphNode {
  id: string;
  label: string;
  description: string;
  frequency: number;
  isToday: boolean;
  // Runtime rendering state
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
  breathPhase: number;
  breathSpeed: number;
  labelAlpha: number;
  targetLabelAlpha: number;
  orbiters: { angle: number; speed: number; dist: number; size: number }[];
  // Entrance animation state
  tx: number;       // target x (where physics will settle it)
  ty: number;       // target y
  cpx: number;      // bezier control point x (for arc trajectory)
  cpy: number;      // bezier control point y
  animT: number;    // 0..1 progress along arc
  animating: boolean;
  entered: boolean;
  settled: boolean;
  opacity: number;
  scale: number;
  delay: number;    // frames to wait before entering
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}
