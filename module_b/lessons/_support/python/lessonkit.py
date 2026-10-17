"""Lesson test kit (python). Every failure is reported as `LESSON_FAIL {json}` so the runner
gets expected/actual/error_type/line identically for every language and framework."""
import importlib
import json
import signal
import traceback

import pytest

TIMEOUT_S = 2.0
MAX_TIMEOUTS = 3          # after this many hangs the remaining cases are reported as skipped timeouts
_timeouts = 0


class _Timeout(BaseException):          # BaseException: a student's `except Exception` can't swallow it
    pass


def _on_alarm(signum, frame):
    raise _Timeout()


def _gen(spec):
    g = spec["gen"]
    if g == "range":
        start, count, step = spec["args"]
        return list(range(start, start + count * step, step))
    if g == "chain_edges":
        return [[i, i + 1] for i in range(spec["args"][0] - 1)]
    raise ValueError(g)


def _build(kind, v, sol):
    if isinstance(v, dict) and "gen" in v:
        v = _gen(v)
    if kind == "linked_list":
        head = None
        for x in reversed(v):
            head = sol.ListNode(x, head)
        return head
    return json.loads(json.dumps(v))     # fresh copy: a mutating solution can't leak into the next case


def _to_json(kind, v):
    if kind == "linked_list":
        out, n = [], 0
        while v is not None:
            out.append(v.val)
            v = v.next
            n += 1
            if n > 1_000_000:
                raise ValueError("returned list has a cycle")
        return out
    return v


def _error_type(e):
    n = type(e).__name__
    if isinstance(e, RecursionError):
        return "RecursionError"
    if isinstance(e, (IndexError,)):
        return "IndexError"
    if isinstance(e, AttributeError) and "NoneType" in str(e):
        return "NullReference"
    if isinstance(e, TypeError) and "NoneType" in str(e):
        return "NullReference"
    if isinstance(e, MemoryError):
        return "MemoryError"
    return n


def _line(tb):
    line = None
    for fr in traceback.extract_tb(tb):
        if fr.filename.endswith("solution.py"):
            line = fr.lineno
    return line


def _fail(info):
    pytest.fail("LESSON_FAIL " + json.dumps(info, default=repr), pytrace=False)


def check(fn, param_kinds, ret_kind, args, expected):
    global _timeouts
    if isinstance(expected, dict) and "eval" in expected:
        expected = eval(expected["eval"])
    if _timeouts >= MAX_TIMEOUTS:
        _fail({"error_type": "Timeout", "expected": expected, "detail": f"skipped: {MAX_TIMEOUTS} earlier cases already timed out"})
    try:
        sol = importlib.import_module("solution")
    except (SyntaxError, ImportError) as e:             # IndentationError is a SyntaxError
        _fail({"error_type": "CompileError", "expected": expected,
               "detail": f"{type(e).__name__}: {str(e)[:120]}", "line": getattr(e, "lineno", None)})
    if not hasattr(sol, fn):
        _fail({"error_type": "WrongAnswer", "expected": expected, "detail": f"function {fn} is not defined"})
    f = getattr(sol, fn)
    real = [_build(k, a, sol) for k, a in zip(param_kinds, args)]
    has_sigalrm = hasattr(signal, "SIGALRM") and hasattr(signal, "setitimer")
    if has_sigalrm:
        signal.signal(signal.SIGALRM, _on_alarm)
        signal.setitimer(signal.ITIMER_REAL, TIMEOUT_S)
    try:
        if has_sigalrm:
            actual = _to_json(ret_kind, f(*real))
        else:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(f, *real)
                actual = _to_json(ret_kind, fut.result(timeout=TIMEOUT_S))
    except (_Timeout, TimeoutError, Exception) as e:
        if has_sigalrm:
            signal.setitimer(signal.ITIMER_REAL, 0)
        is_to = isinstance(e, _Timeout) or type(e).__name__ == "TimeoutError"
        if is_to:
            _timeouts += 1
            _fail({"error_type": "Timeout", "expected": expected, "detail": f"no answer after {TIMEOUT_S:.0f}s"})
        else:
            _fail({"error_type": _error_type(e), "expected": expected, "detail": f"{type(e).__name__}: {str(e)[:120]}",
                   "line": _line(e.__traceback__)})
    except BaseException as e:          # noqa
        if has_sigalrm:
            signal.setitimer(signal.ITIMER_REAL, 0)
        if isinstance(e, _Timeout):
            _timeouts += 1
            _fail({"error_type": "Timeout", "expected": expected, "detail": f"no answer after {TIMEOUT_S:.0f}s"})
        else:
            _fail({"error_type": _error_type(e), "expected": expected, "detail": f"{type(e).__name__}: {str(e)[:120]}",
                   "line": _line(e.__traceback__)})
    finally:
        if has_sigalrm:
            signal.setitimer(signal.ITIMER_REAL, 0)
    try:
        same = json.dumps(actual, sort_keys=True) == json.dumps(expected, sort_keys=True)
    except TypeError:
        same, actual = False, repr(actual)
    if not same:
        _fail({"error_type": "WrongAnswer", "expected": expected, "actual": actual})
