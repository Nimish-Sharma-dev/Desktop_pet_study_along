import { useStore } from '../../store/useStore';
import { GlassCard } from '../components/Glass';

export function DevFeed() {
  const events = useStore((s) => s.events);
  const trace = useStore((s) => s.inspector.trace);
  const petState = useStore((s) => s.petState);
  const nodeCount = useStore((s) => Object.keys(s.graph.nodes).length);
  const issues = useStore((s) => s.issues);
  const issueList = Object.entries(issues).sort((a, b) => b[1] - a[1]);

  return (
    <div className="dash-scroll h-full p-5">
      <h2 className="mb-1 text-lg font-semibold">Dev feed</h2>
      <p className="mb-4 text-xs" style={{ color: 'var(--d-muted)' }}>pet: {petState} · graph nodes: {nodeCount}</p>
      <GlassCard title={`Contract warnings (${issueList.length})`} className="mb-4">
        {issueList.length ? (
          <ul className="space-y-1 font-mono text-xs">
            {issueList.map(([msg, n]) => (<li key={msg}><span className="text-amber-300">×{n}</span> {msg}</li>))}
          </ul>
        ) : <p className="text-xs" style={{ color: 'var(--d-muted)' }}>None. Everything the daemon sent matches the contract.</p>}
      </GlassCard>
      <div className="grid gap-4 md:grid-cols-2">
        <GlassCard title="Events">
          <ul className="space-y-1 font-mono text-xs">
            {events.map((e) => (<li key={e.id}><span style={{ color: 'var(--d-accent)' }}>{e.channel}</span> {e.summary}</li>))}
          </ul>
        </GlassCard>
        <GlassCard title="Last graph_trace">
          {trace ? (
            <pre className="whitespace-pre-wrap font-mono text-xs">{trace.cypher}{'\n\n'}query_ms: {trace.query_ms} · {trace.nodes.length} nodes · {trace.edges.length} edges</pre>
          ) : <p className="text-xs" style={{ color: 'var(--d-muted)' }}>none yet</p>}
        </GlassCard>
      </div>
    </div>
  );
}
