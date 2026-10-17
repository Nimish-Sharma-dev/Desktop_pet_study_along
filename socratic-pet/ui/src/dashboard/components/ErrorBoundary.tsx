import { Component, type ReactNode } from 'react';

// A crash in one widget must not blank the whole dashboard.
export class ErrorBoundary extends Component<{ children: ReactNode; resetKey?: string }, { error: Error | null; key?: string }> {
  state: { error: Error | null; key?: string } = { error: null };
  static getDerivedStateFromError(error: Error) { return { error }; }
  static getDerivedStateFromProps(p: { resetKey?: string }, s: { key?: string; error: Error | null }) {
    return p.resetKey !== s.key ? { error: null, key: p.resetKey } : null;
  }
  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="m-5 rounded-xl border p-4 text-sm" style={{ borderColor: '#ff6b81' }}>
        <div className="mb-1 font-semibold text-warn">This page hit an error</div>
        <pre className="whitespace-pre-wrap text-xs opacity-70">{this.state.error.message}</pre>
        <button className="mt-2 rounded border px-3 py-1 text-xs" style={{ borderColor: 'var(--d-border)' }} onClick={() => this.setState({ error: null })}>Retry</button>
      </div>
    );
  }
}
