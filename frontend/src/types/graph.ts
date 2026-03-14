export interface GraphNode {
  id: string;
  label: string;
  description: string;
  frequency: number;
  isToday: boolean;
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
  todayTx: number;
  todayTy: number;
  fullTx: number;
  fullTy: number;
  tx: number;
  ty: number;
  startX: number;
  startY: number;
  cpx: number;
  cpy: number;
  animT: number;
  animating: boolean;
  entered: boolean;
  settled: boolean;
  opacity: number;
  scale: number;
  delay: number;
  fadeIn?: boolean;
  fadeOut?: boolean;
}

export interface GraphEdge {
  source: string;
  target: string;
}

export interface GraphData {
  nodes: GraphNode[];
  todayEdges: GraphEdge[];
  fullEdges: GraphEdge[];
}
