// Lesson test kit (javascript). Runs solution.js inside a vm context so a hung call can be
// interrupted (vm `timeout`), and reports failures as `LESSON_FAIL {json}`.
const fs = require('fs');
const vm = require('vm');
const path = require('path');

const TIMEOUT_MS = 2000;
const MAX_TIMEOUTS = 3; // after this many hangs the remaining cases are reported as skipped timeouts
let timeouts = 0;
let ctx = null;

function load() {
  if (ctx) return ctx;
  const code = fs.readFileSync(path.join(__dirname, 'solution.js'), 'utf8');
  const sandbox = { module: { exports: {} }, console };
  sandbox.exports = sandbox.module.exports;
  ctx = vm.createContext(sandbox);
  new vm.Script(code, { filename: 'solution.js' }).runInContext(ctx, { timeout: TIMEOUT_MS });
  return ctx;
}

function gen(spec) {
  if (spec.gen === 'range') {
    const [start, count, step] = spec.args;
    return Array.from({ length: count }, (_, i) => start + i * step);
  }
  if (spec.gen === 'chain_edges') {
    return Array.from({ length: spec.args[0] - 1 }, (_, i) => [i, i + 1]);
  }
  throw new Error('unknown generator ' + spec.gen);
}

function errorType(e) {
  const s = String((e && e.name) || '') + ' ' + String((e && e.message) || '');
  if (/Maximum call stack/.test(s)) return 'RecursionError';
  if (/Cannot read propert|of null|of undefined|is not a function/.test(s)) return 'NullReference';
  if (/timed out/.test(s)) return 'Timeout';
  return (e && e.name) || 'Error';
}

function fail(info) {
  throw new Error('LESSON_FAIL ' + JSON.stringify(info));
}

function check(fn, paramKinds, retKind, args, expected) {
  if (expected && typeof expected === 'object' && 'eval' in expected) expected = eval(expected.eval);
  if (timeouts >= MAX_TIMEOUTS) fail({ error_type: 'Timeout', expected, detail: `skipped: ${MAX_TIMEOUTS} earlier cases already timed out` });
  let c;
  try {
    c = load();
  } catch (e) {
    fail({ error_type: e instanceof SyntaxError ? 'CompileError' : errorType(e), expected, detail: `${e.name}: ${String(e.message).slice(0, 120)}` });
  }
  c.__fn = fn;
  c.__args = JSON.stringify(args.map((a) => (a && a.gen ? gen(a) : a)));
  c.__pk = JSON.stringify(paramKinds);
  c.__rk = retKind;
  const driver = `(function () {
    const sol = module.exports;
    const a = JSON.parse(__args), pk = JSON.parse(__pk);
    const real = a.map((v, i) => {
      if (pk[i] !== 'linked_list') return v;
      let head = null;
      for (let j = v.length - 1; j >= 0; j--) head = new sol.ListNode(v[j], head);
      return head;
    });
    let r = sol[__fn](...real);
    if (__rk === 'linked_list') {
      const out = []; let n = 0;
      while (r !== null && r !== undefined) { out.push(r.val); r = r.next; if (++n > 1000000) throw new Error('returned list has a cycle'); }
      r = out;
    }
    return JSON.stringify(r === undefined ? null : r);
  })()`;
  let actualStr;
  try {
    actualStr = vm.runInContext(driver, c, { timeout: TIMEOUT_MS, filename: 'driver.js' });
  } catch (e) {
    const m = /solution\.js:(\d+)/.exec(String(e && e.stack));
    const et = errorType(e);
    if (et === 'Timeout') timeouts++;
    fail({ error_type: et, expected, detail: et === 'Timeout' ? 'no answer after 2s' : `${e.name}: ${String(e.message).slice(0, 120)}`, line: m ? +m[1] : undefined });
  }
  const actual = JSON.parse(actualStr);
  if (JSON.stringify(actual) !== JSON.stringify(expected)) fail({ error_type: 'WrongAnswer', expected, actual });
}

module.exports = { check };
