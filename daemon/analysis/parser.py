"""Tree-sitter loading, driven entirely by languages.yaml (no per-language Python code)."""
from __future__ import annotations
import importlib
import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

_CFG_PATH = Path(os.environ.get("ANALYSIS_LANGUAGES", Path(__file__).with_name("languages.yaml")))

_ALIASES = {"csharp": "c_sharp", "cs": "c_sharp", "c#": "c_sharp", "c++": "cpp", "js": "javascript",
            "ts": "typescript", "golang": "go", "py": "python", "kt": "kotlin",
            "typescriptreact": "typescript", "javascriptreact": "javascript"}


@dataclass
class LangConfig:
    name: str
    module: str
    factory: str
    extensions: list
    kinds: dict
    param_style: str
    mutators: list
    rename_node_types: list
    foreach_iterable: str | None
    foreach_if_child: dict
    bound_patterns: list
    extra_mutation: list
    length_params: list
    _kind_sets: dict = field(default_factory=dict, repr=False)

    def is_kind(self, node_type: str, kind: str) -> bool:
        s = self._kind_sets.get(kind)
        if s is None:
            s = self._kind_sets[kind] = set(self.kinds.get(kind, []))
        return node_type in s


@lru_cache(maxsize=1)
def _raw() -> dict:
    return yaml.safe_load(_CFG_PATH.read_text())


def diagnostic_classes() -> dict:
    return _raw().get("diagnostic_classes", {})


def supported_languages() -> list:
    return sorted(_raw()["languages"])


def detect_language(path: str | None = None, hint: str | None = None) -> str | None:
    names = _raw()["languages"]
    if hint:
        h = hint.lower().strip().replace("-", "_")
        h = _ALIASES.get(h, h)
        if h in names:
            return h
    if path:
        ext = os.path.splitext(path)[1].lower()
        for n, c in names.items():
            if ext in c.get("extensions", []):
                return n
    return None


@lru_cache(maxsize=None)
def get_config(lang: str) -> LangConfig:
    raw = _raw()
    if lang not in raw["languages"]:
        raise KeyError(f"unsupported language {lang!r}; add it to languages.yaml")
    d = dict(raw.get("defaults", {}))
    d.update(raw["languages"][lang])
    return LangConfig(
        name=lang, module=d["module"], factory=d["factory"], extensions=d["extensions"],
        kinds=d["kinds"], param_style=d.get("param_style", "name_colon"),
        mutators=d.get("mutators", []), rename_node_types=d.get("rename_node_types", ["identifier"]),
        foreach_iterable=d.get("foreach_iterable"), foreach_if_child=d.get("foreach_if_child", {}),
        bound_patterns=d.get("bound_patterns", []), extra_mutation=d.get("extra_mutation", []),
        length_params=d.get("length_params", []))


@lru_cache(maxsize=None)
def _parser(lang: str):
    from tree_sitter import Language, Parser
    cfg = get_config(lang)
    mod = importlib.import_module(cfg.module)
    return Parser(Language(getattr(mod, cfg.factory)()))


@dataclass
class Parsed:
    lang: str
    cfg: LangConfig
    src: bytes
    tree: object

    @property
    def root(self):
        return self.tree.root_node

    @property
    def has_errors(self) -> bool:
        return self.root.has_error

    def text(self, node) -> str:
        return self.src[node.start_byte:node.end_byte].decode("utf8", "replace")

    def code_text(self, node) -> str:
        """Node text with comments and string-literal contents blanked out (same length),
        so regexes never match inside comments or strings."""
        start, end = node.start_byte, node.end_byte
        buf = bytearray(self.src[start:end])
        for n in walk(node):
            if self.cfg.is_kind(n.type, "comment") or self.cfg.is_kind(n.type, "string"):
                a, b = max(n.start_byte, start) - start, min(n.end_byte, end) - start
                for i in range(a, b):
                    if buf[i] not in (10, 13):
                        buf[i] = 32
        return buf.decode("utf8", "replace")


def parse(code: str, lang: str) -> Parsed:
    src = code.encode("utf8")
    return Parsed(lang, get_config(lang), src, _parser(lang).parse(src))


def walk(node):
    """Pre-order, document-order traversal."""
    stack = [node]
    while stack:
        n = stack.pop()
        yield n
        stack.extend(reversed(n.children))
