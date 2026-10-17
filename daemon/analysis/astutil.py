"""Small helpers that translate grammar-specific trees into language-neutral questions
("what is this function called", "what is this loop's header", ...)."""
from __future__ import annotations
import re
from .parser import Parsed, walk

IDENT = re.compile(r"[A-Za-z_$][\w$]*")


def nodes_of_kind(p: Parsed, kind: str, root=None):
    for n in walk(root or p.root):
        if n.is_named and p.cfg.is_kind(n.type, kind):
            yield n


def functions(p: Parsed):
    return list(nodes_of_kind(p, "function"))


def line_of(node) -> int:
    """1-based line number."""
    return node.start_point[0] + 1


def _descend_declarator(node):
    # C / C++: function_definition -> declarator (-> declarator)* -> identifier
    d = node.child_by_field_name("declarator")
    while d is not None:
        nxt = d.child_by_field_name("declarator")
        if nxt is None:
            break
        d = nxt
    return d


def function_name(p: Parsed, fn) -> str | None:
    n = fn.child_by_field_name("name")
    if n is None:
        d = _descend_declarator(fn)
        if d is not None:
            n = d
    if n is None:
        for c in fn.children:
            if c.type in ("identifier", "simple_identifier", "property_identifier"):
                n = c
                break
    if n is None:
        return None
    txt = p.text(n)
    parts = re.split(r"::|\.", txt)
    m = IDENT.findall(parts[-1])
    return m[-1] if m else None


def function_body(fn):
    b = fn.child_by_field_name("body")
    if b is not None:
        return b
    for c in reversed(fn.named_children):
        if c.type in ("block", "function_body", "compound_statement", "statement_block"):
            return c
    return fn.named_children[-1] if fn.named_children else fn


def _find_params_node(fn):
    pn = fn.child_by_field_name("parameters")
    if pn is not None:
        return pn
    d = fn.child_by_field_name("declarator")
    while d is not None:
        pn = d.child_by_field_name("parameters")
        if pn is not None:
            return pn
        d = d.child_by_field_name("declarator")
    for c in fn.children:
        if c.type in ("function_value_parameters", "formal_parameters", "parameter_list", "parameters"):
            return c
    return None


def _split_top(s: str) -> list:
    out, depth, cur = [], 0, []
    for ch in s:
        if ch in "<([{":
            depth += 1
        elif ch in ">)]}":
            depth -= 1
        if ch == "," and depth == 0:
            out.append("".join(cur)); cur = []
        else:
            cur.append(ch)
    if "".join(cur).strip():
        out.append("".join(cur))
    return out


_SKIP = {"self", "this", "cls", "final", "const", "mut", "val", "var", "in", "out", "ref", "params", "readonly"}


def function_params(p: Parsed, fn) -> list:
    pn = _find_params_node(fn)
    if pn is None:
        return []
    inner = p.code_text(pn).strip()
    if inner.startswith("(") and inner.endswith(")"):
        inner = inner[1:-1]
    style = p.cfg.param_style
    names = []
    for chunk in _split_top(inner):
        c = chunk.strip()
        if not c:
            continue
        c = re.sub(r"=.*$", "", c).strip()          # defaults
        if style == "name_colon":
            c = c.split(":")[0]
            ids = [i for i in IDENT.findall(c) if i not in _SKIP]
            name = ids[-1] if ids else None
        elif style == "name_first":
            ids = [i for i in IDENT.findall(c) if i not in _SKIP]
            name = ids[0] if ids else None
        else:  # name_last
            c = re.sub(r"\[\s*\d*\s*\]", "", c)
            ids = [i for i in IDENT.findall(c) if i not in _SKIP]
            name = ids[-1] if ids else None
        if name and name not in names:
            names.append(name)
    return names


def loop_body(loop):
    b = loop.child_by_field_name("body")
    if b is not None:
        return b
    return loop.named_children[-1] if loop.named_children else loop


def loop_header(p: Parsed, loop) -> str:
    """Code between the loop keyword and its body (condition / iteration clause)."""
    body = loop_body(loop)
    if body is loop or body.start_byte <= loop.start_byte:
        return p.code_text(loop).split("\n", 1)[0]
    full = p.code_text(loop)
    head = full[: body.start_byte - loop.start_byte]
    if head.strip() in ("do", "do {"):          # do/while: condition follows the body
        cond = loop.child_by_field_name("condition")
        head += " " + (p.code_text(cond) if cond is not None else full[body.end_byte - loop.start_byte:])
    return head


def is_foreach(p: Parsed, loop) -> bool:
    if p.cfg.is_kind(loop.type, "foreach"):
        return True
    kids = p.cfg.foreach_if_child.get(loop.type)
    if kids:
        return any(c.type in kids for c in walk_shallow(loop, 2))
    return False


def walk_shallow(node, depth):
    yield node
    if depth > 0:
        for c in node.children:
            yield from walk_shallow(c, depth - 1)


def ancestors(node):
    n = node.parent
    while n is not None:
        yield n
        n = n.parent


def calls(p: Parsed, root):
    return list(nodes_of_kind(p, "call", root))


def callee_name(p: Parsed, call) -> str:
    """Last identifier of the callee path: `a.b.append(x)` -> `append`; `println!(..)` -> `println`."""
    t = p.code_text(call)
    head = t.split("(", 1)[0].split("!", 1)[0]
    ids = IDENT.findall(head)
    return ids[-1] if ids else ""
