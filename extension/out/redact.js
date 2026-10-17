"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.redact = redact;
// Mirror of daemon/redact.py. Runs BEFORE anything leaves the editor process.
const PATTERNS = [
    [/-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----/g, '[REDACTED:private-key]'],
    [/\bAKIA[0-9A-Z]{16}\b/g, '[REDACTED:aws-key]'],
    [/\bgh[pousr]_[A-Za-z0-9]{36,}\b/g, '[REDACTED:github-token]'],
    [/\bsk-[A-Za-z0-9_\-]{20,}\b/g, '[REDACTED:api-key]'],
    [/\bxox[abprs]-[A-Za-z0-9\-]{10,}\b/g, '[REDACTED:slack-token]'],
    [/\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\b/g, '[REDACTED:jwt]'],
    [/\b([\w.-]*(?:api[_-]?key|secret|token|passw(?:or)?d|pwd)[\w.-]*)(["']?\s*[:=]\s*)(['"])([^'"\n]{4,})\3/gi, '$1$2$3[REDACTED]$3'],
    [/^([ \t]*[A-Z0-9_]*(?:KEY|SECRET|TOKEN|PASSWORD|PASSWD)[A-Z0-9_]*[ \t]*=[ \t]*)(?!['"])\S+/gm, '$1[REDACTED]'],
];
function redact(text) {
    for (const [re, rep] of PATTERNS) {
        text = text.replace(re, rep);
    }
    return text;
}
//# sourceMappingURL=redact.js.map