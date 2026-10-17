// Mood overlays drawn above any art (file or fallback). Coordinates are in the same 200x200
// grid as the fallback art; nudge the constants if real art puts the face elsewhere.
export function GlassesOverlay() {
  return (
    <svg viewBox="0 0 200 200" className="pointer-events-none absolute inset-0 h-full w-full">
      <g fill="rgba(180,210,255,0.18)" stroke="#e6e9f5" strokeWidth="3.5">
        <circle cx="70" cy="112" r="15" />
        <circle cx="130" cy="112" r="15" />
      </g>
      <g stroke="#e6e9f5" strokeWidth="3.5" strokeLinecap="round">
        <line x1="85" y1="112" x2="115" y2="112" />
        <line x1="55" y1="110" x2="38" y2="104" />
        <line x1="145" y1="110" x2="162" y2="104" />
      </g>
    </svg>
  );
}

export function HardHatOverlay() {
  return (
    <svg viewBox="0 0 200 200" className="pointer-events-none absolute inset-0 h-full w-full">
      <path d="M58 64 Q100 8 142 64 Z" fill="#ffc83d" stroke="#c98f00" strokeWidth="3" />
      <rect x="48" y="62" width="104" height="9" rx="3" fill="#ffd966" stroke="#c98f00" strokeWidth="3" />
      <rect x="93" y="30" width="14" height="30" fill="#ffd966" stroke="#c98f00" strokeWidth="2" />
    </svg>
  );
}
