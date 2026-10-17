import { useStore } from '../../store/useStore';
import { GlassCard } from '../components/Glass';
import { ago, humanize } from '../util';

const KIND_STYLE: Record<string, string> = {
  recurring: 'bg-warn/20 text-warn',
  guess_spam: 'bg-amber-400/20 text-amber-300',
  pattern: 'bg-accent/20 text-accent',
};

export function MistakesPanel() {
  const progress = useStore((s) => s.progress);
  const recent = [...(progress?.recent_mistakes ?? [])].sort((a, b) => b.count - a.count);
  const patterns = progress?.patterns ?? [];

  return (
    <GlassCard title="Recent mistakes & patterns">
      <ul className="space-y-2">
        {recent.map((m) => (
          <li key={m.mistake_id} className="flex items-start justify-between gap-3 rounded-lg border px-3 py-2" style={{ borderColor: 'var(--d-border)' }}>
            <div className="min-w-0">
              <div className="text-sm capitalize">{humanize(m.mistake_id)}</div>
              <div className="mt-1 flex flex-wrap gap-1">
                {m.concept_ids.map((c) => (
                  <span key={c} className="rounded-full bg-white/10 px-1.5 py-0.5 text-[10px]" style={{ color: 'var(--d-muted)' }}>{humanize(c)}</span>
                ))}
              </div>
            </div>
            <div className="shrink-0 text-right">
              <div className="text-sm font-semibold">×{m.count}</div>
              <div className="text-[10px]" style={{ color: 'var(--d-muted)' }}>{ago(m.last_seen)}</div>
            </div>
          </li>
        ))}
        {!recent.length && <li className="text-xs" style={{ color: 'var(--d-muted)' }}>No mistakes recorded yet.</li>}
      </ul>
      {patterns.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2 border-t pt-3" style={{ borderColor: 'var(--d-border)' }}>
          {patterns.map((p) => (
            <span key={p.mistake_id + p.kind} className={`rounded-full px-2 py-1 text-[11px] ${KIND_STYLE[p.kind] ?? KIND_STYLE.pattern}`}>
              {humanize(p.kind)}: {humanize(p.mistake_id)} ×{p.count}
            </span>
          ))}
        </div>
      )}
    </GlassCard>
  );
}
