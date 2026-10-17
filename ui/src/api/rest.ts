import { HTTP_BASE } from './config';
import type { GraphSnapshot, Progress, ReviewPayload } from '../types/contracts';
import { parseGraph, parseProgress, parseReview } from './normalize';

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(HTTP_BASE + path, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
  });
  if (!res.ok) throw new Error(`${init?.method ?? 'GET'} ${path} -> ${res.status}`);
  return (await res.json()) as T;
}
const post = <T = unknown>(path: string, body?: unknown) =>
  req<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) });

export const api = {
  progress: (): Promise<Progress> => req<unknown>('/api/progress').then(parseProgress),
  graph: (): Promise<GraphSnapshot> => req<unknown>('/api/graph').then(parseGraph),
  review: (designId?: string) =>
    req<unknown>('/api/review' + (designId ? `?design_id=${encodeURIComponent(designId)}` : '')).then(parseReview) as Promise<ReviewPayload | null>,
  reply: (text: string) => post('/api/reply', { text }),
  voiceStart: () => post('/api/voice/start'),
  voiceStop: () => post('/api/voice/stop'),
  inspector: (enabled: boolean) => post<{ enabled: boolean }>('/api/inspector', { enabled }),
};
