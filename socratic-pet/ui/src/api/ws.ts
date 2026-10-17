import { WS_UI_URL } from './config';
export interface UiSocket { close(): void }

// Auto-reconnecting /ws/ui client (exponential backoff, capped at 5s).
export function connectUiSocket(
  onMessage: (raw: unknown) => void,
  onStatus: (connected: boolean) => void,
): UiSocket {
  let ws: WebSocket | null = null;
  let closed = false;
  let retry = 0;
  let timer: ReturnType<typeof setTimeout> | undefined;

  const open = () => {
    ws = new WebSocket(WS_UI_URL);
    ws.onopen = () => { retry = 0; onStatus(true); };
    ws.onmessage = (e) => {
      let raw: unknown;
      try { raw = JSON.parse(e.data as string); } catch { return; /* not JSON: ignore */ }
      onMessage(raw);
    };
    ws.onclose = () => {
      onStatus(false);
      if (closed) return;
      timer = setTimeout(open, Math.min(5000, 400 * 2 ** retry++));
    };
    ws.onerror = () => ws?.close();
  };
  open();

  return { close() { closed = true; clearTimeout(timer); ws?.close(); } };
}
