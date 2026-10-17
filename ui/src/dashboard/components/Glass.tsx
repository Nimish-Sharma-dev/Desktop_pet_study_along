import type { ReactNode } from 'react';

export function GlassCard({ title, right, children, className = '' }: {
  title?: string; right?: ReactNode; children: ReactNode; className?: string;
}) {
  return (
    <section className={`glass-card p-4 ${className}`}>
      {(title || right) && (
        <header className="mb-3 flex items-center justify-between">
          {title && <h3 className="text-xs font-semibold uppercase tracking-wider" style={{ color: 'var(--d-muted)' }}>{title}</h3>}
          {right}
        </header>
      )}
      {children}
    </section>
  );
}
