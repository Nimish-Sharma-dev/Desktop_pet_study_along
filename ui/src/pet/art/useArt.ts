import { useEffect, useState } from 'react';
import { PET_STATES, type PetState } from '../../types/contracts';
import type { Variant } from './fallbackSvg';

// State name -> file. Lookup order (first file that loads wins):
//   /media/{variant}-s3/{state}.*   (stage 3 only)
//   /media/{variant}/{state}.*
//   /media/{state}.*                (generic)
// then the built-in SVG fallback. Extensions tried: png, webp, gif, svg.
const EXTS = ['png', 'webp', 'gif', 'svg'];

export function candidates(variant: Variant, stage: number, state: PetState): string[] {
  const dirs: string[] = [];
  if (stage >= 3) dirs.push(`/media/${variant}-s3`);
  dirs.push(`/media/${variant}`, '/media');
  return dirs.flatMap((d) => EXTS.map((e) => `${d}/${state}.${e}`));
}

const probeCache = new Map<string, Promise<boolean>>();
const resolved = new Map<string, string | null>();
const keyOf = (v: Variant, stage: number, s: PetState) => `${v}|${stage >= 3 ? 3 : stage}|${s}`;

function probe(url: string): Promise<boolean> {
  let p = probeCache.get(url);
  if (!p) {
    p = new Promise<boolean>((res) => {
      const img = new Image();
      img.onload = () => res(true);
      img.onerror = () => res(false);
      img.src = url;
    });
    probeCache.set(url, p);
  }
  return p;
}

export async function resolveArt(variant: Variant, stage: number, state: PetState): Promise<string | null> {
  const key = keyOf(variant, stage, state);
  if (resolved.has(key)) return resolved.get(key)!;
  for (const url of candidates(variant, stage, state)) {
    if (await probe(url)) { resolved.set(key, url); return url; }
  }
  resolved.set(key, null);
  return null;
}

export function preloadArt(variant: Variant, stage: number) {
  PET_STATES.forEach((s) => void resolveArt(variant, stage, s));
}

export function useArt(variant: Variant, stage: number, state: PetState, forceFallback = false) {
  const key = keyOf(variant, stage, state);
  const [, bump] = useState(0);
  useEffect(() => {
    if (forceFallback || resolved.has(key)) return;
    let alive = true;
    void resolveArt(variant, stage, state).then(() => { if (alive) bump((n) => n + 1); });
    return () => { alive = false; };
  }, [key, variant, stage, state, forceFallback]);
  const url = forceFallback ? null : resolved.get(key) ?? null;
  return { url, source: (url ? 'file' : 'fallback') as 'file' | 'fallback' };
}
