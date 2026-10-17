import { useEffect, useRef, useState } from 'react';
import { invoke, isTauri } from '../lib/tauri';
import { useStore } from '../store/useStore';
import { ErrorBoundary } from './components/ErrorBoundary';
import { Sidebar, type Page } from './components/Sidebar';
import { TitleBar } from './components/TitleBar';
import { InspectorDrawer } from './inspector/InspectorDrawer';
import { CommandCenter } from './pages/CommandCenter';
import { DevFeed } from './pages/DevFeed';
import { GraphPage } from './pages/GraphPage';
import { ProgressPage } from './pages/ProgressPage';

export function DashboardApp() {
  const mode = useStore((s) => s.mode);
  const [page, setPage] = useState<Page>(mode === 'system_design' ? 'command' : 'progress');
  const [glass, setGlass] = useState(false);
  const [boot, setBoot] = useState(0);
  const firstMode = useRef(true);

  useEffect(() => {
    if (!isTauri) { document.body.style.background = '#0b0d17'; return; }
    void invoke<boolean>('glass_enabled').then((v) => setGlass(!!v));
  }, []);

  // entering system design: jump to the command center + play the boot sweep; leaving: back to progress
  useEffect(() => {
    if (mode === 'system_design') {
      setPage('command');
      if (!firstMode.current) setBoot((b) => b + 1);
    } else {
      setPage((p) => (p === 'command' ? 'progress' : p));
    }
    firstMode.current = false;
  }, [mode]);

  return (
    <div className="dash-root relative flex h-full flex-col overflow-hidden" data-mode={mode} data-glass={glass ? 'on' : 'off'}>
      <TitleBar />
      <div className="flex min-h-0 flex-1">
        <Sidebar page={page} mode={mode} onChange={setPage} />
        <main className="min-w-0 flex-1">
          <ErrorBoundary resetKey={page}>
            {page === 'command' && <CommandCenter />}
            {page === 'progress' && <ProgressPage />}
            {page === 'graph' && <GraphPage />}
            {page === 'dev' && <DevFeed />}
          </ErrorBoundary>
        </main>
      </div>
      <InspectorDrawer />
      {boot > 0 && <div key={boot} className="hud-boot" />}
    </div>
  );
}
