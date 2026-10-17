import { useStore } from '../../store/useStore';
import { humanize, masteryTone } from '../util';
import { conceptKey, nodeTitle } from './ids';

export function NodeDetails({ id, onClose, onSelect }: { id: string; onClose: () => void; onSelect: (id: string) => void }) {
  const graph = useStore((s) => s.graph);
  const concepts = useStore((s) => s.progress?.concepts);
  const node = graph.nodes[id];
  if (!node) return null;

  const edges = Object.values(graph.edges);
  const rel = [
    ...edges.filter((e) => e.from === id).map((e) => ({ dir: '→', type: e.type, other: e.to })),
    ...edges.filter((e) => e.to === id).map((e) => ({ dir: '←', type: e.type, other: e.from })),
  ].filter((r) => graph.nodes[r.other]);

  const liveMastery = node.label === 'Concept' ? concepts?.find((c) => c.id === conceptKey(node))?.mastery : undefined;
  const mastery = liveMastery ?? (typeof node.props.mastery === 'number' ? (node.props.mastery > 1 ? node.props.mastery / 100 : node.props.mastery) : undefined);
  const props = Object.entries(node.props).filter(([k]) => k !== 'mastery').map(([k, v]) => [k, typeof v === 'object' ? JSON.stringify(v) : v] as [string, unknown]);
  const fmt = (k: string, v: unknown) => (k === 'ts' && typeof v === 'number' ? new Date(v < 1e12 ? v * 1000 : v).toLocaleTimeString() : String(v));

  return (
    <aside className="glass-card absolute right-3 top-3 z-10 max-h-[calc(100%-24px)] w-72 overflow-y-auto p-4 text-xs" style={{ background: 'rgba(14,16,28,0.8)' }}>
      <div className="mb-2 flex items-start justify-between">
        <div>
          <div className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--d-muted)' }}>{node.label}</div>
          <div className="text-sm font-semibold">{nodeTitle(node, humanize)}</div>
        </div>
        <button onClick={onClose} className="px-1" style={{ color: 'var(--d-muted)' }} aria-label="Close">✕</button>
      </div>

      {mastery !== undefined && (
        <div className="mb-3">
          <div className="mb-1 flex justify-between"><span>Mastery</span><span>{Math.round(mastery * 100)}%</span></div>
          <div className="h-2 overflow-hidden rounded-full bg-white/10">
            <div className="h-full rounded-full" style={{ width: `${mastery * 100}%`, background: masteryTone(mastery) }} />
          </div>
        </div>
      )}

      <dl className="space-y-1">
        <div className="flex justify-between gap-3"><dt style={{ color: 'var(--d-muted)' }}>id</dt><dd className="truncate font-mono">{id}</dd></div>
        {props.map(([k, v]) => (
          <div key={k} className="flex justify-between gap-3"><dt style={{ color: 'var(--d-muted)' }}>{k}</dt><dd className="truncate">{fmt(k, v)}</dd></div>
        ))}
      </dl>

      {rel.length > 0 && (
        <>
          <div className="mb-1 mt-3 text-[10px] uppercase tracking-wider" style={{ color: 'var(--d-muted)' }}>Relationships</div>
          <ul className="space-y-1">
            {rel.map((r, i) => (
              <li key={i}>
                <button onClick={() => onSelect(r.other)} className="flex w-full items-center gap-1.5 rounded px-1.5 py-1 text-left hover:bg-white/10">
                  <span style={{ color: 'var(--d-accent)' }}>{r.dir}</span>
                  <span className="font-mono text-[10px]" style={{ color: 'var(--d-muted)' }}>{r.type}</span>
                  <span className="truncate">{nodeTitle(graph.nodes[r.other], humanize)}</span>
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
    </aside>
  );
}
