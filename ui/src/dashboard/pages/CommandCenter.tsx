import { MasteryBars } from '../progress/MasteryBars';
import { MissionFeed } from '../command/MissionFeed';
import { ReviewRadar } from '../command/ReviewRadar';

// System design mode: tactical command-center layout. Theme (darker, HUD brackets, mono) comes from
// the data-mode="system_design" CSS on the dashboard root.
export function CommandCenter() {
  return (
    <div className="dash-scroll hud-grid h-full p-5">
      <div className="mb-4 flex items-center gap-3">
        <h2 className="text-lg font-semibold tracking-widest">COMMAND CENTER</h2>
        <span className="hud-blink rounded border px-2 py-0.5 text-[10px] tracking-widest" style={{ borderColor: 'var(--d-accent)', color: 'var(--d-accent)' }}>● LIVE REVIEW</span>
      </div>
      <div className="grid gap-4 lg:grid-cols-12">
        <div className="lg:col-span-12"><ReviewRadar /></div>
        <div className="lg:col-span-7"><MissionFeed /></div>
        <div className="lg:col-span-5"><MasteryBars fixedTrack="system_design" /></div>
      </div>
    </div>
  );
}
