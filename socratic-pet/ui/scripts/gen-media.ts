// Regenerates the sample placeholder art in public/media from the built-in fallback drawing.
//   npm run gen:media
// Layout produced:  media/{state}.svg (blob, generic)  media/wizard/  media/wizard-s3/  media/dragon/  media/dragon-s3/
import { mkdirSync, writeFileSync } from 'node:fs';
import { PET_STATES } from '../src/types/contracts';
import { fallbackSvg, type Variant } from '../src/pet/art/fallbackSvg';

const OUT = new URL('../public/media/', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1');
const sets: [string, Variant, number][] = [
  ['', 'blob', 1],
  ['wizard', 'wizard', 2], ['wizard-s3', 'wizard', 3],
  ['dragon', 'dragon', 2], ['dragon-s3', 'dragon', 3],
];
for (const [dir, variant, stage] of sets) {
  mkdirSync(OUT + dir, { recursive: true });
  for (const s of PET_STATES) writeFileSync(`${OUT}${dir ? dir + '/' : ''}${s}.svg`, fallbackSvg(s, variant, stage));
}
console.log('wrote', sets.length * PET_STATES.length, 'files to', OUT);
