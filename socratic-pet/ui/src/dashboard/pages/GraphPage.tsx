import { useEffect, useMemo, useState } from 'react';
import { Background, Controls, ReactFlow, ReactFlowProvider, useReactFlow } from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useStore } from '../../store/useStore';
import { GNode } from '../graph/GNode';
import { NodeDetails } from '../graph/NodeDetails';
import { useGraphElements } from '../graph/useGraphElements';

const nodeTypes = { gnode: GNode };
const LIT_MS = 4200;

function Chip({ on, onClick, children }: { on: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      className="rounded-full border px-2.5 py-1 text-[11px]"
      style={{ borderColor: on ? 'var(--d-accent)' : 'var(--d-border)', color: on ? 'var(--d-accent)' : 'var(--d-muted)', background: 'rgba(14,16,28,0.6)' }}
    >{children}</button>
  );
}

function Legend() {
  const items: [string, string][] = [['Student', '#b388ff'], ['Attempt', '#7fd4ff'], ['Mistake', '#ff6b81'], ['Concept', '#7c9cff'], ['Weak concept', '#ff6b81']];
  return (
    <div className="glass-card absolute bottom-3 left-3 z-10 flex gap-3 px-3 py-2 text-[10px]" style={{ background: 'rgba(14,16,28,0.7)' }}>
      {items.map(([n, c]) => (
        <span key={n} className="flex items-center gap-1.5"><span className="h-2 w-2 rounded-full" style={{ background: c, boxShadow: n === 'Weak concept' ? `0 0 6px ${c}` : undefined }} />{n}</span>
      ))}
    </div>
  );
}

function GraphCanvas() {
  const highlight = useStore((s) => s.highlight);
  const { fitView } = useReactFlow();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [showPrereq, setShowPrereq] = useState(true);
  const [follow, setFollow] = useState(true);
  const [activeAt, setActiveAt] = useState(0);

  // light-up window: active for LIT_MS after each graph_update (and only if recent when the page opens)
  useEffect(() => {
    if (!highlight) return;
    const remaining = LIT_MS - (Date.now() - highlight.at);
    if (remaining <= 0) return;
    setActiveAt(highlight.at);
    const t = setTimeout(() => setActiveAt(0), remaining);
    return () => clearTimeout(t);
  }, [highlight]);

  const lit = useMemo(
    () => (highlight && activeAt === highlight.at ? { nodeIds: highlight.nodeIds, edgeKeys: highlight.edgeKeys } : null),
    [highlight, activeAt],
  );
  const { nodes, edges } = useGraphElements(showPrereq, selectedId, lit);
  const nodeCount = nodes.length;

  // follow the action: gently frame the lit path
  useEffect(() => {
    if (!follow || !lit || !lit.nodeIds.length) return;
    const t = setTimeout(() => void fitView({ nodes: lit.nodeIds.map((id) => ({ id })), padding: 0.6, maxZoom: 1.05, duration: 700 }), 60);
    return () => clearTimeout(t);
  }, [lit, follow, fitView]);

  return (
    <div className="relative h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        colorMode="dark"
        nodesDraggable={false}
        nodesConnectable={false}
        minZoom={0.2}
        maxZoom={1.6}
        fitView
        fitViewOptions={{ padding: 0.15 }}
        onNodeClick={(_, n) => setSelectedId(n.id)}
        onPaneClick={() => setSelectedId(null)}
      >
        <Background gap={26} color="rgba(255,255,255,0.06)" />
        <Controls showInteractive={false} />
      </ReactFlow>

      <div className="absolute left-3 top-3 z-10 flex items-center gap-2">
        <Chip on={follow} onClick={() => setFollow(!follow)}>Follow live</Chip>
        <Chip on={showPrereq} onClick={() => setShowPrereq(!showPrereq)}>Prerequisites</Chip>
        <Chip on={false} onClick={() => void fitView({ padding: 0.15, duration: 500 })}>Fit view</Chip>
        <span className="text-[10px]" style={{ color: 'var(--d-muted)' }}>{nodeCount} nodes</span>
      </div>
      <Legend />
      {selectedId && <NodeDetails id={selectedId} onClose={() => setSelectedId(null)} onSelect={setSelectedId} />}
    </div>
  );
}

export function GraphPage() {
  const empty = useStore((s) => Object.keys(s.graph.nodes).length === 0);
  return (
    <div className="h-full">
      {empty ? (
        <div className="flex h-full items-center justify-center text-sm" style={{ color: 'var(--d-muted)' }}>No graph data yet. Waiting for the daemon (GET /api/graph)…</div>
      ) : (
        <ReactFlowProvider><GraphCanvas /></ReactFlowProvider>
      )}
    </div>
  );
}
