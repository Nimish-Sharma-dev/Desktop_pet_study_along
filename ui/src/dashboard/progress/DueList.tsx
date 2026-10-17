import { useStore } from '../../store/useStore';
import { GlassCard } from '../components/Glass';
import { dueLabel } from '../util';

export function DueList() {
  const progress = useStore((s) => s.progress);
  const due = [...(progress?.spaced_repetition_due ?? [])].sort((a, b) => Date.parse(a.due_at) - Date.parse(b.due_at));
  const names = new Map((progress?.concepts ?? []).map((c) => [c.id, c.name]));

  return (
    <GlassCard title="Spaced repetition due">
      <ul className="space-y-2">
        {due.map((d) => {
          const l = dueLabel(d.due_at);
          return (
            <li key={d.concept_id} className="flex items-center justify-between rounded-lg border px-3 py-2 text-sm" style={{ borderColor: 'var(--d-border)' }}>
              <span>{names.get(d.concept_id) ?? d.concept_id}</span>
              <span className="text-right text-[11px]">
                <span className={l.overdue ? 'text-warn' : ''}>{l.text}</span>
                <span className="block" style={{ color: 'var(--d-muted)' }}>every {d.interval_days}d</span>
              </span>
            </li>
          );
        })}
        {!due.length && <li className="text-xs" style={{ color: 'var(--d-muted)' }}>Nothing due. Nice.</li>}
      </ul>
    </GlassCard>
  );
}
