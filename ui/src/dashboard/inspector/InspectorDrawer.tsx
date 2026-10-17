import { useEffect, useState } from 'react';
import { useStore } from '../../store/useStore';
import { humanize } from '../util';
import { CypherView } from './cypher';
import { SubgraphView } from './SubgraphView';

// query_ms is shown exactly as the daemon measured it; nothing here computes or invents timings.
const fmtMs = (v: unknown) => (typeof v === 'number' && Number.isFinite(v) ? `${v} ms` : 'n/a');

export function InspectorDrawer() {
  const open = useStore((s) => s.inspector.drawerOpen);
  const history = useStore((s) => s.inspector.history);
  const close = useStore((s) => s.closeInspectorDrawer);
  const latestAt = history[0]?.at;
  const [idx, setIdx] = useState(0);
  const [copied, setCopied] = useState(false);

  useEffect(() => setIdx(0), [latestAt]); // jump to the newest reaction
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') close(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [open, close]);

  if (!open || !history.length) return null;
  const entry = history[Math.min(idx, history.length - 1)];
  const { trace } = entry;
  const real = history.map((h) => h.trace.query_ms).filter((v): v is number => typeof v === 'number' && Number.isFinite(v));
  const avg = real.length ? real.reduce((a, b) => a + b, 0) / real.length : null;

  const copy = () => {
    void navigator.clipboard?.writeText(trace.cypher).then(() => { setCopied(true); setTimeout(() => setCopied(false), 1200); });
  };

  return (
    <aside className="drawer-in absolute bottom-0 right-0 top-11 z-30 flex w-[min(820px,96%)] flex-col border-l" style={{ background: 'rgba(8,10,20,0.92)', borderColor: 'var(--d-accent)', boxShadow: '-12px 0 40px rgba(0,0,0,0.5)' }}>
      <header className="flex items-start justify-between gap-3 border-b p-4" style={{ borderColor: 'var(--d-border)' }}>
        <div>
          <div className="text-[10px] uppercase tracking-widest" style={{ color: 'var(--d-accent)' }}>FalkorDB live inspector</div>
          <div className="mt-1 flex flex-wrap items-center gap-2 text-xs">
            <span className="rounded-full bg-white/10 px-2 py-0.5 capitalize">{humanize(entry.mistake_id)}</span>
            <span style={{ color: 'var(--d-muted)' }}>hint L{entry.hint_level}</span>
          </div>
          <p className="mt-2 max-w-md text-xs" style={{ color: 'var(--d-muted)' }}>“{entry.question}”</p>
        </div>
        <div className="shrink-0 text-right">
          <div className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--d-muted)' }}>query_ms</div>
          <div className="font-mono text-2xl font-semibold" style={{ color: 'var(--d-accent)' }}>{fmtMs(trace.query_ms)}</div>
          <div className="text-[10px]" style={{ color: 'var(--d-muted)' }}>
            {trace.nodes.length} nodes · {trace.edges.length} edges
            {avg !== null && real.length > 1 && <> · avg {Number(avg.toFixed(4))} ms / {real.length}</>}
          </div>
        </div>
        <button onClick={close} className="px-1 text-lg leading-none" style={{ color: 'var(--d-muted)' }} aria-label="Close inspector">✕</button>
      </header>

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 overflow-y-auto p-4 md:grid-cols-2">
        <section className="min-w-0">
          <div className="mb-2 flex items-center justify-between">
            <h4 className="text-[10px] font-semibold uppercase tracking-widest" style={{ color: 'var(--d-muted)' }}>Cypher</h4>
            <button onClick={copy} className="rounded border px-2 py-0.5 text-[10px]" style={{ borderColor: 'var(--d-border)', color: 'var(--d-muted)' }}>{copied ? 'copied' : 'copy'}</button>
          </div>
          {trace.cypher ? <CypherView source={trace.cypher} /> : <p className="cy-block" style={{ color: 'var(--d-muted)' }}>This reaction carried no Cypher (graph_trace.cypher empty).</p>}
        </section>
        <section className="min-w-0">
          <h4 className="mb-2 text-[10px] font-semibold uppercase tracking-widest" style={{ color: 'var(--d-muted)' }}>Returned sub-graph</h4>
          <div className="rounded-xl border p-2" style={{ borderColor: 'var(--d-border)' }}>
            {trace.nodes.length ? <SubgraphView key={entry.at} trace={trace} /> : <p className="p-4 text-xs" style={{ color: 'var(--d-muted)' }}>No sub-graph returned with this reaction.</p>}
          </div>
        </section>
      </div>

      {history.length > 1 && (
        <footer className="flex items-center gap-1.5 overflow-x-auto border-t px-4 py-2" style={{ borderColor: 'var(--d-border)' }}>
          <span className="mr-1 text-[10px] uppercase tracking-wider" style={{ color: 'var(--d-muted)' }}>history</span>
          {history.slice(0, 10).map((h, i) => (
            <button
              key={h.at}
              onClick={() => setIdx(i)}
              className="shrink-0 rounded-full border px-2 py-0.5 font-mono text-[10px]"
              style={{ borderColor: i === idx ? 'var(--d-accent)' : 'var(--d-border)', color: i === idx ? 'var(--d-accent)' : 'var(--d-muted)' }}
            >{fmtMs(h.trace.query_ms)}</button>
          ))}
        </footer>
      )}
    </aside>
  );
}
