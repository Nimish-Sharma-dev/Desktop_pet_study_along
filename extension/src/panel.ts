import * as vscode from 'vscode';

/** Side panel: shows the pet's questions and lets the student type a reply. */
export class TutorPanel implements vscode.WebviewViewProvider {
  private view?: vscode.WebviewView;
  private history: string[] = [];
  constructor(private onReply: (text: string) => void) {}

  resolveWebviewView(view: vscode.WebviewView): void {
    this.view = view;
    view.webview.options = { enableScripts: true };
    const nonce = Math.random().toString(36).slice(2);
    view.webview.html = `<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';">
<style>body{font-family:var(--vscode-font-family);padding:8px}
.b{background:var(--vscode-editorWidget-background);border-radius:8px;padding:8px;margin:6px 0}
.me{background:var(--vscode-button-secondaryBackground)}
textarea{width:100%;box-sizing:border-box;margin-top:8px}</style></head><body>
<div id="log"></div><textarea id="t" rows="3" placeholder="Reply to the pet..."></textarea>
<button id="s">Reply</button>
<script nonce="${nonce}">
const vs = acquireVsCodeApi(); const log = document.getElementById('log');
function add(text, me){ const d=document.createElement('div'); d.className='b'+(me?' me':''); d.textContent=text; log.appendChild(d); d.scrollIntoView(); }
document.getElementById('s').onclick = () => { const t=document.getElementById('t'); if(!t.value.trim()) return; add(t.value,true); vs.postMessage({type:'reply',text:t.value}); t.value=''; };
window.addEventListener('message', e => { if(e.data.type==='hint') add(e.data.text,false); });
vs.postMessage({type:'ready'});
</script></body></html>`;
    view.webview.onDidReceiveMessage((m) => {
      if (m.type === 'reply') { this.onReply(String(m.text)); }
      if (m.type === 'ready') { this.history.forEach((t) => view.webview.postMessage({ type: 'hint', text: t })); }
    });
  }

  show(text: string): void {
    this.history = [...this.history.slice(-19), text];
    this.view?.webview.postMessage({ type: 'hint', text });
  }
}
