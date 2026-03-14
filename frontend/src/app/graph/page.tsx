"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { GraphView } from "../../components/GraphView";
import { getGraph } from "../../lib/api";
import { useAppStore } from "../../lib/store";
import { GraphEdge, GraphNode } from "../../lib/types";

export default function GraphPage() {
  const { sessionId } = useAppStore();
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const res = await getGraph(sessionId);
        setNodes(res.nodes);
        setEdges(res.edges);
      } catch (err) {
        setError("Graph not available yet");
      }
    }
    load();
  }, [sessionId]);

  return (
    <main className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Knowledge graph</p>
          <h1 className="text-2xl font-bold text-slate-900">Connections from your basket</h1>
        </div>
        <Link href="/" className="text-sm font-semibold text-blue-700 underline">
          Back to feed
        </Link>
      </div>

      {error && <p className="text-xs text-slate-600">{error}</p>}

      <GraphView nodes={nodes} edges={edges} />
    </main>
  );
}
