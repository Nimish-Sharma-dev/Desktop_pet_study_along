"""Test-runner adapters. Add a language: subclass Adapter in adapters.py and register it here."""
from .base import RunnerError, Adapter, Step, run_tests
from . import adapters as _a

ADAPTERS = {
    "python": _a.PythonAdapter, "javascript": _a.JavaScriptAdapter, "typescript": _a.TypeScriptAdapter,
    "go": _a.GoAdapter, "java": _a.JavaAdapter, "cpp": _a.CppAdapter, "rust": _a.RustAdapter,
    "c_sharp": _a.CSharpAdapter, "kotlin": _a.KotlinAdapter,
}


def get_adapter(language: str) -> Adapter:
    try:
        return ADAPTERS[language]()
    except KeyError:
        raise RunnerError(f"no test adapter for {language!r}; supported: {sorted(ADAPTERS)}")
