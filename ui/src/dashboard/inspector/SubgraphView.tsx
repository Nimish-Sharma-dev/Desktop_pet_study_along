import type { GraphTrace } from '../../types/contracts';
import { colIndex } from '../graph/layout';
import { humanize } from '../util';

const KIND_COLOR: Record<string, string> = { Student: '#b388ff', Attempt: '#7fd4ff', Mistake: '#ff6b81', Concept: '#7c9cff' };
const EDGE_COLOR: Record<string, string> = { MADE: '#b388ff', SHOWED: '#ff6b81', RESOLVED: '#4ade80', INVOLVES: '#7c9cff', PREREQUISITE_OF: '#9aa3c4' };
const NW = 132, NH = 38, GX = 22, GY = 62;

const nameOf = (id: string, props: Record<string, unknown>) => String(props.name ?? props.title ?? humanize(id.replace(/^[A-Za-z]+:/, '')));
const clip = (s: string, n: number) => (s.length > n ? s.slice(0, n - 1) + '…' : s);

// Static top-to-bottom rendering of the sub-graph a query returned (Student > Attempt > Mistake > Concept).
export function SubgraphView({ trace }: { trace: GraphTrace }) {
  const rows = new Map<number, string[]>();
  for (const n of trace.nodes) {
    const r = colIndex(n.label);
    rows.set(r, [...(rows.get(r) ?? []), n.id]);
  }
  const rowKeys = [...rows.keys()].sort((a, b) => a - b);
  const maxPer = Math.max(1, ...[...rows.values()].map((v) => v.length));
  const W = maxPer * NW + (maxPer - 1) * GX + 24;
  const H = rowKeys.length * NH + (rowKeys.length - 1) * GY + 24;

  const pos = new Map<string, { x: number; y: number }>();
  rowKeys.forEach((rk, ri) => {
    const ids = rows.get(rk)!;
    const total = ids.length * NW + (ids.length - 1) * GX;
    ids.forEach((id, i) => pos.set(id, { x: (W - total) / 2 + i * (NW + GX), y: 12 + ri * (NH + GY) }));
  });

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ maxHeight: 420 }} role="img" aria-label="Sub-graph returned by the query">
      {trace.edges.map((e, i) => {
        const a = pos.get(e.from), b = pos.get(e.to);
        if (!a || !b) return null;
        const x1 = a.x + NW / 2, y1 = a.y + NH, x2 = b.x + NW / 2, y2 = b.y;
        const my = (y1 + y2) / 2;
        const color = EDGE_COLOR[e.type] ?? '#9aa3c4';
        return (
          <g key={`${e.from}-${e.type}-${e.to}`} style={{ ['--d' as string]: `${i * 90}ms` }}>
            <path d={`M${x1},${y1} C${x1},${my} ${x2},${my} ${x2},${y2}`} fill="none" stroke={color} strokeWidth={1.8} pathLength={1} className="sg-edge" />
            <text x={(x1 + x2) / 2} y={my + 3} textAnchor="middle" fontSize="8" fill={color} className="sg-fade" stroke="rgba(14,16,28,0.9)" strokeWidth="3" paintOrder="stroke">{e.type}</text>
          </g>
        );
      })}
      {trace.nodes.map((n, i) => {
        const p = pos.get(n.id);
        if (!p) return null;
        const c = KIND_COLOR[n.label] ?? '#8b93b0';
        return (
          <g key={n.id} transform={`translate(${p.x},${p.y})`} className="sg-fade" style={{ ['--d' as string]: `${colIndex(n.label) * 160 + i * 20}ms` }}>
            <rect width={NW} height={NH} rx={9} fill={c} fillOpacity={0.16} stroke={c} strokeWidth={1.4} />
            <text x={NW / 2} y={15} textAnchor="middle" fontSize="10" fontWeight="600" fill="#e6e9f5">{clip(nameOf(n.id, n.props), 20)}</text>
            <text x={NW / 2} y={29} textAnchor="middle" fontSize="8" fill={c}>{n.label}</text>
          </g>
        );
      })}
    </svg>
  );
}
