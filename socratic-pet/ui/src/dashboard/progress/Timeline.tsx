import { useStore } from '../../store/useStore';
import { GlassCard } from '../components/Glass';
import { ago } from '../util';

const KIND: Record<string, { color: string; icon: string }> = {
  hint: { color: '#7c9cff', icon: '?' },
  pass: { color: '#4ade80', icon: '✓' },
  design: { color: '#33ff9c', icon: '▦' },
  evolve: { color: '#ffd666', icon: '★' },
  start: { color: '#8b93b0', icon: '•' },
};

export function Timeline() {
  const items = useStore((s) => s.progress?.timeline) ?? [];
  return (
    <GlassCard title="Session timeline">
      <ol className="relative space-y-3 border-l pl-5" style={{ borderColor: 'var(--d-border)' }}>
        {items.slice(0, 12).map((t, i) => {
          const k = KIND[t.kind] ?? KIND.start;
          return (
            <li key={`${t.ts}-${i}`} className="relative text-sm">
              <span className="absolute -left-[27px] flex h-4 w-4 items-center justify-center rounded-full text-[9px] font-bold text-[#0b0d17]" style={{ background: k.color }}>{k.icon}</span>
              {t.label}
              <span className="ml-2 text-[11px]" style={{ color: 'var(--d-muted)' }}>{ago(t.ts)}</span>
            </li>
          );
        })}
      </ol>
    </GlassCard>
  );
}
