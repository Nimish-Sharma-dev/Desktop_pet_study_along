import { useStore } from '../../store/useStore';
import { GlassCard } from '../components/Glass';
import { humanize } from '../util';

const ORDER = { in_progress: 0, not_started: 1, done: 2 } as const;
const ICON = { in_progress: '◐', not_started: '○', done: '●' } as const;

export function LessonsPanel() {
  const progress = useStore((s) => s.progress);
  const lessons = [...(progress?.lessons ?? [])].sort((a, b) => ORDER[a.status] - ORDER[b.status]);
  const next = progress?.recommended_next;
  const nextLesson = lessons.find((l) => l.id === next?.lesson_id);

  return (
    <GlassCard title="Lessons">
      {next && (
        <div className="mb-3 rounded-xl border p-3" style={{ borderColor: 'var(--d-accent)', boxShadow: 'var(--d-glow)' }}>
          <div className="text-[10px] uppercase tracking-wider" style={{ color: 'var(--d-accent)' }}>Recommended next</div>
          <div className="mt-0.5 text-sm font-medium">{nextLesson?.title ?? humanize(next.lesson_id)}</div>
          <div className="text-xs" style={{ color: 'var(--d-muted)' }}>{next.reason}</div>
        </div>
      )}
      <ul className="space-y-2.5">
        {lessons.map((l) => (
          <li key={l.id}>
            <div className="mb-1 flex items-center justify-between text-xs">
              <span className="flex items-center gap-2">
                <span style={{ color: l.status === 'done' ? '#4ade80' : 'var(--d-accent)' }}>{ICON[l.status]}</span>
                {l.title}
                <span className="rounded-full bg-white/10 px-1.5 text-[9px]" style={{ color: 'var(--d-muted)' }}>{humanize(l.track)}</span>
              </span>
              <span style={{ color: 'var(--d-muted)' }}>{Math.round(l.progress * 100)}%</span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
              <div className="h-full rounded-full transition-[width] duration-700" style={{ width: `${l.progress * 100}%`, background: l.status === 'done' ? '#4ade80' : 'var(--d-accent)' }} />
            </div>
          </li>
        ))}
      </ul>
    </GlassCard>
  );
}
