import { invoke as tauriInvoke } from '@tauri-apps/api/core';
import { getCurrentWindow } from '@tauri-apps/api/window';

// All wrappers are no-ops in a plain browser, so `npm run dev` previews still work.
export const isTauri = typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;

export async function invoke<T = void>(cmd: string, args?: Record<string, unknown>): Promise<T | undefined> {
  if (!isTauri) return undefined;
  return tauriInvoke<T>(cmd, args);
}

export function openDashboard() {
  if (isTauri) void invoke('open_dashboard');
  else window.open('/dashboard.html', 'tutor-pet-dashboard');
}

export async function startDragging() {
  if (isTauri) await getCurrentWindow().startDragging();
}

// Frameless dashboard window controls (no-ops in a browser).
export const windowControls = {
  minimize: () => { if (isTauri) void getCurrentWindow().minimize(); },
  toggleMaximize: () => { if (isTauri) void getCurrentWindow().toggleMaximize(); },
  close: () => { if (isTauri) void getCurrentWindow().close(); },
};
