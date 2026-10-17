#!/usr/bin/env python3
"""Generate starter/ and tests/<lang>/{visible,hidden}/ for every lesson from its cases.yaml.

cases.yaml is the single source of truth for test cases, so adding a language means adding one
renderer here + one adapter in daemon/analysis/runners, not rewriting every lesson.

Value specs:  literals | {gen: range, args: [start,count,step]} | {gen: chain_edges, args: [n]}
Expected:     literal | {eval: "<python expression>"}   (evaluated here for Java/Go)
Types:        int bool string int_list int_list_list linked_list
"""
import json, re, sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
LANGS = ["python", "javascript", "go", "java"]


def camel(s): p = s.split("_"); return p[0] + "".join(x.title() for x in p[1:])
def pascal(s): return "".join(x.title() for x in s.split("_"))


def resolve(v):
    """-> python value for literals/eval; gen specs stay as dicts."""
    if isinstance(v, dict) and "eval" in v:
        return eval(v["eval"])
    return v


def gen_values(spec):
    if spec["gen"] == "range":
        s, c, st = spec["args"]; return list(range(s, s + c * st, st))
    if spec["gen"] == "chain_edges":
        return [[i, i + 1] for i in range(spec["args"][0] - 1)]


# ------------------------------------------------------------------ java
def java_lit(kind, v):
    if isinstance(v, dict) and "gen" in v:
        a = v["args"]
        return f"LessonKit.range({a[0]}, {a[1]}, {a[2]})" if v["gen"] == "range" else f"LessonKit.chainEdges({a[0]})"
    if kind in ("int_list", "linked_list"):
        return "new int[]{" + ",".join(map(str, v)) + "}"
    if kind == "int_list_list":
        return "new int[][]{" + ",".join("{" + ",".join(map(str, r)) + "}" for r in v) + "}"
    if kind == "string": return json.dumps(v)
    if kind == "bool": return "true" if v else "false"
    if kind == "long": return f"{v}L"
    return str(v)


def go_lit(kind, v):
    if isinstance(v, dict) and "gen" in v:
        a = v["args"]
        return f"lessonRange({a[0]}, {a[1]}, {a[2]})" if v["gen"] == "range" else f"lessonChainEdges({a[0]})"
    if kind in ("int_list", "linked_list"):
        return "[]int{" + ",".join(map(str, v)) + "}"
    if kind == "int_list_list":
        return "[][]int{" + ",".join("{" + ",".join(map(str, r)) + "}" for r in v) + "}"
    if kind == "string": return json.dumps(v)
    if kind == "bool": return "true" if v else "false"
    return str(v)


JAVA_T = {"long": "long", "int": "int", "bool": "boolean", "string": "String", "int_list": "int[]", "int_list_list": "int[][]", "linked_list": "ListNode"}
GO_T = {"long": "int", "int": "int", "bool": "bool", "string": "string", "int_list": "[]int", "int_list_list": "[][]int", "linked_list": "*ListNode"}
PY_T = {"long": "int", "int": "int", "bool": "bool", "string": "str", "int_list": "list[int]", "int_list_list": "list[list[int]]", "linked_list": "ListNode | None"}

PRE = {
 "python": "class ListNode:\n    def __init__(self, val=0, next=None):\n        self.val = val\n        self.next = next\n\n\n",
 "go": "type ListNode struct {\n\tVal  int\n\tNext *ListNode\n}\n\n",
 "java": "    public static class ListNode {\n        int val;\n        ListNode next;\n        ListNode(int val, ListNode next) { this.val = val; this.next = next; }\n    }\n\n",
}


def starter(lang, data):
    fns, ll = data["functions"], data.get("helpers") == "linked_list"
    title = data["title"]
    if lang == "python":
        out = f'"""Lesson: {title}. Replace each TODO. Keep the function names and signatures."""\n\n\n' + (PRE["python"] if ll else "")
        for f in fns:
            sig = ", ".join(f"{p['name']}: {PY_T[p['type']]}" for p in f["params"])
            out += f'def {f["name"]}({sig}) -> {PY_T[f["returns"]]}:\n    """{f["doc"]}"""\n    # TODO(student): implement {f["name"]}\n    raise NotImplementedError("TODO")\n\n\n'
        return out.rstrip() + "\n"
    if lang == "javascript":
        out = f"// Lesson: {title}. Replace each TODO. Keep the function names and signatures.\n\n"
        if ll: out += "class ListNode {\n  constructor(val = 0, next = null) {\n    this.val = val;\n    this.next = next;\n  }\n}\n\n"
        for f in fns:
            out += f'// {f["doc"]}\nfunction {camel(f["name"])}({", ".join(p["name"] for p in f["params"])}) {{\n  // TODO(student): implement {camel(f["name"])}\n  throw new Error("TODO");\n}}\n\n'
        return out + "module.exports = { " + ", ".join(camel(f["name"]) for f in fns) + (", ListNode" if ll else "") + " };\n"
    if lang == "go":
        out = f"// Lesson: {title}. Replace each TODO. Keep the function names and signatures.\npackage solution\n\n" + (PRE["go"] if ll else "")
        for f in fns:
            sig = ", ".join(f"{p['name']} {GO_T[p['type']]}" for p in f["params"])
            out += f'// {f["doc"]}\nfunc {pascal(f["name"])}({sig}) {GO_T[f["returns"]]} {{\n\t// TODO(student): implement {pascal(f["name"])}\n\tpanic("TODO")\n}}\n\n'
        return out.rstrip() + "\n"
    if lang == "java":
        out = f"// Lesson: {title}. Replace each TODO. Keep the class, method names and signatures.\npublic class Solution {{\n" + (PRE["java"] if ll else "")
        for f in fns:
            sig = ", ".join(f"{JAVA_T[p['type']]} {p['name']}" for p in f["params"])
            out += f'    // {f["doc"]}\n    public static {JAVA_T[f["returns"]]} {camel(f["name"])}({sig}) {{\n        // TODO(student): implement {camel(f["name"])}\n        throw new UnsupportedOperationException("TODO");\n    }}\n\n'
        return out.rstrip() + "\n}\n"


