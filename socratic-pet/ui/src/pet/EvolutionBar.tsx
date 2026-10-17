import type { EvolutionInfo } from '../types/contracts';

export function EvolutionBar({ evo }: { evo: EvolutionInfo }) {
  const pct = Math.round(evo.progress * 100);
  return (
    <div className="group w-44 text-center text-[10px] text-slate-300">
      <div className="mb-0.5 flex justify-between">
        <span>{evo.stage_name}</span>
        <span className="opacity-70">{evo.next_stage_name ? `→ ${evo.next_stage_name}` : 'max'}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
        <div className="h-full rounded-full bg-gradient-to-r from-accent to-accent2 transition-[width] duration-700" style={{ width: `${pct}%` }} />
      </div>
      <div className="mt-0.5 h-3 opacity-0 transition-opacity group-hover:opacity-100">
        {evo.next
          ? `streak ${evo.streak}/${evo.next.min_streak} · mastery ${evo.mastery_total.toFixed(1)}/${evo.next.min_mastery_total}`
          : `streak ${evo.streak} · mastery ${evo.mastery_total.toFixed(1)}`}
      </div>
    </div>
  );
}
