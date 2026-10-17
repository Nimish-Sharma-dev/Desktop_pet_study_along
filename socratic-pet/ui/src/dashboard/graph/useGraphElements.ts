import { useMemo, useRef } from 'react';
import type { Edge } from '@xyflow/react';
import { edgeKey, useStore } from '../../store/useStore';
import { humanize, WEAK } from '../util';
import type { GFlowNode } from './GNode';
import { conceptKey, nodeTitle } from './ids';
import { colIndex, computeLayout } from './layout';

export interface Lit { nodeIds: string[]; edgeKeys: string[] }

const EDGE_COLOR: Record<string, string> = {
  MADE: 'rgba(179,136,255,0.55)', SHOWED: '#ff6b81', RESOLVED: '#4ade80',
  INVOLVES: '#7c9cff', PREREQUISITE_OF: 'rgba(255,255,255,0.28)',
};
const STAGGER = 220;

export function useGraphElements(showPrereq: boolean, selectedId: string | null, lit: Lit | null) {
  const graph = useStore((s) => s.graph);
  const concepts = useStore((s) => s.progress?.concepts);
  const nodeCache = useRef(new Map<string, { sig: string; node: GFlowNode }>());
  const edgeCache = useRef(new Map<string, { sig: string; edge: Edge }>());

  return useMemo(() => {
    const litNodes = new Set(lit?.nodeIds ?? []);
    const litEdges = new Set(lit?.edgeKeys ?? []);
    const live = new Map((concepts ?? []).map((c) => [c.id, c.mastery]));
    const liveByName = new Map((concepts ?? []).map((c) => [c.name.toLowerCase(), c.mastery]));
    const all = Object.values(graph.nodes);
    const { pos, visible } = computeLayout(all, litNodes);

    // reuse node objects whose visible state did not change => React Flow skips re-rendering them
    const nodes: GFlowNode[] = [];
    for (const n of all) {
      const p = pos.get(n.id);
      if (!p) continue;
      const isConcept = n.label === 'Concept';
      const title = nodeTitle(n, humanize);
      const m = isConcept ? (live.get(conceptKey(n)) ?? liveByName.get(title.toLowerCase()) ?? (typeof n.props.mastery === 'number' ? Math.min(1, n.props.mastery > 1 ? n.props.mastery / 100 : n.props.mastery) : undefined)) : undefined;
      const isLit = litNodes.has(n.id);
      const subtitle = n.label === 'Attempt' ? String(n.props.lesson_id ?? '') : n.label === 'Concept' ? humanize(String(n.props.track ?? '')) : n.label === 'Mistake' ? humanize(String(n.props.lesson_id ?? '')) : undefined;
      const passed = n.label === 'Attempt' ? n.props.passed === true : undefined;
      const delay = isLit ? colIndex(n.label) * STAGGER : 0;
      const selected = n.id === selectedId;
      const sig = [p.x, p.y, title, subtitle, m?.toFixed(3), isLit, delay, passed, selected].join('|');
      const prev = nodeCache.current.get(n.id);
      if (prev && prev.sig === sig) { nodes.push(prev.node); continue; }
      const node: GFlowNode = {
        id: n.id, type: 'gnode', position: p, selected, draggable: false,
        data: { kind: n.label, title, subtitle, mastery: m, weak: m !== undefined && m < WEAK, lit: isLit, delay, passed },
      };
      nodeCache.current.set(n.id, { sig, node });
      nodes.push(node);
    }

    const edges: Edge[] = [];
    for (const e of Object.values(graph.edges)) {
      if (!visible.has(e.from) || !visible.has(e.to)) continue;
      const prereq = e.type === 'PREREQUISITE_OF';
      if (prereq && !showPrereq) continue;
      const key = edgeKey(e);
      const isLit = litEdges.has(key);
      const srcLabel = graph.nodes[e.from]?.label ?? '';
      const delay = colIndex(srcLabel) * STAGGER + STAGGER / 2;
      const sig = [isLit, delay].join('|');
      const prev = edgeCache.current.get(key);
      if (prev && prev.sig === sig) { edges.push(prev.edge); continue; }
      const color = EDGE_COLOR[e.type] ?? 'rgba(255,255,255,0.3)';
      const edge: Edge = {
        id: key, source: e.from, target: e.to,
        sourceHandle: prereq ? 'ps' : 'out', targetHandle: prereq ? 'pt' : 'in',
        type: prereq ? 'smoothstep' : 'default',
        className: isLit ? 'edge-lit' : undefined,
        animated: isLit,
        style: {
          stroke: isLit ? color.replace(/rgba\(([^)]+),[^)]+\)/, 'rgb($1)') : color,
          strokeWidth: isLit ? 3 : prereq ? 1 : 1.5,
          strokeDasharray: prereq && !isLit ? '4 4' : undefined,
          ['--delay' as string]: `${delay}ms`,
        },
      };
      edgeCache.current.set(key, { sig, edge });
      edges.push(edge);
    }
    return { nodes, edges };
  }, [graph, concepts, showPrereq, selectedId, lit]);
}
