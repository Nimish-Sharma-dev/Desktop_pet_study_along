# `/lessons`

```
lessons/
  concepts.yaml                  concept REQUIRES graph (+ Socratic questions, optional runnable drills)
  <lesson-id>/
    lesson.yaml                  Contract 6 (exactly those keys)
    README.md                    the student-facing problem statement
    cases.yaml                   single source of truth for test cases (visible + hidden)   [code lessons]
    starter/                     solution.py solution.js solution.go Solution.java, TODO markers   [generated]
    tests/<lang>/visible|hidden/ native tests (pytest / Jest / go test / JUnit 5)               [generated]
    reference/                   known-good solutions (never shown to students)
    seeded_bugs.yaml             patches/full-file variants that MUST fail
    rubric.yaml, starter/design.md, reference/design.md              [system-design lessons]
  _support/<lang>/               test kit per language (timeouts, LESSON_FAIL format)
  _templates/                    micro-lesson template + base system-design rubric
  _tools/gen_lessons.py          cases.yaml -> starter/ + tests/       (python lessons/_tools/gen_lessons.py [id])
  _tools/verify_lessons.py       acceptance check (reference passes; starter + seeded bugs fail; static bugs map to the same mistake_id)
```

Lessons: binary-search, two-pointers, sliding-window, recursion-basics, linked-list-reversal, graph-bfs-dfs, dp-intro,
hash-maps, stacks-queues (DSA, 4 languages each) and url-shortener, rate-limiter (system design: `design.md` + diagram, scored 0-5 on 8 axes).

## `lesson.yaml` conventions
`prerequisites` are **lesson ids**; `concepts` and `common_mistakes[].concepts` are ids from `concepts.yaml`;
system-design lessons use `languages: [any]`. `common_mistakes[].signals` is how a finding becomes a `mistake_id`:

| signal | matches |
|---|---|
| `rule:<rule_id>` | a static rule (`loop_bound_off_by_one`, `missing_base_case`, `mutation_during_iteration`, `traversal_order`, `nested_loop_quadratic`, `missing_null_check`) |
| `test:<glob>` | a failing test, e.g. `test:test_hidden_single_*` (names are `test_<case name>`) |
| `error:<Type>` | a failure's neutral error type: `WrongAnswer IndexError NullReference RecursionError Timeout MemoryError CompileError Crash` |
| `diag:<class>` | an editor/compiler diagnostic class (`undefined_name`, `syntax_error`, `type_mismatch`, ...) |
| `rubric:<axis>` | a rubric gap (`requirements estimation data_model api scaling bottlenecks failure_handling tradeoffs diagram`) |

Crash/timeout `error:` signals win over `test:` signals; plain wrong answers use `test:` first.

## Adding a lesson
1. `lesson.yaml`, `README.md`, `cases.yaml` (use `{gen: range, args: [start,count,step]}` or `{gen: chain_edges, args:[n]}` for big inputs; keep the **hidden** cases for edge cases and performance).
2. `reference/` solutions in each language (keep `hi = len(x) - 1`-style bounds as separate statements), `seeded_bugs.yaml`
   (`patches` = exact one-match text replacements, or `full` files; mark `static: <mistake_id>` for bugs the analyzer must flag; `static_only: [lang]` when tests cannot see it).
3. `python lessons/_tools/gen_lessons.py <id>` then `PYTHONPATH=daemon python lessons/_tools/verify_lessons.py <id>`.

## Micro-lessons
`analysis.microlesson.root_weak_concept(concept, mastery)` finds the deepest weak prerequisite;
`generate_micro_lesson(concept)` writes `lessons/micro-<concept>/` from `_templates/micro-lesson` (a runnable Python drill if the concept has one in `concepts.yaml`,
otherwise a conversational lesson from its `questions`).

## Rules for the pet
Nothing in `starter/`, `README.md` or the findings `evidence` contains a corrected solution; `reference/` and hidden-test expected values must never be sent to the UI or the model.
