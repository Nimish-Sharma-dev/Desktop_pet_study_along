"""Pure functions: framework output text -> list of raw results

    {"name": <native name>, "passed": bool, "message": str, "info": {...}|None}

`info` is the structured payload our lesson kit embeds in every failure message
(`LESSON_FAIL {"expected":..,"actual":..,"error_type":..}`), so all frameworks give us
expected/actual/error_type the same way. When the payload is absent (build failure,
crash, plain assertion from a hand-written test) `info` is None.
"""
from __future__ import annotations
import json
import re
import xml.etree.ElementTree as ET

_FAIL_RX = re.compile(r"LESSON_FAIL (\{.*\})")


def extract_info(text: str) -> dict | None:
    for line in (text or "").splitlines():
        m = _FAIL_RX.search(line)
        if m:
            try:
                return json.loads(m.group(1))
            except json.JSONDecodeError:
                return None
    return None


def _res(name, passed, message="", skipped=False):
    return {"name": name, "passed": passed, "message": (message or "")[:4000],
            "info": None if passed else extract_info(message), "skipped": skipped}


# ----------------------------------------------------------------------------- JUnit-style XML
def parse_junit_xml(text: str) -> list:
    """pytest --junitxml, JUnit5 console launcher reports, GoogleTest --gtest_output=xml,
    Catch2 -r junit, Kotlin/JUnit. All share <testcase> with <failure>/<error>/<skipped>."""
    if not text.strip():
        return []
    root = ET.fromstring(text)
    out = []
    for tc in root.iter("testcase"):
        name = tc.get("name", "")
        bad = tc.find("failure")
        if bad is None:
            bad = tc.find("error")
        if tc.find("skipped") is not None:
            out.append(_res(name, False, "skipped", skipped=True))
        elif bad is not None:
            msg = (bad.get("message") or "") + "\n" + (bad.text or "")
            out.append(_res(name, False, msg))
            if bad.get("type") and out[-1]["info"] is None:
                out[-1]["exception"] = bad.get("type")
        else:
            out.append(_res(name, True))
    return out


# ----------------------------------------------------------------------------- xUnit.net v2 XML
def parse_xunit_xml(text: str) -> list:
    """xunit v2 native XML (<assemblies><assembly><collection><test result=Pass|Fail>)."""
    if not text.strip():
        return []
    root = ET.fromstring(text)
    out = []
    for t in root.iter("test"):
        name = t.get("name", "")
        res = (t.get("result") or "").lower()
        if res == "pass":
            out.append(_res(name, True))
        elif res == "skip":
            out.append(_res(name, False, "skipped", skipped=True))
        else:
            f = t.find("failure")
            msg = ""
            if f is not None:
                m = f.find("message")
                st = f.find("stack-trace")
                msg = (m.text if m is not None and m.text else "") + "\n" + (st.text if st is not None and st.text else "")
            out.append(_res(name, False, msg))
    return out


# ----------------------------------------------------------------------------- go test -json
def parse_go_test_json(text: str) -> list:
    outputs: dict = {}
    final: dict = {}
    order: list = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = ev.get("Test")
        if not t:
            continue
        if t not in order:
            order.append(t)
        if ev.get("Action") == "output":
            outputs.setdefault(t, []).append(ev.get("Output", ""))
        elif ev.get("Action") in ("pass", "fail", "skip"):
            final[t] = ev["Action"]
    out = []
    for t in order:
        if "/" in t or t not in final:
            continue            # sub-tests and tests that never finished are handled by the caller
        msg = "".join(outputs.get(t, []))
        out.append(_res(t, final[t] == "pass", "" if final[t] == "pass" else msg, skipped=final[t] == "skip"))
    return out


# ----------------------------------------------------------------------------- Jest / Vitest --json
def parse_jest_json(text: str) -> list:
    text = text.strip()
    if not text:
        return []
    start = text.find("{")
    data = json.loads(text[start:])
    out = []
    for suite in data.get("testResults", []):
        asserts = suite.get("assertionResults") or suite.get("tests") or []
        for a in asserts:
            name = a.get("title") or a.get("name", "")
            st = a.get("status")
            if st == "passed":
                out.append(_res(name, True))
            elif st in ("pending", "skipped", "todo"):
                out.append(_res(name, False, "skipped", skipped=True))
            else:
                msg = "\n".join(a.get("failureMessages") or []) or a.get("message", "")
                out.append(_res(name, False, msg))
        if not asserts and suite.get("status") == "failed":
            out.append({"name": "<suite>", "passed": False, "message": (suite.get("message") or "")[:4000],
                        "info": None, "skipped": False, "suite_error": True})
    return out


# ----------------------------------------------------------------------------- cargo test (libtest text)
def parse_cargo_test(text: str) -> list:
    res = {}
    order = []
    for m in re.finditer(r"^test (\S+) \.\.\. (ok|FAILED|ignored)", text, re.M):
        name, st = m.group(1), m.group(2)
        order.append(name)
        res[name] = st
    details = {}
    for m in re.finditer(r"^---- (\S+) stdout ----\n(.*?)(?=^---- |\n^failures:|\Z)", text, re.M | re.S):
        details[m.group(1)] = m.group(2)
    out = []
    for n in order:
        if res[n] == "ok":
            out.append(_res(n, True))
        elif res[n] == "ignored":
            out.append(_res(n, False, "ignored", skipped=True))
        else:
            out.append(_res(n, False, details.get(n, "")))
    return out
