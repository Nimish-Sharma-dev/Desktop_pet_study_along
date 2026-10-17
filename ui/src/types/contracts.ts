// Module D types. Mirrors Contracts 4 + 5 and the additions in /docs/contracts.md.

export const PET_STATES = [
  'idle', 'curious', 'thinking', 'asking',
  'celebrating', 'sleeping', 'stressed', 'detective',
] as const;
export type PetState = (typeof PET_STATES)[number];

export type Mode = 'dsa' | 'system_design';

// ---------- Contract 4: tutor output ----------
export interface GraphNode {
  id: string;
  label: string; // Student | Attempt | Mistake | Concept | Lesson ...
  props: Record<string, unknown>;
}
export interface GraphEdge {
  from: string;
  to: string;
  type: string; // MADE | SHOWED | INVOLVES | RESOLVED | PREREQUISITE_OF ...
}
export interface GraphTrace {
  cypher: string;
  query_ms: number | null; // real measured value, shown as-is; null if the daemon sent none (UI shows n/a)
  nodes: GraphNode[];
  edges: GraphEdge[];
}
export interface TutorOutput {
  question: string;
  hint_level: 0 | 1 | 2 | 3 | 4;
  targets_concept: string;
  mistake_id: string;
  pet_state: PetState;
  graph_trace: GraphTrace;
}

// ---------- Contract 5: /ws/ui payloads ----------
export interface EvolutionInfo {
  stage: number;
  variant: 'blob' | 'wizard' | 'dragon';
  stage_name: string;
  next_stage_name: string | null;
  progress: number; // 0..1 toward next stage
  streak: number;
  mastery_total: number;
  next: { min_streak: number; min_mastery_total: number } | null;
}
export interface PetStatePayload { state: PetState; reason?: string }
export interface GraphUpdatePayload {
  nodes: GraphNode[]; // new or changed nodes (upsert)
  edges: GraphEdge[]; // new or changed edges (upsert)
  highlight: { node_ids: string[]; edges: GraphEdge[]; reason?: string };
}
export interface MasteryUpdatePayload {
  concept_id: string;
  mastery: number; // 0..1
  delta: number;
  evolution: EvolutionInfo | null; // optional from the daemon; derived client-side when absent
}
export interface ConfettiPayload { reason?: string; count?: number }
export interface ModePayload { mode: Mode }
export interface ReviewAxis { id: string; label: string; score: number; max: number }
export interface ReviewPayload { design_id: string; axes: ReviewAxis[]; notes?: string[] }

export type UiMessage =
  | { channel: 'pet_state'; payload: PetStatePayload }
  | { channel: 'bubble'; payload: TutorOutput }
  | { channel: 'graph_update'; payload: GraphUpdatePayload }
  | { channel: 'mastery_update'; payload: MasteryUpdatePayload }
  | { channel: 'confetti'; payload: ConfettiPayload }
  | { channel: 'mode'; payload: ModePayload }
  | { channel: 'review'; payload: ReviewPayload };

// ---------- REST: GET /api/progress ----------
export interface ConceptMastery { id: string; name: string; track: string; mastery: number }
export interface Progress {
  mode?: Mode; // optional: lets the UI start in the right mode without waiting for a `mode` message
  streak: { current: number; best: number };
  daily_activity: { date: string; count: number }[];
  skill_radar: Record<string, { axis: string; value: number }[]>; // per track
  concepts: ConceptMastery[];
  recent_mistakes: { mistake_id: string; count: number; last_seen: string; concept_ids: string[] }[];
  patterns: { mistake_id: string; kind: string; count: number }[];
  hint_dependency: { date: string; avg_hint_level: number }[];
  lessons: { id: string; title: string; track: string; status: 'not_started' | 'in_progress' | 'done'; progress: number }[];
  recommended_next: { lesson_id: string; reason: string } | null;
  spaced_repetition_due: { concept_id: string; due_at: string; interval_days: number }[];
  timeline: { ts: number; kind: string; label: string }[];
  evolution: EvolutionInfo;
}

export interface GraphSnapshot { nodes: GraphNode[]; edges: GraphEdge[] }
