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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.DaemonClient = void 0;
const http = __importStar(require("http"));
const ws_1 = __importDefault(require("ws"));
/** WebSocket to /ws/editor with reconnect + tiny REST helper. Talks to localhost only. */
class DaemonClient {
    constructor(baseUrl, onCommand, onState, log) {
        this.baseUrl = baseUrl;
        this.onCommand = onCommand;
        this.onState = onState;
        this.log = log;
        this.backoff = 1000;
        this.disposed = false;
        this.connected = false;
    }
    connect() {
        if (this.disposed) {
            return;
        }
        const url = this.baseUrl().replace(/^http/, 'ws') + '/ws/editor';
        const ws = new ws_1.default(url);
        this.ws = ws;
        ws.on('open', () => { this.connected = true; this.backoff = 1000; this.onState(true); this.log(`connected to ${url}`); });
        ws.on('message', (data) => {
            try {
                this.onCommand(JSON.parse(data.toString()));
            }
            catch (e) {
                this.log(`bad command frame: ${e}`);
            }
        });
        ws.on('error', () => { });
        ws.on('close', () => {
            const was = this.connected;
            this.connected = false;
            if (was) {
                this.onState(false);
            }
            if (!this.disposed && this.ws === ws) {
                this.timer = setTimeout(() => this.connect(), this.backoff);
                this.backoff = Math.min(this.backoff * 2, 10000);
            }
        });
    }
    reconnect() {
        if (this.timer) {
            clearTimeout(this.timer);
        }
        const old = this.ws;
        this.ws = undefined;
        old?.close();
        this.connected = false;
        this.onState(false);
        this.backoff = 1000;
        this.connect();
    }
    send(obj) {
        if (this.ws && this.ws.readyState === ws_1.default.OPEN) {
            this.ws.send(JSON.stringify(obj));
        }
    }
    postJson(pathname, body, timeoutMs = 60000) {
        return new Promise((resolve, reject) => {
            const u = new URL(this.baseUrl() + pathname);
            const payload = JSON.stringify(body);
            const req = http.request({ hostname: u.hostname, port: u.port, path: u.pathname, method: 'POST', timeout: timeoutMs,
                headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(payload) } }, (res) => {
                let buf = '';
                res.on('data', (c) => (buf += c));
                res.on('end', () => {
                    if ((res.statusCode ?? 500) >= 400) {
                        reject(new Error(`${res.statusCode}: ${buf}`));
                        return;
                    }
                    try {
                        resolve(JSON.parse(buf));
                    }
                    catch (e) {
                        reject(e);
                    }
                });
            });
            req.on('timeout', () => req.destroy(new Error('daemon request timed out')));
            req.on('error', reject);
            req.write(payload);
            req.end();
        });
    }
    dispose() {
        this.disposed = true;
        if (this.timer) {
            clearTimeout(this.timer);
        }
        this.ws?.close();
    }
}
exports.DaemonClient = DaemonClient;
//# sourceMappingURL=daemonClient.js.map