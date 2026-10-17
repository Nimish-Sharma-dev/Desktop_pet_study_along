// Defensive parsing of everything the daemon sends. The daemon is built by other people; a missing
// field or a slightly different shape must never crash the UI. Every deviation is recorded as a
// "contract warning" (shown in Dev feed, and by `npm run check:daemon`). Nothing is invented:
// a missing query_ms stays null and renders as n/a.
import { deriveEvolution } from '../config/evolution';
import {
  PET_STATES, type EvolutionInfo, type GraphEdge, type GraphNode, type GraphSnapshot, type GraphTrace,
  type Mode, type PetState, type Progress, type ReviewPayload, type TutorOutput, type UiMessage,
} from '../types/contracts';

type Rec = Record<string, unknown>;
type Issues = string[];

let sink: ((issues: string[]) => void) | null = null;
export const setIssueSink = (fn: ((issues: string[]) => void) | null) => { sink = fn; };
const report = (issues: Issues) => { if (issues.length) sink?.(issues); };

const isRec = (v: unknown): v is Rec => typeof v === 'object' && v !== null && !Array.isArray(v);
const str = (v: unknown, d = ''): string => (typeof v === 'string' ? v : typeof v === 'number' ? String(v) : d);
const num = (v: unknown, d = 0): number => (typeof v === 'number' && Number.isFinite(v) ? v : d);
const arr = (v: unknown): unknown[] => (Array.isArray(v) ? v : []);
const humanize = (s: string) => s.replace(/[_-]/g, ' ');
const clamp01 = (v: number) => Math.min(1, Math.max(0, v));
/** Scores may arrive as 0..1 or as percentages (0..100). */
const unit = (v: unknown) => { const n = num(v); return clamp01(n > 1 && n <= 100 ? n / 100 : n); };
/** Epoch seconds (Contract 1 style) or milliseconds -> milliseconds. */
export const toMs = (ts: number) => (ts < 1e12 ? ts * 1000 : ts);
const iso = (v: unknown): string => (typeof v === 'number' ? new Date(toMs(v)).toISOString() : str(v, new Date().toISOString()));

const LABELS = ['Student', 'Attempt', 'Mistake', 'Concept', 'Lesson'];
export const canonicalLabel = (l: string) => LABELS.find((x) => x.toLowerCase() === l.toLowerCase()) ?? l;

// ---------- graph primitives ----------
function normNode(v: unknown, issues: Issues): GraphNode | null {
  if (!isRec(v)) { issues.push('graph: node is not an object'); return null; }
  const id = str(v.id);
  if (!id) { issues.push('graph: node without id'); return null; }
  const props = isRec(v.props) ? v.props : isRec(v.properties) ? v.properties : {};
  const label = str(v.label ?? (Array.isArray(v.labels) ? v.labels[0] : undefined), 'Node');
  return { id, label: canonicalLabel(label), props };
}

function normEdge(v: unknown, issues: Issues): GraphEdge | null {
  if (!isRec(v)) { issues.push('graph: edge is not an object'); return null; }
  const from = str(v.from ?? v.source ?? v.src ?? v.start);
  const to = str(v.to ?? v.target ?? v.dst ?? v.end);
  if (!from || !to) { issues.push('graph: edge without from/to'); return null; }
  return { from, to, type: str(v.type ?? v.rel ?? v.label, 'RELATED') };
}

const nodes = (v: unknown, issues: Issues) => arr(v).map((n) => normNode(n, issues)).filter((n): n is GraphNode => !!n);
const edges = (v: unknown, issues: Issues) => arr(v).map((e) => normEdge(e, issues)).filter((e): e is GraphEdge => !!e);

function normTrace(v: unknown, issues: Issues): GraphTrace {
  if (!isRec(v)) {
    issues.push('bubble: graph_trace missing (inspector will have nothing to show)');
    return { cypher: '', query_ms: null, nodes: [], edges: [] };
  }
  const q = v.query_ms;
  if (typeof q !== 'number' || !Number.isFinite(q)) issues.push('bubble: graph_trace.query_ms missing or not a number (shown as n/a)');
  return {
    cypher: str(v.cypher),
    query_ms: typeof q === 'number' && Number.isFinite(q) ? q : null,
    nodes: nodes(v.nodes, issues),
    edges: edges(v.edges, issues),
  };
}

