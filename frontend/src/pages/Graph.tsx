import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { useNavigate } from "react-router-dom";
import ForceGraph2D from "react-force-graph-2d";
import { getGraph } from "../api/graph";
import type { GraphNode, GraphEdge } from "../types/graph";

const TYPE_CONFIG: Record<string, { label: string; color: string }> = {
  journal: { label: "Journal", color: "#60a5fa" },
  goal: { label: "Goal", color: "#fbbf24" },
  metric_type: { label: "Metric", color: "#34d399" },
  exercise_type: { label: "Exercise", color: "#fb7185" },
};

const EDGE_DASH: Record<string, number[] | null> = {
  mentions: null,
  tracks: [5, 5],
  shared_tag: [2, 2],
};

function getEntityLink(nodeId: string): string {
  const [type, ...idParts] = nodeId.split(":");
  const id = idParts.join(":");
  switch (type) {
    case "journal":
      return `/journals/${id}`;
    case "goal":
      return "/goals";
    case "metric_type":
      return "/metrics";
    case "exercise_type":
      return "/results";
    default:
      return "/";
  }
}

export default function Graph() {
  const navigate = useNavigate();
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTypes, setActiveTypes] = useState<Set<string>>(
    new Set(["journal", "goal", "metric_type", "exercise_type"]),
  );
  const [includeOrphans, setIncludeOrphans] = useState(false);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const lastClickRef = useRef<{ id: string; time: number } | null>(null);

  const loadGraph = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getGraph({ include_orphans: includeOrphans });
      setNodes(data.nodes);
      setEdges(data.edges);
    } finally {
      setLoading(false);
    }
  }, [includeOrphans]);

  useEffect(() => {
    loadGraph();
  }, [loadGraph]);

  const filteredNodes = useMemo(
    () => nodes.filter((n) => activeTypes.has(n.type)),
    [nodes, activeTypes],
  );

  const filteredNodeIds = useMemo(() => new Set(filteredNodes.map((n) => n.id)), [filteredNodes]);

  const filteredEdges = useMemo(
    () => edges.filter((e) => filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target)),
    [edges, filteredNodeIds],
  );

  const graphData = useMemo(
    () => ({
      nodes: filteredNodes,
      edges: filteredEdges,
    }),
    [filteredNodes, filteredEdges],
  );

  const toggleType = (type: string) => {
    setActiveTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) {
        next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  };

  const handleNodeClick = useCallback(
    (node: GraphNode) => {
      const now = Date.now();
      const last = lastClickRef.current;
      if (last && last.id === node.id && now - last.time < 400) {
        // Double-click: navigate
        lastClickRef.current = null;
        navigate(getEntityLink(node.id));
        return;
      }
      lastClickRef.current = { id: node.id, time: now };
      setSelectedNode(node);
    },
    [navigate],
  );

  const nodeConnections = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const e of filteredEdges) {
      counts[e.source] = (counts[e.source] || 0) + 1;
      counts[e.target] = (counts[e.target] || 0) + 1;
    }
    return counts;
  }, [filteredEdges]);

  if (loading) {
    return (
      <div className="flex h-[calc(100vh-3.5rem)] items-center justify-center md:h-screen">
        <div className="text-light-text/50">Loading graph…</div>
      </div>
    );
  }

  if (nodes.length === 0) {
    return (
      <div className="flex h-[calc(100vh-3.5rem)] items-center justify-center md:h-screen">
        <div className="text-center text-light-text/50">
          <p className="text-lg">No data to visualize</p>
          <p className="text-sm">
            Add journal entries, metrics, results, and goals to see your health graph.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative h-[calc(100vh-3.5rem)] overflow-hidden md:h-screen">
      {/* Control Panel */}
      <div className="bg-dark-card/90 absolute left-3 top-3 z-10 flex flex-col gap-2 rounded-lg p-3 shadow-lg backdrop-blur">
        <h2 className="text-sm font-semibold text-light-text">Filters</h2>

        {/* Type toggles */}
        <div className="flex flex-wrap gap-1">
          {Object.entries(TYPE_CONFIG).map(([type, cfg]) => (
            <button
              key={type}
              onClick={() => toggleType(type)}
              className={`rounded-full px-2.5 py-1 text-xs font-medium transition-colors ${
                activeTypes.has(type) ? "text-white" : "bg-slate-700/50 text-slate-500"
              }`}
              style={activeTypes.has(type) ? { backgroundColor: cfg.color } : undefined}
            >
              {cfg.label}
            </button>
          ))}
        </div>

        {/* Include orphans */}
        <label className="flex items-center gap-2 text-xs text-slate-400">
          <input
            type="checkbox"
            checked={includeOrphans}
            onChange={(e) => setIncludeOrphans(e.target.checked)}
            aria-label="Include orphans"
            className="rounded"
          />
          Include orphans
        </label>
      </div>

      {/* Node detail panel */}
      {selectedNode && (
        <div className="bg-dark-card/90 absolute right-3 top-3 z-10 w-64 rounded-lg p-4 shadow-lg backdrop-blur">
          <div className="mb-2 flex items-start justify-between">
            <h3 className="text-sm font-semibold text-light-text">{selectedNode.label}</h3>
            <button
              onClick={() => setSelectedNode(null)}
              className="text-slate-500 hover:text-slate-300"
              aria-label="Close"
            >
              ×
            </button>
          </div>

          <div className="space-y-1.5 text-xs text-slate-400">
            <div>
              <span
                className="inline-block rounded-full px-2 py-0.5 text-white"
                style={{
                  backgroundColor: TYPE_CONFIG[selectedNode.type]?.color ?? "#64748b",
                }}
              >
                {TYPE_CONFIG[selectedNode.type]?.label ?? selectedNode.type}
              </span>
            </div>

            {selectedNode.date && <div>Date: {selectedNode.date}</div>}
            {selectedNode.status && <div>Status: {selectedNode.status}</div>}
            {selectedNode.progress !== undefined && selectedNode.progress !== null && (
              <div>
                Progress: {selectedNode.progress}%
                <div className="mt-1 h-1.5 w-full rounded-full bg-slate-700">
                  <div
                    className="h-1.5 rounded-full bg-primary"
                    style={{ width: `${selectedNode.progress}%` }}
                  />
                </div>
              </div>
            )}
            {selectedNode.tags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {selectedNode.tags.map((t) => (
                  <span key={t} className="rounded bg-slate-700 px-1.5 py-0.5 text-[10px]">
                    {t}
                  </span>
                ))}
              </div>
            )}
            <div>Connections: {nodeConnections[selectedNode.id] ?? 0}</div>
          </div>

          <button
            onClick={() => navigate(getEntityLink(selectedNode.id))}
            className="mt-3 text-xs text-primary hover:underline"
          >
            Go to detail →
          </button>
        </div>
      )}

      {/* Graph canvas */}
      <ForceGraph2D
        graphData={{
          nodes: graphData.nodes,
          links: graphData.edges.map((e) => ({
            source: e.source,
            target: e.target,
            type: e.type,
            tag: e.tag,
          })),
        }}
        nodeId="id"
        nodeLabel={(node: GraphNode) => node.label}
        nodeColor={(node: GraphNode) => TYPE_CONFIG[node.type]?.color ?? "#64748b"}
        nodeVal={(node: GraphNode) => Math.max(2, (nodeConnections[node.id] || 0) + 1)}
        linkLineDash={(link: { type?: string }) => EDGE_DASH[link.type ?? "mentions"] ?? null}
        linkColor={() => "#475569"}
        linkWidth={(link: { type?: string }) => (link.type === "tracks" ? 2 : 1)}
        onNodeClick={handleNodeClick}
        backgroundColor="rgba(0,0,0,0)"
      />
    </div>
  );
}
