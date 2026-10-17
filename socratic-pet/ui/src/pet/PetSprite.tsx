import type { PetState } from '../types/contracts';
import { fallbackSvg, svgDataUri, type Variant } from './art/fallbackSvg';
import { useArt } from './art/useArt';
import { GlassesOverlay, HardHatOverlay } from './Overlays';

interface Props {
  state: PetState;
  variant: Variant;
  stage: number;
  repeat?: number;        // consecutive times the same mistake came up
  hardHat?: boolean;      // system design mode
  evolving?: boolean;
  forceFallback?: boolean;
  showSource?: boolean;
  size?: number;
}

// Same mistake 3+ times => stressed look, whatever the daemon's pet_state says
// (unless the pet is mid-celebration/thinking/sleeping).
const KEEP = new Set<PetState>(['celebrating', 'thinking', 'sleeping']);

export function PetSprite({ state, variant, stage, repeat = 0, hardHat = false, evolving = false, forceFallback = false, showSource = false, size = 160 }: Props) {
  const visual: PetState = repeat >= 3 && !KEEP.has(state) ? 'stressed' : state;
  const { url, source } = useArt(variant, stage, visual, forceFallback);
  const src = url ?? svgDataUri(fallbackSvg(visual, variant, stage));
  const glasses = (repeat === 2 && visual !== 'stressed') || visual === 'detective';

  return (
    <div className={`relative ${evolving ? 'pet-evolve' : ''}`} style={{ width: size, height: size }}>
      <div className={`absolute inset-0 pet-anim-${visual}`}>
        <img
          src={src}
          alt={visual}
          draggable={false}
          className={`h-full w-full select-none ${url ? '' : '[image-rendering:pixelated]'}`}
        />
        {glasses && <GlassesOverlay />}
        {hardHat && <HardHatOverlay />}
      </div>
      {showSource && (
        <span className={`absolute -bottom-1 right-0 rounded px-1 text-[9px] ${source === 'file' ? 'bg-ok/80 text-black' : 'bg-warn/80 text-black'}`}>
          {source}
        </span>
      )}
    </div>
  );
}
