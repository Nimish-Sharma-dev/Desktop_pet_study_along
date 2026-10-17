"""Language-neutral rules. Each rule is written ONCE against neutral node kinds
(function / loop / foreach / conditional / call, see languages.yaml) plus expression
regexes run on comment- and string-blanked source. A grammar never gets its own rule code.

A rule returns Hits tagged with a neutral rule id (e.g. "loop_bound_off_by_one").
analyzer.py maps rule ids to a lesson's mistake_id through the `signals` list
("rule:<rule id>") in lesson.yaml, so the same logical bug yields the same mistake_id
in every language.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Callable

from . import astutil as A
from .model import Hit
from .parser import Parsed, walk


@dataclass
class Rule:
    id: str
    default_mistake: str
    concepts: list
    fn: Callable[[Parsed], list]
    doc: str = ""


RULES: dict = {}


def rule(id: str, default_mistake: str, concepts: list):
    def deco(fn):
        RULES[id] = Rule(id, default_mistake, concepts, fn, (fn.__doc__ or "").strip())
        return fn
    return deco


# --------------------------------------------------------------------------- expressions
LEN = (r"(?:len\(\s*\w+\s*\)|\w+(?:\.\w+)*\.(?:length|size|Length|Count|count|len)(?:\(\))?"
       r"|strlen\(\s*\w+\s*\))")

_BOUND = [  # (regex, confidence, description)
    # bare index on the left: `i + k <= n.length` is a legitimate window bound, `i <= n.length` is not
    (rf"(?<![\w+\-*/])(?<![+\-*/]\s)\w+\s*<=\s*{LEN}(?!\s*[-/*])", 0.85, "loop runs while index <= length"),
    (rf"range\(\s*(?:[^(),]+,\s*)?{LEN}\s*\+\s*1\s*\)", 0.9, "range goes one past the length"),
    (rf"<\s*{LEN}\s*\+\s*1", 0.85, "loop runs while index < length + 1"),
    (rf"=\s*{LEN}\s*;[^;]*>=[^;]*;[^)]*(?:--|-=\s*1)", 0.6, "countdown loop starts at length"),
    (rf"range\(\s*{LEN}\s*,[^)]*,\s*-1\s*\)", 0.6, "countdown range starts at length"),
]
_LOOPVAR = re.compile(r"for\s*\(?\s*(?:[A-Za-z_][\w<>\[\]*&]*\s+)*(\w+)\s*(?::=|=|\bin\b|,)")


def _line_at(base_row: int, text: str, idx: int) -> int:
    return base_row + 1 + text.count("\n", 0, idx)


@rule("loop_bound_off_by_one", "boundary_off_by_one", ["array_indexing", "loop_invariants"])
def r_off_by_one(p: Parsed) -> list:
    """Loop bound or index arithmetic that reaches one element past a collection."""
    hits = []
    pats = [(re.compile(rx), c, d) for rx, c, d in _BOUND]
    for extra in p.cfg.bound_patterns:
        pats.append((re.compile(extra.replace("{LEN}", LEN)), 0.8, "range reaches the length itself"))
    if p.cfg.length_params:     # C-like: arrays carry no length, so trust conventional names, but only if indexed
        names = "|".join(p.cfg.length_params)
        pats.append((re.compile(rf"<=\s*(?:{names})\b(?!\s*[-/*])"), 0.55, "inclusive bound on a length-like parameter"))
    for loop in A.nodes_of_kind(p, "loop"):
        head = A.loop_header(p, loop)
        for rx, conf, desc in pats:
            m = rx.search(head)
            if not m:
                continue
            body = p.code_text(A.loop_body(loop))
            lv = _LOOPVAR.search(head)
            indexed = bool(lv and re.search(r"\[\s*" + re.escape(lv.group(1)) + r"\s*\]", body))
            if desc.startswith("inclusive bound on a length-like") and not indexed:
                continue
            if indexed:
                conf = min(0.95, conf + 0.08)
            hits.append(Hit("loop_bound_off_by_one", A.line_of(loop),
                            f"{desc}: `{' '.join(m.group(0).split())}`"
                            + (" and the loop variable indexes the collection" if indexed else ""),
                            conf, key=head.strip()))
            break
    # variable initialised to the length, later used as an inclusive bound
    for fn in A.functions(p):
        text = p.code_text(fn)
        for m in re.finditer(rf"\b(\w+)\s*(?::=|=)\s*{LEN}\s*(?:;|\n|$)", text):
            var = m.group(1)
            for loop in A.nodes_of_kind(p, "loop", fn):
                head = A.loop_header(p, loop)
                if re.search(rf"<=\s*{re.escape(var)}\b|\b{re.escape(var)}\s*>=", head) \
                        and "[" in text:
                    hits.append(Hit("loop_bound_off_by_one", A.line_of(loop),
                                    f"`{var}` starts at the collection length but is used as an inclusive bound",
                                    0.6, key=f"init:{var}:{head.strip()}"))
    return _dedupe(hits)


@rule("missing_base_case", "missing_base_case", ["base_cases", "recursion"])
def r_base_case(p: Parsed) -> list:
    """Function calls itself but contains no conditional (if / ternary / match / switch) at all."""
    hits = []
    for fn in A.functions(p):
        name = A.function_name(p, fn)
        if not name:
            continue
        body = A.function_body(fn)
        text = p.code_text(body)
        rx = rf"(?:(?<![\w.])|(?<=self\.)|(?<=this\.)|(?<=cls\.)){re.escape(name)}\s*\("
        m = re.search(rx, text)
        if not m:
            continue
        if any(True for _ in A.nodes_of_kind(p, "conditional", body)):
            continue
        hits.append(Hit("missing_base_case", A.line_of(fn),
                        f"`{name}` calls itself but has no conditional, so nothing can stop the recursion",
                        0.85, key=f"{name}:{text.strip()[:80]}"))
    return hits


@rule("mutation_during_iteration", "mutation_during_iteration", ["iteration_safety"])
def r_mutation(p: Parsed) -> list:
    """Collection is structurally modified inside a for-each loop that iterates over it."""
    hits = []
    if not p.cfg.foreach_iterable:
        return hits
    it_rx = re.compile(p.cfg.foreach_iterable)
    muts = "|".join(re.escape(m) for m in p.cfg.mutators)
    for loop in A.nodes_of_kind(p, "loop"):
        if not A.is_foreach(p, loop):
            continue
        head = A.loop_header(p, loop).strip()
        m = it_rx.search(head)
        if not m:
            continue
        x = re.escape(m.group("it"))
        body_node = A.loop_body(loop)
        body = p.code_text(body_node)
        pats = [rf"\b{x}\s*(?:\.|->|\?\.)\s*(?:{muts})\s*\("]
        pats += [t.replace("{X}", x) for t in p.cfg.extra_mutation]
        for pat in pats:
            mm = re.search(pat, body)
            if mm:
                line = _line_at(body_node.start_point[0], body, mm.start())
                hits.append(Hit("mutation_during_iteration", line,
                                f"`{m.group('it')}` is modified while the loop on line {A.line_of(loop)} iterates over it",
                                0.85, key=f"{m.group('it')}:{head}"))
                break
    return hits


_VISIT = {"append", "add", "push", "push_back", "emplace_back", "print", "println", "printf",
          "Println", "Printf", "Print", "visit", "process", "write", "writeln", "log", "Add",
          "Write", "WriteLine", "puts", "echo"}
_ORDER = {"in": "RVR", "pre": "VRR", "post": "RRV"}
_ORDER_DESC = {"V": "visit", "R": "recurse"}


@rule("traversal_order", "wrong_traversal_order", ["tree_traversal", "recursion"])
def r_traversal(p: Parsed) -> list:
    """A function named pre/in/post-order whose visit/recurse sequence does not match its name."""
    hits = []
    for fn in A.functions(p):
        name = A.function_name(p, fn) or ""
        m = re.search(r"(?i)(pre|in|post)[_]?order", name)
        if not m:
            continue
        kind = m.group(1).lower()
        events = []
        for c in A.calls(p, A.function_body(fn)):
            cn = A.callee_name(p, c)
            if cn == name:
                events.append(("R", c))
            elif cn in _VISIT and not any(cn == A.callee_name(p, a) for a in A.ancestors(c) if p.cfg.is_kind(a.type, "call")):
                events.append(("V", c))
        seq = "".join(e for e, _ in events)
        if seq.count("R") != 2 or seq.count("V") != 1:
            continue                      # style we cannot judge (e.g. concatenating return values)
        if seq != _ORDER[kind]:
            v = next(c for e, c in events if e == "V")
            hits.append(Hit("traversal_order", A.line_of(v),
                            f"`{name}` does: {', '.join(_ORDER_DESC[e] for e in seq)}; "
                            f"that is not the {kind}-order pattern its name promises",
                            0.8, key=f"{name}:{seq}"))
    return hits


@rule("nested_loop_quadratic", "avoidable_nested_loops", ["time_complexity"])
def r_nested(p: Parsed) -> list:
    """Loop nested inside another loop of the same function (candidate for O(n^2) that may be avoidable)."""
    hits = []
    for fn in A.functions(p):
        seen = set()
        for loop in A.nodes_of_kind(p, "loop", fn):
            outer = [a for a in A.ancestors(loop) if a is not fn and p.cfg.is_kind(a.type, "loop")
                     and a.start_byte >= fn.start_byte]
            if not outer or id(outer[-1]) in seen:
                continue
            seen.add(id(outer[-1]))
            hits.append(Hit("nested_loop_quadratic", A.line_of(loop),
                            f"loop on line {A.line_of(loop)} is nested inside the loop on line {A.line_of(outer[-1])}",
                            0.5, key=f"{A.line_of(outer[-1])}:{A.loop_header(p, outer[-1]).strip()}"))
    return hits


_UNSAFE = [
    r"(?P<x>[A-Za-z_]\w*)\s*\[\s*(?:0|-1)\s*\]",
    r"(?P<x>[A-Za-z_]\w*)\s*\[\s*len\(\s*(?P=x)\s*\)\s*-\s*1\s*\]",
    r"(?P<x>[A-Za-z_]\w*)\s*\[\s*(?P=x)\.(?:length|size\(\))\s*-\s*1\s*\]",
    r"(?P<x>[A-Za-z_]\w*)\s*(?:\.|->)\s*(?i:pop|peek|top|back|front|first|last|pop_back|removeFirst|removeLast|getFirst|getLast|element|shift|dequeue)\s*\(\s*\)",
    r"(?P<x>[A-Za-z_]\w*)\s*(?:\.|->|\?\.)\s*(?i:next|val|value|left|right|data|prev)\b",
]
_UNSAFE_RX = [re.compile(x) for x in _UNSAFE]
_ALIAS = re.compile(r"^\s*(?:[\w<>\[\]*&:]+\s+)*(\w+)\s*(?::=|=)\s*(\w+)\s*;?\s*$")


@rule("missing_null_check", "missing_null_check", ["edge_cases"])
def r_null(p: Parsed) -> list:
    """Reads the first/last element, pops, or dereferences a value with no emptiness/null guard before it."""
    hits = []
    for fn in A.functions(p):
        body = A.function_body(fn)
        text = p.code_text(body)
        lines = text.split("\n")
        base = body.start_point[0]
        alias = {}
        for ln in lines:
            m = _ALIAS.match(ln)
            if m and m.group(1) != m.group(2):
                alias.setdefault(m.group(1), set()).add(m.group(2))

        def closure(x):
            seen, todo = {x}, [x]
            while todo:
                for y in alias.get(todo.pop(), ()):
                    if y not in seen:
                        seen.add(y); todo.append(y)
            return seen

        guards = []   # (row, line text without the unsafe accesses)
        for n in walk(body):
            if n.is_named and (p.cfg.is_kind(n.type, "conditional") or p.cfg.is_kind(n.type, "loop")):
                row = n.start_point[0]
                guards.append((row, lines[row - base] if 0 <= row - base < len(lines) else ""))
        flagged = set()
        for i, ln in enumerate(lines):
            row = base + i
            for rx in _UNSAFE_RX:
                for m in rx.finditer(ln):
                    x = m.group("x")
                    if x in flagged or x in ("self", "this"):
                        continue
                    names = closure(x)
                    guarded = False
                    for grow, gtxt in guards:
                        if grow > row:
                            continue
                        stripped = gtxt
                        for r2 in _UNSAFE_RX:
                            stripped = r2.sub(" ", stripped) if grow == row else stripped
                        if any(re.search(rf"\b{re.escape(nm)}\b", stripped) for nm in names):
                            guarded = True
                            break
                    if guarded:
                        continue
                    flagged.add(x)
                    hits.append(Hit("missing_null_check", row + 1,
                                    f"`{x}` is accessed (`{m.group(0).strip()}`) with no emptiness/null check before it",
                                    0.5, key=f"{x}:{m.group(0)}"))
    return hits


def _dedupe(hits: list) -> list:
    seen, out = set(), []
    for h in hits:
        k = (h.rule, h.line)
        if k not in seen:
            seen.add(k)
            out.append(h)
    return out


def run_rules(p: Parsed, only: set | None = None) -> list:
    out = []
    for rid, r in RULES.items():
        if only is not None and rid not in only:
            continue
        out.extend(r.fn(p))
    return out
