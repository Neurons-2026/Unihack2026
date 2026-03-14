"use client";

import { GraphEdge, GraphNode } from "../lib/types";

interface GraphViewProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export function GraphView({ nodes, edges }: GraphViewProps) {
  if (!nodes.length) {
    return <p className="text-sm text-slate-600">No graph yet. Generate from your basket.</p>;
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <p className="mb-3 text-sm font-semibold text-slate-700">Concepts</p>
      <div className="flex flex-wrap gap-2">
        {nodes.map((node) => (
          <span key={node.id} className="rounded-full bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700">
            {node.label}
          </span>
        ))}
      </div>
      {edges.length > 0 && (
        <div className="mt-4 text-xs text-slate-600">
          <p className="font-semibold text-slate-700">Relationships</p>
          <ul className="list-disc space-y-1 pl-5">
            {edges.slice(0, 8).map((edge) => (
              <li key={edge.id}>{edge.source_node_id} → {edge.target_node_id} ({edge.relationship ?? "related"})</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
