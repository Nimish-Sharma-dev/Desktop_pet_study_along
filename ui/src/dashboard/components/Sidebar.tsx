import type { Mode } from '../../types/contracts';

export type Page = 'command' | 'progress' | 'graph' | 'dev';

const ITEMS: { id: Page; label: string; icon: string; dev?: boolean; only?: Mode }[] = [
  { id: 'command', label: 'Command center', icon: '▦', only: 'system_design' },
  { id: 'progress', label: 'Progress', icon: '◔' },
  { id: 'graph', label: 'Live Graph', icon: '⬡' },
  { id: 'dev', label: 'Dev feed', icon: '›_', dev: true },
];

export function Sidebar({ page, mode, onChange }: { page: Page; mode: Mode; onChange: (p: Page) => void }) {
  return (
    <nav className="flex w-48 shrink-0 flex-col gap-1 border-r p-3" style={{ borderColor: 'var(--d-border)' }}>
      {ITEMS.filter((it) => !it.only || it.only === mode).map((it) => {
        const active = page === it.id;
        return (
          <button
            key={it.id}
            onClick={() => onChange(it.id)}
            className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-left text-sm transition-colors ${it.dev ? 'mt-auto text-xs' : ''}`}
            style={{
              background: active ? 'var(--d-panel)' : 'transparent',
              border: `1px solid ${active ? 'var(--d-border)' : 'transparent'}`,
              color: active ? 'var(--d-accent)' : 'var(--d-muted)',
              boxShadow: active ? 'var(--d-glow)' : 'none',
            }}
          >
            <span className="w-4 text-center">{it.icon}</span>
            {it.label}
          </button>
        );
      })}
    </nav>
  );
}
