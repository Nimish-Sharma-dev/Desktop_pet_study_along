import * as fs from 'fs';
import * as os from 'os';
import * as path from 'path';

export function expandHome(p: string): string {
  return p === '~' || p.startsWith('~/') || p.startsWith('~\\') ? path.join(os.homedir(), p.slice(1)) : p;
}

function real(p: string): string {
  try { return fs.realpathSync(p); } catch { return path.resolve(p); }
}

/** True only for files inside an allowlisted folder, and never for obvious secret files. */
export function isAllowed(file: string, folders: string[]): boolean {
  const base = path.basename(file).toLowerCase();
  if (base.startsWith('.env') || base.endsWith('.pem') || base.endsWith('.key')) { return false; }
  const f = real(file);
  return folders.some((folder) => {
    const rel = path.relative(real(expandHome(folder)), f);
    return rel === '' || (!rel.startsWith('..') && !path.isAbsolute(rel));
  });
}
