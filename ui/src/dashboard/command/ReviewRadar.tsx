import { PolarAngleAxis, PolarGrid, PolarRadiusAxis, Radar, RadarChart, ResponsiveContainer } from 'recharts';
import { useStore } from '../../store/useStore';
import { GlassCard } from '../components/Glass';
import { humanize } from '../util';

const grade = (pct: number) =>
  pct < 40 ? { t: 'CRITICAL', c: '#ff6b81' } : pct < 60 ? { t: 'WEAK', c: '#ffb454' } : pct < 80 ? { t: 'SOLID', c: '#33ff9c' } : { t: 'STRONG', c: '#7fffd4' };
const tone = (r: number) => (r < 0.4 ? '#ff6b81' : r < 0.65 ? '#ffb454' : '#33ff9c');

// Live design review: axes and scores come entirely from `review` messages (any rubric axes render).
export function ReviewRadar() {
  const review = useStore((s) => s.review);
  const prevMap = useStore((s) => s.reviewPrev);
  const activeId = useStore((s) => s.activeDesignId);
  const setActive = useStore((s) => s.setActiveDesign);

  const ids = Object.keys(review);
  const current = activeId ? review[activeId] : undefined;
  const prev = activeId ? prevMap[activeId] : undefined;

  if (!current) {
    return (
      <GlassCard title="Design review">
        <div className="hud-scan flex h-64 items-center justify-center text-xs tracking-widest" style={{ color: 'var(--d-muted)' }}>AWAITING DESIGN SUBMISSION…</div>
      </GlassCard>
    );
  }

  const prevScore = new Map((prev?.axes ?? []).map((a) => [a.id, a.score / a.max]));
  const data = current.axes.map((a) => ({
    axis: a.label,
    value: Math.round((a.score / a.max) * 100),
    before: prevScore.has(a.id) ? Math.round(prevScore.get(a.id)! * 100) : undefined,
  }));
  const total = current.axes.reduce((a, x) => a + x.score, 0);
  const max = current.axes.reduce((a, x) => a + x.max, 0);
  const pct = max ? Math.round((total / max) * 100) : 0;
  const g = grade(pct);

  return (
    <GlassCard
      title={`Design review // ${humanize(current.design_id)}`}
      right={ids.length > 1 && (
        <div className="flex gap-1">
          {ids.map((id) => (
            <button key={id} onClick={() => setActive(id)} className="rounded border px-2 py-0.5 text-[10px]" style={{ borderColor: id === activeId ? 'var(--d-accent)' : 'var(--d-border)', color: id === activeId ? 'var(--d-accent)' : 'var(--d-muted)' }}>{humanize(id)}</button>
          ))}
        </div>
      )}
    >
      <div className="grid gap-4 md:grid-cols-2">
        <div>
          <ResponsiveContainer width="100%" height={290}>
            <RadarChart data={data} outerRadius="70%">
              <PolarGrid stroke="var(--d-border)" />
              <PolarAngleAxis dataKey="axis" tick={{ fill: 'var(--d-muted)', fontSize: 11 }} />
              <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
              {prev && <Radar dataKey="before" stroke="var(--d-muted)" fill="none" strokeDasharray="4 4" strokeWidth={1.5} isAnimationActive={false} />}
              <Radar dataKey="value" stroke="var(--d-accent)" fill="var(--d-accent)" fillOpacity={0.3} strokeWidth={2.5} animationDuration={700} />
            </RadarChart>
          </ResponsiveContainer>
          {prev && <p className="text-center text-[10px]" style={{ color: 'var(--d-muted)' }}>dashed = previous review</p>}
        </div>

        <div className="flex flex-col">
          <div className="mb-3 flex items-end justify-between border-b pb-3" style={{ borderColor: 'var(--d-border)' }}>
            <div>
              <div className="text-[10px] tracking-widest" style={{ color: 'var(--d-muted)' }}>OVERALL</div>
              <div key={pct} className="flash text-4xl font-semibold" style={{ color: g.c }}>{pct}<span className="text-base opacity-60">/100</span></div>
            </div>
            <span className="rounded border px-2 py-1 text-[11px] tracking-widest" style={{ color: g.c, borderColor: g.c }}>{g.t}</span>
          </div>

          <ul className="space-y-2.5">
            {current.axes.map((a) => {
              const before = prev?.axes.find((x) => x.id === a.id);
              const delta = before ? a.score - before.score : 0;
              return (
                <li key={a.id}>
                  <div className="mb-1 flex items-center justify-between text-xs">
                    <span>{a.label}</span>
                    <span key={a.score} className="flash font-mono">
                      {a.score}/{a.max}
                      {delta !== 0 && <span className="ml-1.5" style={{ color: delta > 0 ? '#33ff9c' : '#ff6b81' }}>{delta > 0 ? '▲' : '▼'}{Math.abs(delta)}</span>}
                    </span>
                  </div>
                  <div className="h-1.5 overflow-hidden rounded-sm bg-white/10">
                    <div className="h-full transition-[width] duration-700" style={{ width: `${(a.score / a.max) * 100}%`, background: tone(a.score / a.max) }} />
                  </div>
                </li>
              );
            })}
          </ul>

          {!!current.notes?.length && (
            <ul className="mt-3 space-y-1 border-t pt-3 font-mono text-[11px]" style={{ borderColor: 'var(--d-border)', color: 'var(--d-muted)' }}>
              {current.notes.map((n, i) => (<li key={i}><span style={{ color: 'var(--d-accent)' }}>&gt;</span> {n}</li>))}
            </ul>
          )}
        </div>
      </div>
    </GlassCard>
  );
}
