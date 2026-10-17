# `/daemon/analysis` - code analysis, test runners, sandbox (Module B)

Decides whether the student's code is wrong. **The tutor model never does** - everything here is deterministic
(tree-sitter rules, AST diffs, real tests in a sandbox, a regex rubric).

```python
from analysis import analyze, run_tests, test_results_to_findings, score_design
from analysis.microlesson import root_weak_concept, generate_micro_lesson

findings = analyze(event_batch, lesson)            # Contract 1 events -> [Finding]   (Contract 3, .to_dict())
result   = run_tests("binary-search", "java", workspace_dir)   # Contract 2 dict
findings += test_results_to_findings(result, lesson, file="Solution.java")
radar    = score_design("design.md", "url-shortener")          # axes, radar, gaps, findings
path     = generate_micro_lesson(root_weak_concept("dp", mastery))
```

## Setup (everything local, no cloud)

```bash
pip install tree-sitter pyyaml pytest \
  tree-sitter-python tree-sitter-java tree-sitter-c tree-sitter-cpp tree-sitter-c-sharp \
  tree-sitter-go tree-sitter-rust tree-sitter-javascript tree-sitter-typescript tree-sitter-kotlin
# test toolchains - install only the languages you teach:
#   python: pytest   javascript: node + `npm i -g jest`   go: go>=1.22
#   java: JDK 17+ and junit-platform-console-standalone.jar (apt: junit5; or set JUNIT_CONSOLE_JAR)
#   cpp: g++ + GoogleTest (apt: libgtest-dev)   typescript: `npm i -g vitest`
#   rust: cargo   c_sharp: dotnet (xUnit, offline NuGet cache)   kotlin: kotlinc + the JUnit jar
cd daemon
python -m pytest analysis/tests -q                 # unit + sandbox + end-to-end (~1-2 min)
PYTHONPATH=. python ../lessons/_tools/verify_lessons.py             # every lesson x language (several min)
python -m analysis.demo                            # the demo script (add --write-mocks to refresh /docs/mocks/b_*.json)
```

Optional env: `LESSONS_DIR`, `ANALYSIS_LANGUAGES` (alternate languages.yaml), `ANALYSIS_CACHE` (Go warm build cache),
`JEST_BIN`, `JUNIT_CONSOLE_JAR`, `SANDBOX_MODE=docker|subprocess`, `SANDBOX_IMAGE_<LANG>`.

## What is in here

| file | purpose |
|---|---|
| `languages.yaml` | **the only per-language static-analysis config**: grammar module, extensions, neutral-kind -> node-type map, mutators, ... |
| `parser.py`, `astutil.py` | tree-sitter loading; neutral helpers (function name/params, loop header/body, foreach, ...) |
| `rules.py` | the pattern rules, written once (see below) |
| `guess_spam.py` | AST-diff guess-spam detector |
| `analyzer.py` | `analyze()`, `test_results_to_findings()`, lesson loading and mistake mapping |
| `sandbox.py` | docker or locked-down subprocess backend |
| `runners/` | test adapters + parsers -> Contract 2 |
| `rubric.py` | system-design rubric scorer (radar) |
| `microlesson.py` | `root_weak_concept`, `generate_micro_lesson` |

## Rules (language-neutral; mapped per grammar through `languages.yaml`)

| rule id | default `mistake_id` | detects |
|---|---|---|
| `loop_bound_off_by_one` | `boundary_off_by_one` | `i <= len`, `range(len+1)`, `..=len`, countdown from `len`, a variable initialised to `len` used as an inclusive bound |
| `missing_base_case` | `missing_base_case` | function that calls itself and contains no conditional at all |
| `mutation_during_iteration` | `mutation_during_iteration` | for-each over X whose body appends/removes/... on X |
| `traversal_order` | `wrong_traversal_order` | `preorder`/`inorder`/`postorder` function whose visit/recurse sequence contradicts its name |
| `nested_loop_quadratic` | `avoidable_nested_loops` | loop nested in a loop (candidate - lesson must opt in) |
| `missing_null_check` | `missing_null_check` | `x[0]`, `x[-1]`, `x.pop()`, `x.peek()`, `x.next` ... with no emptiness/null guard before it (alias-aware) |

**Same bug, same `mistake_id`:** rules emit a *rule id*; a lesson maps it via `signals: ["rule:<id>"]` in
`common_mistakes`, so Python/Java/Go (and the other 7 grammars) produce the identical `mistake_id` and concepts.
With a lesson, only rules the lesson lists fire (so correct nested loops in a BFS lesson are never reported).
Without one, all rules fire with the defaults above.

Static rules run only when the buffer parses cleanly. Findings are de-duplicated per (student, file, mistake, line, code).

