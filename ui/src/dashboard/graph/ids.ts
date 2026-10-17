import type { GraphNode } from '../../types/contracts';

/** Key that links a graph Concept node to /api/progress concepts. Tries explicit props first, then the id suffix. */
export function conceptKey(n: GraphNode): string {
  const p = n.props;
  for (const k of ['concept_id', 'key', 'slug', 'id']) {
    const v = p[k];
    if (typeof v === 'string' && v) return v;
  }
  const i = n.id.lastIndexOf(':');
  return i >= 0 ? n.id.slice(i + 1) : n.id;
}

export const nodeTitle = (n: GraphNode, humanize: (s: string) => string) =>
  String(n.props.name ?? n.props.title ?? humanize(n.id.replace(/^[A-Za-z]+:/, '')));