function normEvolution(v: unknown): EvolutionInfo | null {
  if (!isRec(v) || typeof v.stage !== 'number') return null;
  const stage = Math.max(1, Math.round(v.stage));
  const variant = v.variant === 'wizard' || v.variant === 'dragon' || v.variant === 'blob' ? v.variant : stage === 1 ? 'blob' : 'wizard';
  const next = isRec(v.next) ? { min_streak: num(v.next.min_streak), min_mastery_total: num(v.next.min_mastery_total) } : null;
  return {
    stage, variant, stage_name: str(v.stage_name, `Stage ${stage}`),
    next_stage_name: v.next_stage_name == null ? null : str(v.next_stage_name),
    progress: clamp01(num(v.progress)), streak: num(v.streak), mastery_total: num(v.mastery_total), next,
  };
}

function normReview(p: Rec, issues: Issues): ReviewPayload {
  const axes = arr(p.axes).flatMap((a) => {
    if (!isRec(a)) return [];
    const label = str(a.label ?? a.id ?? a.name);
    const id = str(a.id ?? a.key ?? a.name ?? label);
    if (!id) return [];
    return [{ id, label: str(a.label, humanize(id)), score: num(a.score), max: num(a.max, 10) > 0 ? num(a.max, 10) : 10 }];
  });
  if (!axes.length) issues.push('review: no usable axes');
  return { design_id: str(p.design_id, 'design'), axes, notes: arr(p.notes).map((n) => str(n)).filter(Boolean) };
}

// ---------- /ws/ui ----------
export function parseUiMessage(raw: unknown): UiMessage | null {
  const issues: Issues = [];
  let out: UiMessage | null = null;

  if (!isRec(raw) || typeof raw.channel !== 'string') {
    issues.push('ws: message is not {channel, payload}');
  } else {
    const ch = raw.channel;
    const p: Rec = isRec(raw.payload) ? raw.payload : {};
    if (!isRec(raw.payload)) issues.push(`${ch}: payload missing or not an object`);

    switch (ch) {
      case 'pet_state': {
        const ok = PET_STATES.includes(p.state as PetState);
        if (!ok) issues.push(`pet_state: unknown state "${str(p.state)}" (using idle)`);
        out = { channel: ch, payload: { state: ok ? (p.state as PetState) : 'idle', reason: str(p.reason) || undefined } };
        break;
      }
      case 'bubble': {
        const ps = PET_STATES.includes(p.pet_state as PetState);
        if (!ps) issues.push(`bubble: unknown pet_state "${str(p.pet_state)}" (using asking)`);
        if (!str(p.question)) issues.push('bubble: question is empty');
        const payload: TutorOutput = {
          question: str(p.question),
          hint_level: Math.min(4, Math.max(0, Math.round(num(p.hint_level)))) as TutorOutput['hint_level'],
          targets_concept: str(p.targets_concept),
          mistake_id: str(p.mistake_id),
          pet_state: ps ? (p.pet_state as PetState) : 'asking',
          graph_trace: normTrace(p.graph_trace, issues),
        };
        out = { channel: ch, payload };
        break;
      }
      case 'graph_update': {
        const ns = nodes(p.nodes, issues), es = edges(p.edges, issues);
        const h = isRec(p.highlight) ? p.highlight : null;
        if (!h) issues.push('graph_update: no highlight (lighting everything in this update)');
        const hEdges = h ? edges(h.edges, issues) : es;
        const hIds = h && Array.isArray(h.node_ids) ? h.node_ids.map((x) => str(x)).filter(Boolean)
          : [...new Set([...ns.map((n) => n.id), ...hEdges.flatMap((e) => [e.from, e.to])])];
        out = { channel: ch, payload: { nodes: ns, edges: es, highlight: { node_ids: hIds, edges: hEdges, reason: h ? str(h.reason) || undefined : undefined } } };
        break;
      }
      case 'mastery_update': {
        const id = str(p.concept_id ?? p.concept ?? p.id);
        if (!id) issues.push('mastery_update: no concept_id');
        out = { channel: ch, payload: { concept_id: id, mastery: unit(p.mastery), delta: num(p.delta), evolution: normEvolution(p.evolution) } };
        break;
      }
      case 'confetti':
        out = { channel: ch, payload: { reason: str(p.reason) || undefined, count: typeof p.count === 'number' ? p.count : undefined } };
        break;
      case 'mode':
        if (p.mode === 'dsa' || p.mode === 'system_design') out = { channel: ch, payload: { mode: p.mode as Mode } };
        else issues.push(`mode: unknown mode "${str(p.mode)}" (ignored; expected dsa | system_design)`);
        break;
      case 'review':
        out = { channel: ch, payload: normReview(p, issues) };
        break;
      default:
        issues.push(`ws: unknown channel "${ch}" (ignored)`);
    }
  }
  report(issues);
  return out;
}

// ---------- REST ----------
export function parseGraph(raw: unknown): GraphSnapshot {
  const issues: Issues = [];
  const r: Rec = isRec(raw) ? raw : {};
  if (!isRec(raw)) issues.push('GET /api/graph: not an object');
  const snap = { nodes: nodes(r.nodes, issues), edges: edges(r.edges, issues) };
  report(issues);
  return snap;
}

