import type { EvolutionInfo } from '../types/contracts';

// Fallback only: the daemon is the source of truth and may send `evolution` itself.
// If it does not, the UI derives the stage from streak + total concept mastery with these thresholds.
export const EVOLUTION_STAGES = [
  { stage: 1, name: 'Pixel Blob', min_streak: 0, min_mastery_total: 0 },
  { stage: 2, name: 'Apprentice', min_streak: 5, min_mastery_total: 6 }, // wizard | dragon variant
  { stage: 3, name: 'Master', min_streak: 14, min_mastery_total: 10 },
];

export function deriveEvolution(streak: number, concepts: { track: string; mastery: number }[]): EvolutionInfo {
  const total = concepts.reduce((a, c) => a + c.mastery, 0);
  let cur = EVOLUTION_STAGES[0];
  for (const s of EVOLUTION_STAGES) if (streak >= s.min_streak && total >= s.min_mastery_total) cur = s;
  const next = EVOLUTION_STAGES.find((s) => s.stage === cur.stage + 1) ?? null;
  const dsa = concepts.filter((c) => c.track === 'dsa').reduce((a, c) => a + c.mastery, 0);
  const progress = next
    ? Math.min(1, (Math.min(1, streak / next.min_streak) + Math.min(1, total / next.min_mastery_total)) / 2)
    : 1;
  return {
    stage: cur.stage,
    variant: cur.stage === 1 ? 'blob' : dsa >= total - dsa ? 'wizard' : 'dragon',
    stage_name: cur.name,
    next_stage_name: next?.name ?? null,
    progress: Number(progress.toFixed(3)),
    streak,
    mastery_total: Number(total.toFixed(2)),
    next: next ? { min_streak: next.min_streak, min_mastery_total: next.min_mastery_total } : null,
  };
}
