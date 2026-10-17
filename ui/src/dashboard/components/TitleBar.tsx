import { windowControls, isTauri } from '../../lib/tauri';
import { useStore } from '../../store/useStore';

function Toggle({ on, onChange, label }: { on: boolean; onChange: (v: boolean) => void; label: string }) {
  return (
    <button
      onClick={() => onChange(!on)}
      title="Developer: show the FalkorDB inspector drawer on every pet reaction"
      className="flex items-center gap-2 rounded-full border px-2.5 py-1 text-[11px] transition-colors"
      style={{ borderColor: on ? 'var(--d-accent)' : 'var(--d-border)', color: on ? 'var(--d-accent)' : 'var(--d-muted)' }}
    >
      <span className="relative inline-block h-3.5 w-6 rounded-full" style={{ background: on ? 'var(--d-accent)' : 'rgba(255,255,255,0.15)' }}>
        <span className="absolute top-0.5 h-2.5 w-2.5 rounded-full bg-[#0b0d17] transition-all" style={{ left: on ? 12 : 2 }} />
      </span>
      {label}
    </button>
  );
}

const winBtn = 'flex h-7 w-9 items-center justify-center text-xs hover:bg-white/10';

export function TitleBar() {
  const connected = useStore((s) => s.connected);
  const mode = useStore((s) => s.mode);
  const inspectorOn = useStore((s) => s.inspector.enabled);
  const setInspector = useStore((s) => s.setInspectorEnabled);
  const issues = useStore((s) => s.issues);
  const issueKeys = Object.keys(issues);

  return (
    <header
      data-tauri-drag-region
      className="flex h-11 shrink-0 select-none items-center justify-between border-b px-3"
      style={{ borderColor: 'var(--d-border)' }}
    >
      <div data-tauri-drag-region className="flex items-center gap-3">
        <span className="text-sm font-semibold tracking-wide">Tutor Pet</span>
        <span
          className="rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-wider"
          style={{ borderColor: 'var(--d-border)', color: 'var(--d-accent)' }}
        >
          {mode === 'dsa' ? 'DSA' : 'System design'}
        </span>
      </div>
      <div className="flex items-center gap-3">
        {issueKeys.length > 0 && (
          <span className="rounded-full bg-amber-400/20 px-2 py-0.5 text-[10px] text-amber-300" title={issueKeys.slice(0, 6).join('\n')}>⚠ {issueKeys.length} contract warning{issueKeys.length === 1 ? '' : 's'} (see Dev feed)</span>
        )}
        <span className="flex items-center gap-1.5 text-[11px]" style={{ color: 'var(--d-muted)' }}>
          <span className={`h-1.5 w-1.5 rounded-full ${connected ? 'bg-ok' : 'bg-warn'}`} />
          {connected ? 'daemon live' : 'offline'}
        </span>
        <Toggle on={inspectorOn} onChange={(v) => void setInspector(v)} label="Inspector" />
        {isTauri && (
          <div className="-mr-3 flex">
            <button className={winBtn} onClick={windowControls.minimize} aria-label="Minimize">–</button>
            <button className={winBtn} onClick={windowControls.toggleMaximize} aria-label="Maximize">▢</button>
            <button className={`${winBtn} hover:!bg-warn/70`} onClick={windowControls.close} aria-label="Close">✕</button>
          </div>
        )}
      </div>
    </header>
  );
}
