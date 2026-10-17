import { HTTP_BASE } from '../../api/config';
import { useStore } from '../../store/useStore';
import { GlassCard } from '../components/Glass';
import { DueList } from '../progress/DueList';
import { Heatmap } from '../progress/Heatmap';
import { HintChart } from '../progress/HintChart';
import { LessonsPanel } from '../progress/LessonsPanel';
import { MasteryBars } from '../progress/MasteryBars';
import { MistakesPanel } from '../progress/MistakesPanel';
import { SkillRadar } from '../progress/SkillRadar';
import { Timeline } from '../progress/Timeline';

export function ProgressPage() {
  const progress = useStore((s) => s.progress);
  const evo = useStore((s) => s.evolution);

  if (!progress) {
    return <div className="flex h-full items-center justify-center text-sm" style={{ color: 'var(--d-muted)' }}>Waiting for the daemon at {HTTP_BASE}…</div>;
  }
  const today = progress.daily_activity[progress.daily_activity.length - 1]?.count ?? 0;
  const total = progress.daily_activity.reduce((a, d) => a + d.count, 0);

  return (
    <div className="dash-scroll h-full p-5">
      <h2 className="mb-4 text-lg font-semibold">Progress</h2>
      <div className="grid gap-4 lg:grid-cols-12">
        <div className="lg:col-span-4 xl:col-span-3">
          <GlassCard title="Streak" className="h-full">
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-semibold">{progress.streak.current}</span>
              <span className="text-sm" style={{ color: 'var(--d-muted)' }}>day streak 🔥</span>
            </div>
            <dl className="mt-3 space-y-1 text-xs" style={{ color: 'var(--d-muted)' }}>
              <div className="flex justify-between"><dt>Best</dt><dd>{progress.streak.best} days</dd></div>
              <div className="flex justify-between"><dt>Today</dt><dd>{today} attempts</dd></div>
              <div className="flex justify-between"><dt>Last 17 weeks</dt><dd>{total} attempts</dd></div>
              {evo && <div className="flex justify-between"><dt>Pet</dt><dd>{evo.stage_name} · {Math.round(evo.progress * 100)}%</dd></div>}
            </dl>
          </GlassCard>
        </div>
        <div className="lg:col-span-8 xl:col-span-9">
          <GlassCard title="Daily activity" className="h-full"><Heatmap data={progress.daily_activity} /></GlassCard>
        </div>

        <div className="lg:col-span-5"><SkillRadar /></div>
        <div className="lg:col-span-7"><MasteryBars /></div>

        <div className="lg:col-span-6"><MistakesPanel /></div>
        <div className="lg:col-span-6"><HintChart /></div>

        <div className="lg:col-span-7"><LessonsPanel /></div>
        <div className="lg:col-span-5"><DueList /></div>

        <div className="lg:col-span-12"><Timeline /></div>
      </div>
    </div>
  );
}
