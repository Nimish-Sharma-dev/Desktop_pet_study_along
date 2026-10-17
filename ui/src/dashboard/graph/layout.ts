import type { GraphNode } from '../../types/contracts';

// Left-to-right layered layout: Student -> Attempt -> Mistake -> Concept.
// Positions are deterministic and stable (no physics), so streaming updates never make nodes jump.
export const COLUMN: Record<string, number> = { Student: 0, Attempt: 1, Mistake: 2, Concept: 3 };
const COL_X = [0, 320, 660, 1010, 1360];
const ROW: Record<string, number> = { Student: 80, Attempt: 72, Mistake: 112, Concept: 62 };
export const MAX_ATTEMPTS = 10;

export const colIndex = (label: string) => COLUMN[label] ?? 4;

const attemptOrder = (n: GraphNode): [number, number] => {
  const seq = Number(/(\d+)$/.exec(n.id)?.[1] ?? 0);
  const ts = typeof n.props.ts === 'number' ? n.props.ts : 0;
  return [ts, seq];
};

export interface Layout { pos: Map<string, { x: number; y: number }>; visible: Set<string> }

export function computeLayout(nodes: GraphNode[], keep: Set<string>): Layout {
  const by: Record<string, GraphNode[]> = {};
  for (const n of nodes) (by[n.label] ??= []).push(n);

  const attempts = (by.Attempt ?? []).sort((a, b) => {
    const [ta, sa] = attemptOrder(a), [tb, sb] = attemptOrder(b);
    return ta - tb || sa - sb;
  });
  const recent = new Set(attempts.slice(-MAX_ATTEMPTS).map((n) => n.id));
  const shownAttempts = attempts.filter((n) => recent.has(n.id) || keep.has(n.id));

  const concepts = (by.Concept ?? []).sort((a, b) =>
    String(a.props.track ?? '').localeCompare(String(b.props.track ?? '')) || a.id.localeCompare(b.id));
  const mistakes = (by.Mistake ?? []).sort((a, b) => a.id.localeCompare(b.id));
  const students = by.Student ?? [];
  const others = Object.keys(by).filter((k) => !(k in COLUMN)).flatMap((k) => by[k].sort((a, b) => a.id.localeCompare(b.id)));

  const H = Math.max(concepts.length * ROW.Concept, Math.max(shownAttempts.length, MAX_ATTEMPTS) * ROW.Attempt, mistakes.length * ROW.Mistake, 400);
  const pos = new Map<string, { x: number; y: number }>();
  const visible = new Set<string>();
  const put = (list: GraphNode[], x: number, row: number, startY: number) =>
    list.forEach((n, i) => { pos.set(n.id, { x, y: startY + i * row }); visible.add(n.id); });

  put(students, COL_X[0], ROW.Student, H / 2 - 30);
  put(shownAttempts, COL_X[1], ROW.Attempt, (H - MAX_ATTEMPTS * ROW.Attempt) / 2); // top-aligned, fixed start
  put(mistakes, COL_X[2], ROW.Mistake, (H - mistakes.length * ROW.Mistake) / 2);
  put(concepts, COL_X[3], ROW.Concept, (H - concepts.length * ROW.Concept) / 2);
  put(others, COL_X[4], ROW.Concept, (H - others.length * ROW.Concept) / 2);
  return { pos, visible };
}
