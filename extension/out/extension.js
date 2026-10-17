"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const path = __importStar(require("path"));
const vscode = __importStar(require("vscode"));
const allowlist_1 = require("./allowlist");
const daemonClient_1 = require("./daemonClient");
const panel_1 = require("./panel");
const redact_1 = require("./redact");
const SEVERITY = ['error', 'warning', 'info', 'hint'];
const cfg = () => vscode.workspace.getConfiguration('tutor');
const folders = () => cfg().get('allowlistedFolders', ['~/tutor-lessons']);
function activate(ctx) {
    const out = vscode.window.createOutputChannel('Tutor');
    const log = (m) => out.appendLine(`[${new Date().toISOString()}] ${m}`);
    let paused = ctx.workspaceState.get('tutor.paused', cfg().get('pauseOnStart', false));
    const coalesce = new Map();
    // ---- UI bits
    const bar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 100);
    bar.command = 'tutor.togglePause';
    const hintBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 99);
    hintBar.command = 'tutor.reply';
    const renderBar = () => {
        if (paused) {
            bar.text = '$(debug-pause) Tutor paused';
            bar.tooltip = 'Nothing is being sent. Click to resume.';
            bar.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
        }
        else {
            bar.text = client.connected ? '$(mortar-board) Tutor' : '$(mortar-board) Tutor (offline)';
            bar.tooltip = client.connected ? 'Watching allowlisted lesson folders. Click to pause.' : 'Daemon not reachable; retrying...';
            bar.backgroundColor = undefined;
        }
        bar.show();
    };
    const sid = () => cfg().get('studentId', 'local-user');
    const panel = new panel_1.TutorPanel((t) => void sendReply(t));
    const client = new daemonClient_1.DaemonClient(() => cfg().get('daemonUrl', 'http://localhost:7777'), (c) => void onCommand(c), () => { renderBar(); if (client.connected && !paused) {
        resync();
    } }, log);
    // ---- the single gate every outgoing event passes through
    function emit(ev) {
        if (paused) {
            return;
        }
        if (!(0, allowlist_1.isAllowed)(ev.file, folders())) {
            return;
        }
        if (ev.content !== undefined) {
            ev.content = (0, redact_1.redact)(ev.content);
        }
        ev.diagnostics?.forEach((d) => (d.message = (0, redact_1.redact)(d.message).slice(0, 300)));
        client.send(ev);
    }
    function base(doc, type) {
        const ed = vscode.window.visibleTextEditors.find((e) => e.document === doc);
        const sel = ed?.selection;
        return {
            type, ts: Math.floor(Date.now() / 1000), file: doc.uri.fsPath, language: doc.languageId, student_id: sid(),
            cursor: sel ? { line: sel.active.line + 1, col: sel.active.character + 1 } : null,
            selection: sel && !sel.isEmpty
                ? { start: { line: sel.start.line + 1, col: sel.start.character + 1 }, end: { line: sel.end.line + 1, col: sel.end.character + 1 } }
                : null,
        };
    }
    const watched = (doc) => doc.uri.scheme === 'file';
    function resync() {
        const ed = vscode.window.activeTextEditor;
        if (ed && watched(ed.document)) {
            emit({ ...base(ed.document, 'focus'), content: ed.document.getText() });
        }
    }
    // ---- editor listeners (all early-out when paused; pausing also cancels pending timers)
    ctx.subscriptions.push(vscode.workspace.onDidChangeTextDocument((e) => {
        if (paused || !watched(e.document) || e.contentChanges.length === 0) {
            return;
        }
        const key = e.document.uri.toString();
        clearTimeout(coalesce.get(key));
        coalesce.set(key, setTimeout(() => {
            coalesce.delete(key);
            emit({ ...base(e.document, 'edit'), content: e.document.getText() });
        }, cfg().get('editCoalesceMs', 250)));
    }), vscode.window.onDidChangeActiveTextEditor((ed) => {
        if (ed && watched(ed.document)) {
            emit({ ...base(ed.document, 'focus'), content: ed.document.getText() });
        }
    }), vscode.window.onDidChangeTextEditorSelection((e) => {
        if (watched(e.textEditor.document)) {
            emit(base(e.textEditor.document, 'cursor'));
        }
    }), vscode.languages.onDidChangeDiagnostics((e) => {
        if (paused) {
            return;
        }
        for (const uri of e.uris) {
            if (uri.scheme !== 'file') {
                continue;
            }
            const doc = vscode.workspace.textDocuments.find((d) => d.uri.toString() === uri.toString());
            const diags = vscode.languages.getDiagnostics(uri).slice(0, 50).map((d) => ({
                line: d.range.start.line + 1, severity: SEVERITY[d.severity] ?? 'info', message: d.message
            }));
            emit({ type: 'diagnostics', ts: Math.floor(Date.now() / 1000), file: uri.fsPath,
                language: doc?.languageId ?? '', student_id: sid(), diagnostics: diags });
        }
    }), vscode.workspace.onDidOpenTextDocument((d) => { if (watched(d)) {
        emit({ ...base(d, 'file_open'), action: 'open' });
    } }), vscode.workspace.onDidCloseTextDocument((d) => { if (watched(d)) {
        emit({ ...base(d, 'file_open'), action: 'close' });
    } }), vscode.workspace.onDidChangeConfiguration((e) => { if (e.affectsConfiguration('tutor.daemonUrl')) {
        client.reconnect();
    } }));
    // ---- commands from the user
    async function setPaused(p) {
        paused = p;
        await ctx.workspaceState.update('tutor.paused', p);
        if (p) {
            coalesce.forEach(clearTimeout);
            coalesce.clear();
        }
        renderBar();
        try {
            await client.postJson('/api/pause', { paused: p }, 3000);
        }
        catch { /* daemon also drops nothing it never receives */ }
        if (!p) {
            resync();
        }
        vscode.window.setStatusBarMessage(p ? 'Tutor paused: nothing is sent' : 'Tutor resumed', 3000);
    }
    async function sendReply(text) {
        if (paused) {
            vscode.window.showInformationMessage('Tutor is paused.');
            return;
        }
        try {
            await client.postJson('/api/reply', { text: (0, redact_1.redact)(text), student_id: sid() });
        }
        catch (e) {
            vscode.window.showWarningMessage(`Tutor: could not send reply (${e})`);
        }
    }
    async function promptReply() {
        const text = await vscode.window.showInputBox({ prompt: 'Reply to the pet', ignoreFocusOut: true });
        if (text) {
            await sendReply(text);
        }
    }
    async function runTests() {
        const ed = vscode.window.activeTextEditor;
        if (!ed || !watched(ed.document)) {
            vscode.window.showWarningMessage('Open a lesson file first.');
            return;
        }
        if (!(0, allowlist_1.isAllowed)(ed.document.uri.fsPath, folders())) {
            vscode.window.showWarningMessage('This file is outside your allowlisted lessons folder.');
            return;
        }
        await ed.document.save();
        await vscode.window.withProgress({ location: vscode.ProgressLocation.Notification, title: 'Tutor: running tests...' }, async () => {
            try {
                const r = await client.postJson('/api/run_tests', { file: ed.document.uri.fsPath, language: ed.document.languageId, student_id: sid() });
                const results = r.results ?? [];
                const passed = results.filter((x) => x.passed).length;
                out.clear();
                out.appendLine(`${r.lesson_id} (${r.language}) ${passed}/${results.length} passed in ${r.duration_ms} ms`);
                for (const t of results) {
                    out.appendLine(`${t.passed ? 'PASS' : 'FAIL'}  ${t.name}`);
                    if (!t.passed) {
                        out.appendLine(`      expected ${t.expected}, got ${t.actual}${t.error_type ? ` (${t.error_type})` : ''}`);
                    }
                }
                out.show(true);
                const msg = `Tutor: ${passed}/${results.length} tests passed`;
                if (r.all_passed) {
                    vscode.window.showInformationMessage(msg + ' 🎉');
                }
                else {
                    vscode.window.showWarningMessage(msg);
                }
            }
            catch (e) {
                vscode.window.showErrorMessage(`Tutor: test run failed (${e})`);
            }
        });
    }
    // ---- commands received from the daemon (allowlist enforced again here)
    async function onCommand(c) {
        log(`command ${c.command}`);
        switch (c.command) {
            case 'show_hint': {
                const text = String(c.text ?? '');
                hintBar.text = `$(comment) ${text.length > 60 ? text.slice(0, 57) + '...' : text}`;
                hintBar.tooltip = `${text}\n\n(click to reply)`;
                hintBar.show();
                panel.show(text);
                vscode.window.setStatusBarMessage(`Tutor: ${text}`, 20000);
                break;
            }
            case 'open_file': {
                const f = String(c.file ?? '');
                if (!(0, allowlist_1.isAllowed)(f, folders())) {
                    return;
                }
                const doc = await vscode.workspace.openTextDocument(f);
                const ed = await vscode.window.showTextDocument(doc);
                const line = Math.max(0, Number(c.line ?? 1) - 1);
                const pos = new vscode.Position(line, 0);
                ed.selection = new vscode.Selection(pos, pos);
                ed.revealRange(new vscode.Range(pos, pos), vscode.TextEditorRevealType.InCenter);
                break;
            }
            case 'open_lesson': {
                const p = String(c.path ?? '');
                if (!(0, allowlist_1.isAllowed)(p, folders())) {
                    return;
                }
                const uri = vscode.Uri.file(p);
                if (vscode.workspace.workspaceFolders?.length) {
                    vscode.workspace.updateWorkspaceFolders(vscode.workspace.workspaceFolders.length, 0, { uri, name: path.basename(p) });
                }
                else {
                    await vscode.commands.executeCommand('vscode.openFolder', uri);
                }
                break;
            }
            case 'accept_reply':
                await promptReply();
                break;
            default:
                log(`unknown command ${c.command}`);
        }
    }
    ctx.subscriptions.push(vscode.commands.registerCommand('tutor.runTests', runTests), vscode.commands.registerCommand('tutor.togglePause', () => setPaused(!paused)), vscode.commands.registerCommand('tutor.reply', promptReply), vscode.window.registerWebviewViewProvider('tutor.panel', panel, { webviewOptions: { retainContextWhenHidden: true } }), bar, hintBar, out, { dispose: () => client.dispose() });
    renderBar();
    client.connect();
    if (paused) {
        void client.postJson('/api/pause', { paused: true }, 3000).catch(() => undefined);
    }
    log(`activated; allowlist=${folders().map(allowlist_1.expandHome).join(', ')}; paused=${paused}`);
}
function deactivate() { }
//# sourceMappingURL=extension.js.map