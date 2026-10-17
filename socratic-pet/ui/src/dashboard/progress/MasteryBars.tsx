import { useMemo, useState } from 'react';
import { useStore } from '../../store/useStore';
import { GlassCard } from '../components/Glass';
import { humanize, masteryTone, WEAK } from '../util';

const LIMIT = 8;

export function MasteryBars({ fixedTrack }: { fixedTrack?: string } = {}) {
  const concepts = useStore((s) => s.progress?.concepts);
  const [pickedTrack, setTrack] = useState('all');
  const track = fixedTrack ?? pickedTrack;
  const [all, setAll] = useState(false);

  const tracks = useMemo(() => ['all', ...new Set((concepts ?? []).map((c) => c.track))], [concepts]);
  const rows = useMemo(
    () => (concepts ?? []).filter((c) => track === 'all' || c.track === track).sort((a, b) => a.mastery - b.mastery),
    [concepts, track],
  );
  const shown = all ? rows : rows.slice(0, LIMIT);

  return (
    <GlassCard
      title="Concept mastery · weakest first"
      right={!fixedTrack && (
        <div className="flex gap-1">
          {tracks.map((t) => (
            <button
              key={t}
              onClick={() => setTrack(t)}
              className="rounded-full border px-2 py-0.5 text-[10px]"
              style={{ borderColor: t === track ? 'var(--d-accent)' : 'var(--d-border)', color: t === track ? 'var(--d-accent)' : 'var(--d-muted)' }}
            >{humanize(t)}</button>
          ))}
        </div>
      )}
    >
      <ul className="space-y-2.5">
        {shown.map((c) => (
          <li key={c.id}>
            <div className="mb-1 flex justify-between text-xs">
              <span className="flex items-center gap-1.5">
                {c.name}
                {c.mastery < WEAK && <span className="rounded bg-warn/20 px-1 text-[9px] text-warn">weak</span>}
              </span>
              <span style={{ color: 'var(--d-muted)' }}>{Math.round(c.mastery * 100)}%</span>
            </div>
            <div className="h-2 overflow-hidden rounded-full bg-white/10">
              <div className="h-full rounded-full transition-[width] duration-700" style={{ width: `${c.mastery * 100}%`, background: masteryTone(c.mastery) }} />
            </div>
          </li>
        ))}
      </ul>
      {rows.length > LIMIT && (
        <button onClick={() => setAll(!all)} className="mt-3 text-[11px]" style={{ color: 'var(--d-accent)' }}>
          {all ? 'Show fewer' : `Show all ${rows.length}`}
        </button>
      )}
    </GlassCard>
  );
}
