import * as http from 'http';
import WebSocket from 'ws';

export type Command = { command: string; [k: string]: any };

/** WebSocket to /ws/editor with reconnect + tiny REST helper. Talks to localhost only. */
export class DaemonClient {
  private ws?: WebSocket;
  private timer?: NodeJS.Timeout;
  private backoff = 1000;
  private disposed = false;
  connected = false;

  constructor(
    private baseUrl: () => string,
    private onCommand: (c: Command) => void,
    private onState: (connected: boolean) => void,
    private log: (m: string) => void,
  ) {}

  connect(): void {
    if (this.disposed) { return; }
    const url = this.baseUrl().replace(/^http/, 'ws') + '/ws/editor';
    const ws = new WebSocket(url);
    this.ws = ws;
    ws.on('open', () => { this.connected = true; this.backoff = 1000; this.onState(true); this.log(`connected to ${url}`); });
    ws.on('message', (data) => {
      try { this.onCommand(JSON.parse(data.toString())); } catch (e) { this.log(`bad command frame: ${e}`); }
    });
    ws.on('error', () => { /* 'close' follows; reconnect is scheduled there */ });
    ws.on('close', () => {
      const was = this.connected;
      this.connected = false;
      if (was) { this.onState(false); }
      if (!this.disposed && this.ws === ws) {
        this.timer = setTimeout(() => this.connect(), this.backoff);
        this.backoff = Math.min(this.backoff * 2, 10000);
      }
    });
  }

  reconnect(): void {
    if (this.timer) { clearTimeout(this.timer); }
    const old = this.ws;
    this.ws = undefined;
    old?.close();
    this.connected = false;
    this.onState(false);
    this.backoff = 1000;
    this.connect();
  }

  send(obj: unknown): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) { this.ws.send(JSON.stringify(obj)); }
  }

  postJson<T = any>(pathname: string, body: unknown, timeoutMs = 60000): Promise<T> {
    return new Promise((resolve, reject) => {
      const u = new URL(this.baseUrl() + pathname);
      const payload = JSON.stringify(body);
      const req = http.request(
        { hostname: u.hostname, port: u.port, path: u.pathname, method: 'POST', timeout: timeoutMs,
          headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(payload) } },
        (res) => {
          let buf = '';
          res.on('data', (c) => (buf += c));
          res.on('end', () => {
            if ((res.statusCode ?? 500) >= 400) { reject(new Error(`${res.statusCode}: ${buf}`)); return; }
            try { resolve(JSON.parse(buf)); } catch (e) { reject(e); }
          });
        });
      req.on('timeout', () => req.destroy(new Error('daemon request timed out')));
      req.on('error', reject);
      req.write(payload);
      req.end();
    });
  }

  dispose(): void {
    this.disposed = true;
    if (this.timer) { clearTimeout(this.timer); }
    this.ws?.close();
  }
}
