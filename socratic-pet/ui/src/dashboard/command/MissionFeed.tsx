import { useStore } from '../../store/useStore';
import { GlassCard } from '../components/Glass';
import { humanize } from '../util';

export function MissionFeed() {
  const bubble = useStore((s) => s.bubble);
  const events = useStore((s) => s.events);
  const q = bubble?.data;

  return (
    <GlassCard title="Mission feed">
      {q ? (
        <div className="mb-3 rounded border p-3" style={{ borderColor: 'var(--d-accent)', boxShadow: 'var(--d-glow)' }}>
          <div className="mb-1 flex items-center gap-2 text-[10px] tracking-widest" style={{ color: 'var(--d-accent)' }}>
            <span>TUTOR QUERY</span>
            <span className="flex gap-0.5">{[0, 1, 2, 3, 4].map((i) => (<span key={i} className="h-1.5 w-3" style={{ background: i <= q.hint_level ? 'var(--d-accent)' : 'rgba(255,255,255,0.1)' }} />))}</span>
          </div>
          <p className="text-sm leading-snug">{q.question}</p>
          <p className="mt-1 text-[10px]" style={{ color: 'var(--d-muted)' }}>target: {humanize(q.targets_concept)}</p>
        </div>
      ) : <p className="mb-3 text-xs" style={{ color: 'var(--d-muted)' }}>No tutor queries yet.</p>}
      <ul className="space-y-1 font-mono text-[11px]">
        {events.slice(0, 7).map((e) => (
          <li key={e.id} className="truncate"><span style={{ color: 'var(--d-accent)' }}>{e.channel.padEnd(14, '\u00a0')}</span>{e.summary}</li>
        ))}
      </ul>
    </GlassCard>
  );
}