export function parseReview(raw: unknown): ReviewPayload | null {
  if (!isRec(raw)) return null; // no review yet is normal
  const issues: Issues = [];
  const r = normReview(raw, issues);
  report(issues.map((i) => `GET /api/review: ${i}`));
  return r.axes.length ? r : null;
}

const STATUS = ['not_started', 'in_progress', 'done'] as const;

export function parseProgress(raw: unknown): Progress {
  const issues: Issues = [];
  if (!isRec(raw)) issues.push('GET /api/progress: not an object');
  const r: Rec = isRec(raw) ? raw : {};
  const miss = (k: string) => { if (!(k in r)) issues.push(`GET /api/progress: "${k}" missing (widget shows empty state)`); };
  ['streak', 'daily_activity', 'skill_radar', 'concepts', 'recent_mistakes', 'hint_dependency', 'lessons', 'spaced_repetition_due', 'timeline'].forEach(miss);

  const st = isRec(r.streak) ? r.streak : { current: r.streak };
  const concepts = arr(r.concepts).flatMap((c) => isRec(c) && str(c.id) ? [{ id: str(c.id), name: str(c.name, humanize(str(c.id))), track: str(c.track, 'dsa'), mastery: unit(c.mastery) }] : []);
  const streakCur = num(st.current);

  const skill_radar: Progress['skill_radar'] = {};
  if (isRec(r.skill_radar)) {
    for (const [track, axes] of Object.entries(r.skill_radar)) {
      skill_radar[track] = arr(axes).flatMap((a) => isRec(a) ? [{ axis: str(a.axis ?? a.label), value: unit(a.value) }] : []);
    }
  }

  const evolution = normEvolution(r.evolution) ?? deriveEvolution(streakCur, concepts);
  if (!isRec(r.evolution)) issues.push('GET /api/progress: "evolution" missing (derived from streak + mastery with default thresholds)');

  const progress: Progress = {
    mode: r.mode === 'dsa' || r.mode === 'system_design' ? r.mode : undefined,
    streak: { current: streakCur, best: num(st.best, streakCur) },
    daily_activity: arr(r.daily_activity).flatMap((d) => isRec(d) && str(d.date) ? [{ date: str(d.date).slice(0, 10), count: num(d.count) }] : [])
      .sort((a, b) => a.date.localeCompare(b.date)),
    skill_radar,
    concepts,
    recent_mistakes: arr(r.recent_mistakes).flatMap((m) => isRec(m) && str(m.mistake_id)
      ? [{ mistake_id: str(m.mistake_id), count: num(m.count, 1), last_seen: iso(m.last_seen), concept_ids: arr(m.concept_ids).map((c) => str(c)).filter(Boolean) }] : []),
    patterns: arr(r.patterns).flatMap((m) => isRec(m) && str(m.mistake_id) ? [{ mistake_id: str(m.mistake_id), kind: str(m.kind, 'pattern'), count: num(m.count, 1) }] : []),
    hint_dependency: arr(r.hint_dependency).flatMap((d) => isRec(d) && str(d.date) ? [{ date: str(d.date).slice(0, 10), avg_hint_level: Math.min(4, Math.max(0, num(d.avg_hint_level))) }] : []),
    lessons: arr(r.lessons).flatMap((l) => {
      if (!isRec(l) || !str(l.id)) return [];
      const progressV = unit(l.progress);
      const status = STATUS.includes(l.status as (typeof STATUS)[number]) ? (l.status as (typeof STATUS)[number]) : progressV >= 1 ? 'done' : progressV > 0 ? 'in_progress' : 'not_started';
      return [{ id: str(l.id), title: str(l.title, humanize(str(l.id))), track: str(l.track, 'dsa'), status, progress: progressV }];
    }),
    recommended_next: isRec(r.recommended_next) && str(r.recommended_next.lesson_id)
      ? { lesson_id: str(r.recommended_next.lesson_id), reason: str(r.recommended_next.reason) } : null,
    spaced_repetition_due: arr(r.spaced_repetition_due).flatMap((d) => isRec(d) && str(d.concept_id)
      ? [{ concept_id: str(d.concept_id), due_at: iso(d.due_at), interval_days: num(d.interval_days, 1) }] : []),
    timeline: arr(r.timeline).flatMap((t) => isRec(t) ? [{ ts: toMs(num(t.ts, Date.now())), kind: str(t.kind, 'event'), label: str(t.label) }] : [])
      .sort((a, b) => b.ts - a.ts),
    evolution,
  };
  report(issues);
  return progress;
}
