// Built-in placeholder art (pixel blob + wizard/dragon variants). Used whenever no file exists
// in /media. Also the single source for the generated sample files (scripts/gen-media.ts).
import type { PetState } from '../../types/contracts';

export type Variant = 'blob' | 'wizard' | 'dragon';

const U = 10; // 20x20 grid, 10px cells
const D = '#14182c';
const W = '#ffffff';
const rect = (x: number, y: number, w: number, h: number, fill: string) =>
  `<rect x="${x * U}" y="${y * U}" width="${w * U}" height="${h * U}" fill="${fill}"/>`;

const PALETTE: Record<Variant, { body: string; shade: string; hi: string }> = {
  blob: { body: '#7c9cff', shade: '#5a78d6', hi: '#b7c8ff' },
  wizard: { body: '#b388ff', shade: '#8a5fd6', hi: '#d9c2ff' },
  dragon: { body: '#4fd1a1', shade: '#34a37a', hi: '#9af0cc' },
};

// body rows 6..17 -> [x0, x1]
const SPANS: [number, number][] = [
  [7, 12], [5, 14], [4, 15], [3, 16], [3, 16], [3, 16], [3, 16], [3, 16], [4, 15], [4, 15], [5, 14], [6, 13],
];

function body(v: Variant): string {
  const p = PALETTE[v];
  let s = '';
  SPANS.forEach(([a, b], i) => { s += rect(a, 6 + i, b - a + 1, 1, i >= 8 ? p.shade : p.body); });
  return s + rect(5, 7, 2, 1, p.hi) + rect(4, 8, 1, 2, p.hi);
}

const eye = (x: number, y: number, w = 2, h = 2) => rect(x, y, w, h, D) + rect(x, y, 1, 1, W);

function face(state: PetState): string {
  switch (state) {
    case 'idle':
      return eye(6, 10) + eye(12, 10) + rect(9, 13, 2, 1, D);
    case 'curious':
      return eye(6, 9, 2, 3) + eye(12, 10) + rect(9, 13, 2, 1, D) + rect(12, 8, 2, 1, D);
    case 'thinking':
      return eye(6, 9) + eye(12, 9) + rect(10, 13, 1, 1, D)
        + rect(13, 3, 1, 1, '#e6e9f5') + rect(15, 2, 1, 1, '#e6e9f5') + rect(17, 1, 2, 2, '#e6e9f5');
    case 'asking':
      return eye(6, 10, 2, 3) + eye(12, 10, 2, 3) + rect(9, 14, 2, 2, D)
        + `<text x="148" y="46" font-size="44" font-weight="700" font-family="monospace" fill="#e6e9f5">?</text>`;
    case 'celebrating':
      return rect(6, 11, 1, 1, D) + rect(7, 10, 1, 1, D) + rect(8, 11, 1, 1, D)
        + rect(12, 11, 1, 1, D) + rect(13, 10, 1, 1, D) + rect(14, 11, 1, 1, D)
        + rect(8, 13, 4, 1, D) + rect(9, 14, 2, 1, D)
        + [[1, 4], [18, 3], [2, 12], [17, 11], [10, 1]].map(([x, y]) => rect(x, y, 1, 1, '#ffd666')).join('');
    case 'sleeping':
      return rect(6, 11, 2, 1, D) + rect(12, 11, 2, 1, D) + rect(10, 13, 1, 1, D)
        + `<text x="138" y="62" font-size="28" font-weight="700" font-family="monospace" fill="#e6e9f5">z</text>`
        + `<text x="158" y="34" font-size="38" font-weight="700" font-family="monospace" fill="#e6e9f5">Z</text>`;
    case 'stressed':
      return rect(5, 8, 3, 1, D) + rect(12, 8, 3, 1, D) + eye(6, 9, 2, 3) + eye(12, 9, 2, 3)
        + rect(8, 14, 1, 1, D) + rect(9, 13, 1, 1, D) + rect(10, 14, 1, 1, D) + rect(11, 13, 1, 1, D)
        + rect(16, 7, 1, 2, '#7fd4ff') + rect(15, 9, 3, 2, '#7fd4ff');
    case 'detective':
      return eye(6, 10) + eye(12, 10) + rect(5, 8, 3, 1, D) + rect(12, 8, 3, 1, D) + rect(9, 13, 2, 1, D);
  }
}

function extras(v: Variant, stage: number): { behind: string; front: string } {
  const p = PALETTE[v];
  if (v === 'wizard' && stage >= 2) {
    const hat = '#3b2f8f';
    let front = rect(5, 5, 10, 1, hat) + rect(7, 4, 6, 1, hat) + rect(8, 3, 4, 1, hat) + rect(9, 2, 2, 1, hat)
      + rect(9, 4, 1, 1, '#ffd666') + rect(11, 3, 1, 1, '#ffd666');
    let behind = '';
    if (stage >= 3) {
      front += rect(10, 1, 1, 1, hat) + rect(11, 0, 1, 1, hat) + rect(7, 3, 1, 1, '#ffd666') + rect(12, 4, 1, 1, '#ffd666');
      behind = rect(1, 7, 1, 11, '#8b5a2b') + rect(0, 6, 3, 1, '#ffd666') + rect(1, 5, 1, 1, '#ffd666');
    }
    return { behind, front };
  }
  if (v === 'dragon' && stage >= 2) {
    const horn = '#ffe7a8';
    let behind = rect(1, 9, 2, 3, p.shade) + rect(0, 8, 1, 2, p.shade) + rect(17, 9, 2, 3, p.shade) + rect(19, 8, 1, 2, p.shade)
      + rect(16, 16, 3, 1, p.body) + rect(18, 15, 1, 1, p.body);
    let front = rect(5, 4, 1, 2, horn) + rect(14, 4, 1, 2, horn) + rect(6, 5, 1, 1, horn) + rect(13, 5, 1, 1, horn);
    if (stage >= 3) {
      behind += rect(0, 10, 3, 3, p.shade) + rect(17, 10, 3, 3, p.shade) + rect(0, 7, 1, 1, p.shade) + rect(19, 7, 1, 1, p.shade);
      front += rect(8, 5, 1, 1, horn) + rect(10, 5, 1, 1, horn) + rect(12, 5, 1, 1, horn) + rect(5, 3, 1, 1, horn) + rect(14, 3, 1, 1, horn);
    }
    return { behind, front };
  }
  return { behind: '', front: '' };
}

export function fallbackSvg(state: PetState, variant: Variant = 'blob', stage = 1): string {
  const { behind, front } = extras(variant, stage);
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" shape-rendering="crispEdges">${behind}${body(variant)}${face(state)}${front}</svg>`;
}

export const svgDataUri = (svg: string) => `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