### Guess-spam (`guess_spam.py`)
Each clean snapshot gets an *alpha* fingerprint (locals alpha-renamed - same control+data flow) and a *bag*
fingerprint (statement order ignored). Edits are classified neutral / rename / reshuffle / revert / real; reordering two
statements that share a variable counts as **real** (data flow changed). 3 consecutive rename/reshuffle/revert edits emit
`guess_spam` - i.e. **detected on the 4th snapshot** for rename and reshuffle streaks, the 5th for operator flip-flopping
(the first flip is itself a real edit). Half-typed (unparseable) buffers are ignored, comment/whitespace edits are neutral, and a genuine rewrite typed
character by character is never flagged (tested).

## Sandbox (`sandbox.py`)

`capabilities()` reports what the host can enforce. With root + `setpriv` + `unshare` (as in the dev container, verified):
throw-away uid per run (so `RLIMIT_NPROC` stops fork bombs), private **network namespace** (no network), private mount
namespace with `/` read-only and only the work dir writable, `RLIMIT_CPU/DATA/FSIZE/NOFILE/NPROC`, process-group + uid
kill on wall timeout, scrubbed environment, captured+truncated output. Not root: rlimits + group kill only (`require_isolation=True` refuses to run). Docker backend (`--network none --read-only
--pids-limit --memory --cap-drop ALL`) is used automatically when `docker` exists - **written but untested here (no docker in the dev container)**.
Notes: dead fork-bomb children can show as zombies until the host's PID 1 reaps them (use `docker run --init` / tini);
the Go warm build cache is *copied* per run (never shared writable). The threat model is accidental infinite loops/memory, not a determined attacker - use the docker backend for anything stronger.

## Adding a language

*Static analysis only (config change):* `pip install tree-sitter-<lang>`, then add a block to `languages.yaml`:
`module`, `factory`, `extensions`, `kinds` (map neutral kinds `function, loop, foreach, conditional, call, comment, string, block`
to the grammar's node type names - use `tree-sitter parse` or `python -c "print(parse(code,lang).root)"` to find them), `param_style`
(`name_first|name_last|name_colon`), and optionally `foreach_iterable` (regex with `(?P<it>...)` over the loop header), `extra_mutation`,
`bound_patterns`, `length_params`. Then add a snippet to `tests/fixtures.py` - `test_rules.py` runs every rule against it.

*Test running (add a runner):* subclass `Adapter` in `runners/adapters.py` (`solution_files`, `build_steps`, `test_step`, `parse`) and register it in
`runners/__init__.py`; reuse a parser from `runners/parsers.py` (JUnit XML, xUnit XML, go test -json, Jest/Vitest JSON, cargo test).
*Lesson tests:* add a renderer to `lessons/_tools/gen_lessons.py` (`starter()` + `tests()`) and a kit in `lessons/_support/<lang>/`
(run the function under a hard timeout; on failure emit `LESSON_FAIL {"error_type","expected","actual","line","detail"}`), plus a reference solution per lesson.

## Verification status (honest)

| area | status |
|---|---|
| static rules | 10 grammars (py, java, c, cpp, c#, go, rust, js, ts, kotlin) x 6 rules, fixtures pass; correct-code fixtures give no false positives |
| runners end-to-end (real sandbox, real frameworks) | **python/pytest, javascript/Jest, go test, java/JUnit5** (all 9 code lessons x 4 langs via `verify_lessons.py`), **cpp/GoogleTest** (smoke test) |
| runners parser/command only (no toolchain installed to run them) | typescript/Vitest, rust/cargo, c#/xUnit, kotlin/JUnit. Parsers are unit-tested on recorded output shapes; the commands are unrun |
| docker backend | untested |
| lesson packs | 9 code lessons in 4 languages + 2 design lessons; no lesson tests yet for c, cpp, ts, rust, c#, kotlin |

## Limits of the rubric scorer
It measures **coverage** of topics (does the Estimation section have QPS, storage, a ratio, ...), by regex, inside the right section.
It cannot judge whether numbers are *right* or the design is *good*; keyword stuffing inside a section can raise a score. Use it to
decide what to ask about, not to grade. Pass = every axis >= 3, total >= 28/40, diagram present.

## Known limitations
* Line numbers are **1-based**. `line` is `0` when unknown (test failure with no stack frame), so it is always an int.
* C arrays carry no length, so C/C++ off-by-one relies on conventional names (`n`, `len`, `size`...), at lower confidence.
* `traversal_order` abstains for styles it cannot judge (e.g. concatenating returned lists).
* JS returns `undefined` for out-of-range reads, so some bugs are only caught statically in JS.