def tests(lang, data, hidden):
    out = ""
    ll = data.get("helpers") == "linked_list"
    cases = [(f, c) for f in data["functions"] for c in f["cases"] if bool(c.get("hidden")) == hidden]
    if not cases: return None
    kind = "hidden" if hidden else "visible"
    if lang == "python":
        out = "from lessonkit import check\n\n"
        for f, c in cases:
            out += f'\ndef test_{c["name"]}():\n    check({f["name"]!r}, {[p["type"] for p in f["params"]]!r}, {f["returns"]!r}, {c["args"]!r}, {resolve(c["expected"])!r})\n'
        return f"test_{kind}.py", out
    if lang == "javascript":
        out = "const { check } = require('./lessonkit');\n\n"
        for f, c in cases:
            out += f"test({json.dumps(c['name'])}, () => {{\n  check({json.dumps(camel(f['name']))}, {json.dumps([p['type'] for p in f['params']])}, {json.dumps(f['returns'])}, {json.dumps(c['args'])}, {json.dumps(resolve(c['expected']))});\n}});\n\n"
        return f"{kind}.test.js", out
    if lang == "go":
        out = 'package solution\n\nimport "testing"\n\n'
        for f, c in cases:
            args = ", ".join(go_lit(p["type"], a) for p, a in zip(f["params"], c["args"]))
            args = ", ".join(("fromList(" + go_lit("int_list", a) + ")") if p["type"] == "linked_list" else go_lit(p["type"], a) for p, a in zip(f["params"], c["args"]))
            call = f'{pascal(f["name"])}({args})'
            if f["returns"] == "linked_list": call = f"toList({call})"
            exp = resolve(c["expected"])
            out += f'func Test_{c["name"]}(t *testing.T) {{\n\trunCase(t, func() interface{{}} {{ return {call} }}, {go_lit("int_list" if f["returns"]=="linked_list" else f["returns"], exp)})\n}}\n\n'
        return f"{kind}_test.go", out
    if lang == "java":
        cls = "VisibleTest" if not hidden else "HiddenTest"
        out = "import org.junit.jupiter.api.Test;\n\npublic class " + cls + " {\n"
        for f, c in cases:
            args = ", ".join(("ListKit.fromList(" + java_lit("int_list", a) + ")") if p["type"] == "linked_list" else java_lit(p["type"], a) for p, a in zip(f["params"], c["args"]))
            call = f'Solution.{camel(f["name"])}({args})'
            if f["returns"] == "linked_list": call = f"ListKit.toList({call})"
            exp = resolve(c["expected"])
            out += f'    @Test\n    void {c["name"]}() {{\n        LessonKit.check(() -> {call}, {java_lit("int_list" if f["returns"]=="linked_list" else f["returns"], exp)});\n    }}\n\n'
        return f"{cls}.java", out + "}\n"


GO_LIST = '''package solution

func fromList(a []int) *ListNode {
	var head *ListNode
	for i := len(a) - 1; i >= 0; i-- {
		head = &ListNode{Val: a[i], Next: head}
	}
	return head
}

func toList(h *ListNode) []int {
	out := []int{}
	for n := 0; h != nil; n++ {
		if n > 1000000 {
			panic("returned list has a cycle")
		}
		out = append(out, h.Val)
		h = h.Next
	}
	return out
}
'''
JAVA_LIST = '''public class ListKit {
    public static Solution.ListNode fromList(int[] a) {
        Solution.ListNode head = null;
        for (int i = a.length - 1; i >= 0; i--) head = new Solution.ListNode(a[i], head);
        return head;
    }

    public static int[] toList(Solution.ListNode h) {
        java.util.ArrayList<Integer> out = new java.util.ArrayList<>();
        int n = 0;
        while (h != null) {
            if (++n > 1000000) throw new IllegalStateException("returned list has a cycle");
            out.add(h.val);
            h = h.next;
        }
        return out.stream().mapToInt(Integer::intValue).toArray();
    }
}
'''
SOL_NAME = {"python": "solution.py", "javascript": "solution.js", "go": "solution.go", "java": "Solution.java"}


def generate_lesson(d, langs=LANGS):
    """Write starter/ and tests/ for one lesson directory from its cases.yaml."""
    d = Path(d)
    data = yaml.safe_load((d / "cases.yaml").read_text())
    if True:
        for lang in langs:
            (d / "starter").mkdir(exist_ok=True)
            (d / "starter" / SOL_NAME[lang]).write_text(starter(lang, data))
            for hidden in (False, True):
                r = tests(lang, data, hidden)
                if not r: continue
                tdir = d / "tests" / lang / ("hidden" if hidden else "visible")
                tdir.mkdir(parents=True, exist_ok=True)
                (tdir / r[0]).write_text(r[1])
                if not hidden and data.get("helpers") == "linked_list":
                    if lang == "go": (tdir / "listhelpers_test.go").write_text(GO_LIST)
                    if lang == "java": (tdir / "ListKit.java").write_text(JAVA_LIST)


def main(only=None):
    for d in sorted(ROOT.iterdir()):
        if not (d / "cases.yaml").exists() or (only and d.name != only): continue
        generate_lesson(d)
        print("generated", d.name)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
