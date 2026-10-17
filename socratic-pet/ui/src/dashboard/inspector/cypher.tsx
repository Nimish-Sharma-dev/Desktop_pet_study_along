import { useMemo } from 'react';

const KEYWORDS = new Set(['MATCH', 'OPTIONAL', 'WHERE', 'RETURN', 'WITH', 'CREATE', 'MERGE', 'SET', 'DELETE', 'DETACH', 'ORDER', 'BY', 'LIMIT', 'SKIP', 'UNWIND', 'AS', 'AND', 'OR', 'NOT', 'IN', 'DISTINCT', 'CALL', 'YIELD', 'ON', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'UNION', 'ASC', 'DESC', 'NULL', 'TRUE', 'FALSE', 'STARTS', 'ENDS', 'CONTAINS', 'IS', 'XOR', 'EXISTS', 'REMOVE', 'FOREACH']);

// comment | string | $param | number | :Label(|Other) | function( | identifier | whitespace | any char
const TOKEN = /(\/\/[^\n]*)|('(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")|(\$[A-Za-z_]\w*)|(\b\d+(?:\.\d+)?\b)|(:[A-Za-z_]\w*(?:\|[A-Za-z_]\w*)*)|([A-Za-z_]\w*)(?=\s*\()|([A-Za-z_]\w*)|(\s+)|([\s\S])/g;

type Tok = { cls: string; text: string };

export function tokenizeCypher(src: string): Tok[] {
  const out: Tok[] = [];
  let braces = 0;
  for (const m of src.matchAll(TOKEN)) {
    const [text, com, str, param, num, label, fn, ident, ws] = m;
    if (com) out.push({ cls: 'cy-com', text });
    else if (str) out.push({ cls: 'cy-str', text });
    else if (param) out.push({ cls: 'cy-param', text });
    else if (num) out.push({ cls: 'cy-num', text });
    else if (label) out.push({ cls: 'cy-label', text });
    else if (fn) out.push({ cls: KEYWORDS.has(fn.toUpperCase()) ? 'cy-kw' : 'cy-fn', text });
    else if (ident) {
      const next = src.slice((m.index ?? 0) + text.length).trimStart()[0];
      out.push({ cls: KEYWORDS.has(ident.toUpperCase()) ? 'cy-kw' : braces > 0 && next === ':' ? 'cy-key' : 'cy-var', text });
    } else if (ws) out.push({ cls: '', text });
    else {
      if (text === '{') braces++;
      if (text === '}') braces = Math.max(0, braces - 1);
      out.push({ cls: 'cy-punct', text });
    }
  }
  return out;
}

export function CypherView({ source }: { source: string }) {
  const toks = useMemo(() => tokenizeCypher(source), [source]);
  return (
    <pre className="cy-block">
      {toks.map((t, i) => (t.cls ? <span key={i} className={t.cls}>{t.text}</span> : t.text))}
    </pre>
  );
}
