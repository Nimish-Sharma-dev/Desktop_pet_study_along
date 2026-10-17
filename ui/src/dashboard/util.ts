import { toMs } from '../api/normalize';

export const humanize = (id: string) => id.replace(/[_-]/g, ' ');


export function ago(ts: number | string): string {
  const t = typeof ts === 'string' ? Date.parse(ts) : toMs(ts);
  const s = Math.max(0, (Date.now() - t) / 1000);
  if (s < 60) return 'just now';
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}

export function dueLabel(iso: string): { text: string; overdue: boolean } {
  const d = (Date.parse(iso) - Date.now()) / 86400000;
  if (d < -1) return { text: `overdue ${Math.round(-d)}d`, overdue: true };
  if (d < 0) return { text: 'overdue', overdue: true };
  if (d < 1) return { text: 'due today', overdue: false };
  return { text: `in ${Math.round(d)}d`, overdue: false };
}

export const WEAK = 0.4;
export const masteryTone = (m: number) => (m < WEAK ? '#ff6b81' : m < 0.7 ? 'var(--d-accent)' : '#4ade80');
