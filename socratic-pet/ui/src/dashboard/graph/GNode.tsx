import { Handle, Position, type Node, type NodeProps } from '@xyflow/react';
import { masteryTone } from '../util';

export type GNodeData = {
  kind: string;
  title: string;
  subtitle?: string;
  mastery?: number;
  weak: boolean;
  lit: boolean;
  delay: number; // ms, staggers the light-up along the path
  passed?: boolean;
  [key: string]: unknown;
};
export type GFlowNode = Node<GNodeData, 'gnode'>;

const KIND_COLOR: Record<string, string> = {
  Student: '#b388ff', Attempt: '#7fd4ff', Mistake: '#ff6b81', Concept: '#7c9cff',
};
const KIND_ICON: Record<string, string> = { Student: '◉', Attempt: '▶', Mistake: '✕', Concept: '⬡' };

export function GNode({ data, selected }: NodeProps<GFlowNode>) {
  const color = data.passed ? '#4ade80' : KIND_COLOR[data.kind] ?? '#8b93b0';
  return (
    <div
      className={`gnode ${data.lit ? 'gnode-lit' : ''} ${data.weak ? 'gnode-weak' : ''} ${selected ? 'gnode-selected' : ''}`}
      style={{ ['--c' as string]: color, ['--delay' as string]: `${data.delay}ms` }}
    >
      <Handle type="target" position={Position.Left} id="in" className="gh" />
      <Handle type="source" position={Position.Right} id="out" className="gh" />
      <Handle type="source" position={Position.Right} id="ps" className="gh" />
      <Handle type="target" position={Position.Right} id="pt" className="gh" />
      <div className="flex items-center gap-2">
        <span className="text-xs" style={{ color }}>{KIND_ICON[data.kind] ?? '●'}</span>
        <div className="min-w-0">
          <div className="truncate text-xs font-medium">{data.title}</div>
          {data.subtitle && <div className="truncate text-[10px] opacity-60">{data.subtitle}</div>}
        </div>
      </div>
      {data.mastery !== undefined && (
        <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-white/10">
          <div className="h-full rounded-full" style={{ width: `${data.mastery * 100}%`, background: masteryTone(data.mastery) }} />
        </div>
      )}
    </div>
  );
}
