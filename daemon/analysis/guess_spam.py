"""Guess-spam detection from AST diffs between consecutive *clean* snapshots.

For every snapshot that parses without syntax errors we compute two structural fingerprints:

  alpha  - ordered AST shape with local variables alpha-renamed per function
           (x, y -> ID0, ID1 by first occurrence). Two snapshots with equal alpha
           fingerprints have the same control flow AND the same data flow; they differ
           only in variable names / formatting / comments.
  bag    - AST shape with real names but with the children of block-like nodes sorted.
           Equal bag fingerprints => the same statements in a different order.

An edit between consecutive clean snapshots is classified:

  neutral   comments / whitespace only          (ignored: neither counts nor resets)
  rename    alpha equal, names differ
  reshuffle bag equal, statements moved, and no two statements that share an identifier
            changed relative order (so data flow is unchanged)
  revert    returns to the structure of a snapshot from 2-6 edits ago (flip-flopping)
  real      anything else (control flow or data flow changed)  -> resets the streak

`threshold` consecutive rename/reshuffle/revert edits => guess_spam. Snapshots with syntax
errors (mid-keystroke states) are skipped, so typing a genuine rewrite character by
character never counts as noise: each time the buffer parses again it differs structurally
from the last clean one ("real").
"""
from __future__ import annotations
import difflib
import hashlib
import re
import sys
from collections import deque
from dataclasses import dataclass, field

from .parser import Parsed, parse

sys.setrecursionlimit(max(sys.getrecursionlimit(), 20000))


def _h(s: str) -> str:
    return hashlib.blake2b(s.encode(), digest_size=10).hexdigest()


@dataclass
class Fingerprint:
    alpha: str
    bag: str
    idents: tuple                  # sorted renamable identifier occurrences
    code_norm: str                 # comments removed, whitespace collapsed
    blocks: dict = field(default_factory=dict)   # block bag-hash -> [(stmt bag-hash, frozenset idents)]


def _renamable(p: Parsed, n) -> bool:
    if n.type not in p.cfg.rename_node_types:
        return False
    nxt = p.src[n.end_byte:n.end_byte + 8].lstrip()[:1]
    if nxt == b"(":
        return False                                   # callee / declaration name: keep literal
    prev = p.src[max(0, n.start_byte - 3):n.start_byte].rstrip()
    return not (prev.endswith(b".") or prev.endswith(b"->") or prev.endswith(b"::"))


def fingerprint(p: Parsed) -> Fingerprint:
    cfg = p.cfg
    idents: list = []
    blocks: dict = {}

    def alpha(n, scope: dict) -> str:
        if cfg.is_kind(n.type, "comment"):
            return ""
        if cfg.is_kind(n.type, "string"):
            return "STR"
        if cfg.is_kind(n.type, "function"):
            scope = {}
        if n.child_count == 0:
            if n.is_named and _renamable(p, n):
                t = p.text(n)
                return scope.setdefault(t, f"ID{len(scope)}")
            return f"{n.type}:{p.text(n)}" if n.is_named else n.type
        return "(" + n.type + " " + " ".join(s for s in (alpha(c, scope) for c in n.children) if s) + ")"

    def bag(n):
        """returns (shape, idents frozenset)"""
        if cfg.is_kind(n.type, "comment"):
            return "", frozenset()
        if cfg.is_kind(n.type, "string"):
            return "STR", frozenset()
        if n.child_count == 0:
            if n.is_named and _renamable(p, n):
                t = p.text(n)
                idents.append(t)
                return f"ID:{t}", frozenset([t])
            return (f"{n.type}:{p.text(n)}" if n.is_named else n.type), frozenset()
        parts = [bag(c) for c in n.children]
        ids = frozenset().union(*[x[1] for x in parts]) if parts else frozenset()
        shapes = [s for s, _ in parts if s]
        if cfg.is_kind(n.type, "block"):
            named = [(s, i) for (s, i), c in zip(parts, n.children) if s and c.is_named]
            shapes_sorted = sorted(shapes)
            shape = "{" + n.type + " " + " ".join(shapes_sorted) + "}"
            blocks.setdefault(_h(shape), []).append(named)
            return shape, ids
        return "(" + n.type + " " + " ".join(shapes) + ")", ids

    a = _h(alpha(p.root, {}))
    bshape, _ = bag(p.root)
    stripped = p.code_text(p.root)
    # code_text blanks comments/strings; collapse whitespace to compare "same program text"
    norm = re.sub(r"\s+", "", stripped)
    return Fingerprint(a, _h(bshape), tuple(sorted(idents)), norm, blocks)


