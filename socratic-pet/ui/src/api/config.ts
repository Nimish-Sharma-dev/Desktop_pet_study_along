const base = (import.meta.env.VITE_DAEMON_URL as string | undefined) ?? 'http://localhost:7777';
export const HTTP_BASE = base.replace(/\/$/, '');
export const WS_UI_URL = HTTP_BASE.replace(/^http/, 'ws') + '/ws/ui';
