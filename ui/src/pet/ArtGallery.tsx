// Dev-only: open http://localhost:1420/?gallery in a browser to inspect all 8 states.
import { useState } from 'react';
import { PET_STATES } from '../types/contracts';
import type { Variant } from './art/fallbackSvg';
import { PetSprite } from './PetSprite';

export function ArtGallery() {
  const [variant, setVariant] = useState<Variant>('blob');
  const [stage, setStage] = useState(1);
  const [force, setForce] = useState(false);
  const [repeat, setRepeat] = useState(0);
  const [hat, setHat] = useState(false);
  const btn = (active: boolean) => `rounded border px-2 py-1 ${active ? 'border-accent bg-accent/20' : 'border-white/10'}`;

  return (
    <div className="h-full overflow-auto bg-[#0b0d17] p-5 text-xs text-slate-200">
      <div className="mb-4 flex flex-wrap items-center gap-2">
        {(['blob', 'wizard', 'dragon'] as Variant[]).map((v) => (
          <button key={v} className={btn(variant === v)} onClick={() => { setVariant(v); if (v === 'blob') setStage(1); else if (stage === 1) setStage(2); }}>{v}</button>
        ))}
        <span className="mx-2 opacity-40">|</span>
        {[1, 2, 3].map((s) => <button key={s} className={btn(stage === s)} onClick={() => setStage(s)}>stage {s}</button>)}
        <span className="mx-2 opacity-40">|</span>
        <label><input type="checkbox" checked={force} onChange={(e) => setForce(e.target.checked)} /> force fallback art</label>
        <label><input type="checkbox" checked={hat} onChange={(e) => setHat(e.target.checked)} /> hard hat</label>
        {[0, 2, 3].map((r) => <button key={r} className={btn(repeat === r)} onClick={() => setRepeat(r)}>repeat ×{r}</button>)}
      </div>
      <div className="grid grid-cols-2 gap-6 md:grid-cols-4">
        {PET_STATES.map((s) => (
          <div key={s} className="flex flex-col items-center gap-2 rounded-xl border border-white/10 p-3">
            <PetSprite state={s} variant={variant} stage={stage} repeat={repeat} hardHat={hat} forceFallback={force} showSource />
            <span>{s}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