def _dependent_reorder(a: Fingerprint, b: Fingerprint) -> bool:
    """True if some pair of statements sharing an identifier changed relative order."""
    for key, a_list in a.blocks.items():
        b_list = b.blocks.get(key)
        if not b_list:
            continue
        for sa, sb in zip(a_list, b_list):
            if [s for s, _ in sa] == [s for s, _ in sb]:
                continue
            pos: dict = {}
            for j, (s, _) in enumerate(sb):
                pos.setdefault(s, deque()).append(j)
            perm = []
            for s, _ in sa:
                q = pos.get(s)
                if not q:
                    return True
                perm.append(q.popleft())
            for i in range(len(sa)):
                for j in range(i + 1, len(sa)):
                    if perm[i] > perm[j] and (sa[i][1] & sa[j][1]):
                        return True
    return False


def classify_edit(prev: Fingerprint, new: Fingerprint, history: list) -> str:
    if prev.code_norm == new.code_norm:
        return "neutral"
    if prev.alpha == new.alpha:
        return "rename" if prev.idents != new.idents else "neutral"
    if prev.bag == new.bag and prev.idents == new.idents and not _dependent_reorder(prev, new):
        return "reshuffle"
    if any(h.alpha == new.alpha for h in history[:-1][-6:]):
        return "revert"
    return "real"


@dataclass
class _Stream:
    clean: list = field(default_factory=list)      # [(text, Fingerprint)]
    run: int = 0
    kinds: list = field(default_factory=list)


@dataclass
class SpamSignal:
    line: int
    evidence: str
    confidence: float
    kinds: list


class GuessSpamDetector:
    def __init__(self, threshold: int = 3, history: int = 8):
        self.threshold = threshold
        self.history = history
        self.streams: dict = {}

    def reset(self, key=None):
        if key is None:
            self.streams.clear()
        else:
            self.streams.pop(key, None)

    def observe(self, key, code: str, lang: str, cursor_line: int | None = None) -> SpamSignal | None:
        """Feed one buffer snapshot. Returns a SpamSignal when the streak threshold is reached."""
        p = parse(code, lang)
        if p.has_errors or not code.strip():
            return None                                  # mid-keystroke state: ignore entirely
        fp = fingerprint(p)
        st = self.streams.setdefault(key, _Stream())
        if st.clean and st.clean[-1][0] == code:
            return None
        sig = None
        if st.clean:
            prev_text, prev_fp = st.clean[-1]
            kind = classify_edit(prev_fp, fp, [f for _, f in st.clean])
            if kind in ("rename", "reshuffle", "revert"):
                st.run += 1
                st.kinds.append(kind)
            elif kind == "real":
                st.run, st.kinds = 0, []
            if st.run >= self.threshold:
                line = _first_changed_line(prev_text, code) or (cursor_line or 1)
                kinds = st.kinds[-self.threshold:]
                what = {"rename": "renamed variables", "reshuffle": "moved lines around",
                        "revert": "flipped back to an earlier version"}
                evidence = (f"last {len(kinds)} edits only " +
                            ", ".join(sorted({what[k] for k in kinds})) +
                            "; control flow and data flow are unchanged")
                conf = 0.6 + 0.1 * min(3, st.run - self.threshold) + (0.1 if len(set(kinds)) == 1 else 0)
                sig = SpamSignal(line, evidence, min(conf, 0.9), kinds)
                st.run, st.kinds = 0, []
        st.clean.append((code, fp))
        del st.clean[:-self.history]
        return sig


def _first_changed_line(a: str, b: str) -> int | None:
    al, bl = a.splitlines(), b.splitlines()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, al, bl, autojunk=False).get_opcodes():
        if tag != "equal":
            return j1 + 1
    return None
