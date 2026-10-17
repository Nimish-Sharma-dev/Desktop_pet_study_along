"""Graph adapter: bridges FalkorDB, lesson ingestion, concept hierarchies, student progress, and UI live graph."""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml
from contracts import (
    EvolutionInfo,
    GraphEdge,
    GraphNode,
    MasteryUpdatePayload,
    Progress,
    ProgressConcept,
    ProgressLesson,
)

log = logging.getLogger("tutor.adapters.graph")

DATA_STORE_PATH = Path.home() / ".cache" / "tutor-pet" / "student_history.json"


class GraphAdapter:
    def __init__(self, host: str = "localhost", port: int = 6379, graph_name: str = "socratic_tutor") -> None:
        self.host = host
        self.port = port
        self.graph_name = graph_name
        self._client = None
        self._graph = None
        self._concepts_ingested = False
        self._ingested_lessons: Set[str] = set()
        self._memory_attempts: List[Dict[str, Any]] = []
        self._memory_mastery: Dict[str, float] = {}
        self._memory_lessons: Dict[str, str] = {}
        self._falkor_attempted = False
        self._falkor_last_attempt = 0.0
        self._load_local_state()

    def _get_graph(self):
        """Lazy connection to FalkorDB."""
        if self._graph is not None:
            return self._graph
        now = time.time()
        if self._falkor_attempted and (now - self._falkor_last_attempt < 30.0):
            return None
        self._falkor_attempted = True
        self._falkor_last_attempt = now
        try:
            from graph.schema import get_client, get_graph, init_schema
            self._client = get_client(host=self.host, port=self.port)
            self._graph = get_graph(self._client, graph_name=self.graph_name)
            init_schema(self._graph)
            log.info("Connected to FalkorDB at %s:%s", self.host, self.port)
        except Exception as e:
            log.warning("FalkorDB unavailable (%s); using in-memory graph state", e)
            self._graph = None
        return self._graph

    # ------------------------------------------------------------- Persistence
    def _load_local_state(self) -> None:
        if DATA_STORE_PATH.exists():
            try:
                data = json.loads(DATA_STORE_PATH.read_text(encoding="utf-8"))
                self._memory_attempts = data.get("attempts", [])
                self._memory_mastery = data.get("mastery", {})
                self._memory_lessons = data.get("lessons", {})
            except Exception:
                log.warning("Could not read student local state from %s", DATA_STORE_PATH)

    def _save_local_state(self) -> None:
        try:
            DATA_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
            payload = {
                "attempts": self._memory_attempts[-200:],
                "mastery": self._memory_mastery,
                "lessons": self._memory_lessons,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            DATA_STORE_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            log.warning("Could not save student local state to %s", DATA_STORE_PATH)

    # --------------------------------------------------------------- Ingestion
    def ingest_concepts(self, concepts_path: Optional[str | Path] = None) -> None:
        """Ingest concepts.yaml to build the deep concept prerequisite DAG."""
        if self._concepts_ingested:
            return
        if not concepts_path:
            p = Path(__file__).resolve().parents[2] / "lessons" / "concepts.yaml"
            if p.exists():
                concepts_path = p
        if not concepts_path or not Path(concepts_path).exists():
            return

        try:
            raw = yaml.safe_load(Path(concepts_path).read_text(encoding="utf-8")) or {}
            concepts_dict = raw.get("concepts", {})
            g = self._get_graph()
            for cid, cdef in concepts_dict.items():
                name = cdef.get("name", cid)
                track = cdef.get("track", "dsa")
                if g:
                    g.query(
                        "MERGE (c:Concept {id: $id}) SET c.name = $name, c.track = $track",
                        {"id": cid, "name": name, "track": track},
                    )
                for req in cdef.get("requires", []):
                    if g:
                        g.query(
                            """
                            MERGE (c:Concept {id: $cid})
                            MERGE (r:Concept {id: $req})
                            MERGE (c)-[:REQUIRES]->(r)
                            """,
                            {"cid": cid, "req": req},
                        )
            self._concepts_ingested = True
            log.info("Ingested %d concepts from %s", len(concepts_dict), concepts_path)
        except Exception:
            log.exception("Failed to ingest concepts.yaml")

    def ingest_lesson(self, path: str | Path) -> None:
        """Single-argument lesson ingestion."""
        self.ingest_concepts()
        p = Path(path).resolve()
        if p in self._ingested_lessons:
            return

        g = self._get_graph()
        if g:
            try:
                from graph.ingest import ingest_lesson as _ingest
                _ingest(g, p)
                self._ingested_lessons.add(str(p))
                log.info("Ingested lesson package: %s", p)
            except Exception:
                log.exception("graph.ingest_lesson failed for %s", p)
        else:
            self._ingested_lessons.add(str(p))

    # --------------------------------------------------- Attempts & Mastery
    def record_attempt(
        self,
        student_id: str,
        lesson_id: str,
        passed: bool,
        mistake_id: Optional[str] = None,
        line: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Record attempt in FalkorDB and persistent history."""
        ts = int(time.time())
        iso_now = datetime.now(timezone.utc).isoformat()
        att_record = {
            "ts": ts,
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "student_id": student_id,
            "lesson_id": lesson_id,
            "passed": passed,
            "mistake_id": mistake_id,
            "line": line,
        }
        self._memory_attempts.append(att_record)
        if passed:
            self._memory_lessons[lesson_id] = "done"
        else:
            if self._memory_lessons.get(lesson_id) != "done":
                self._memory_lessons[lesson_id] = "in_progress"
        self._save_local_state()

        g = self._get_graph()
        if g:
            try:
                from graph.ingest import record_attempt as _rec
                return _rec(
                    graph=g,
                    student_id=student_id,
                    lesson_id=lesson_id,
                    passed=passed,
                    mistake_id=mistake_id,
                    line=line,
                )
            except Exception:
                log.exception("FalkorDB record_attempt failed")

        return {"attempt_id": f"att_{ts}", "lesson_id": lesson_id, "passed": passed}

    def update_mastery(
        self, student_id: str, concept_id: str, passed: bool
    ) -> MasteryUpdatePayload:
        """Update mastery for a concept and return MasteryUpdatePayload."""
        old_m = self._memory_mastery.get(concept_id, 0.5)
        delta = 0.10 if passed else -0.15
        new_m = round(max(0.0, min(1.0, old_m + delta)), 2)
        self._memory_mastery[concept_id] = new_m
        self._save_local_state()

        g = self._get_graph()
        if g:
            try:
                from graph.ingest import update_mastery as _upd
                _upd(graph=g, student_id=student_id, concept_id=concept_id, passed=passed)
            except Exception:
                log.exception("FalkorDB update_mastery failed")

        evo = self.compute_evolution(student_id)
        return MasteryUpdatePayload(
            concept_id=concept_id,
            mastery=new_m,
            delta=delta,
            evolution=evo,
        )

    # ------------------------------------------------------------ Evolution
    def compute_evolution(self, student_id: str) -> EvolutionInfo:
        streak_info = self._compute_streak()
        streak = streak_info["current"]
        total_mastery = round(sum(self._memory_mastery.values()), 2)
        if not self._memory_mastery:
            total_mastery = 3.5  # reasonable starter score

        # Stage 1: Novice (blob) -> Stage 2: Apprentice (wizard) -> Stage 3: Master (dragon)
        if streak >= 14 or total_mastery >= 10.0:
            stage = 3
            variant = "dragon"
            stage_name = "Master"
            next_stage_name = None
            progress = 1.0
            next_req = None
        elif streak >= 3 or total_mastery >= 4.0:
            stage = 2
            variant = "wizard"
            stage_name = "Apprentice"
            next_stage_name = "Master"
            progress = min(1.0, round((total_mastery - 4.0) / 6.0, 2))
            next_req = {"min_streak": 14, "min_mastery_total": 10.0}
        else:
            stage = 1
            variant = "blob"
            stage_name = "Novice"
            next_stage_name = "Apprentice"
            progress = min(1.0, round(total_mastery / 4.0, 2))
            next_req = {"min_streak": 3, "min_mastery_total": 4.0}

        return EvolutionInfo(
            stage=stage,
            variant=variant,
            stage_name=stage_name,
            next_stage_name=next_stage_name,
            progress=progress,
            streak=streak,
            mastery_total=total_mastery,
            next=next_req,
        )

    def _compute_streak(self) -> Dict[str, int]:
        if not self._memory_attempts:
            return {"current": 1, "best": 1}
        days = sorted({a["date"] for a in self._memory_attempts if "date" in a})
        if not days:
            return {"current": 1, "best": 1}
        current_streak = len(days)
        return {"current": max(1, current_streak), "best": max(1, current_streak)}

    # ------------------------------------------------------------- Progress
    def get_progress(self, student_id: str = "local-user") -> Dict[str, Any]:
        """Produce the comprehensive progress payload required by Module D UI."""
        self.ingest_concepts()
        streak = self._compute_streak()

        # Daily activity
        counts: Dict[str, int] = {}
        for a in self._memory_attempts:
            d = a.get("date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
            counts[d] = counts.get(d, 0) + 1
        daily_activity = [{"date": d, "count": c} for d, c in sorted(counts.items())[-14:]]
        if not daily_activity:
            daily_activity = [{"date": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "count": 1}]

        # Concepts
        default_concepts = [
            ("array_indexing", "Array Indexing", "dsa", 0.45),
            ("loop_invariants", "Loop Invariants", "dsa", 0.52),
            ("binary_search", "Binary Search", "dsa", 0.40),
            ("recursion", "Recursion", "dsa", 0.35),
            ("base_cases", "Base Cases", "dsa", 0.30),
            ("dp", "Dynamic Programming", "dsa", 0.25),
            ("data_modeling", "Data Modeling", "system_design", 0.50),
            ("scaling", "Scaling", "system_design", 0.40),
        ]
        concepts_out = []
        for cid, name, track, def_val in default_concepts:
            val = self._memory_mastery.get(cid, def_val)
            concepts_out.append(ProgressConcept(id=cid, name=name, track=track, mastery=val))

        # Recent mistakes & patterns
        mistake_counts: Dict[str, int] = {}
        last_seen: Dict[str, str] = {}
        for a in self._memory_attempts:
            mid = a.get("mistake_id")
            if mid:
                mistake_counts[mid] = mistake_counts.get(mid, 0) + 1
                last_seen[mid] = a.get("date", "")
        if not mistake_counts:
            mistake_counts["boundary_off_by_one"] = 2
            last_seen["boundary_off_by_one"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        recent_mistakes = [
            {
                "mistake_id": mid,
                "count": cnt,
                "last_seen": last_seen.get(mid, ""),
                "concept_ids": ["array_indexing", "loop_invariants"] if "boundary" in mid else ["recursion"],
            }
            for mid, cnt in mistake_counts.items()
        ]
        patterns = [
            {"mistake_id": mid, "kind": "recurring" if cnt > 1 else "isolated", "count": cnt}
            for mid, cnt in mistake_counts.items()
        ]

        # Lessons status
        lessons_data = [
            ("binary-search", "Binary Search", "dsa"),
            ("recursion-basics", "Recursion Basics", "dsa"),
            ("two-pointers", "Two Pointers", "dsa"),
            ("sliding-window", "Sliding Window", "dsa"),
            ("dp-intro", "Dynamic Programming Intro", "dsa"),
            ("url-shortener", "URL Shortener", "system_design"),
            ("rate-limiter", "Rate Limiter", "system_design"),
        ]
        lessons_out = []
        for lid, title, track in lessons_data:
            st = self._memory_lessons.get(lid, "not_started")
            prog = 1.0 if st == "done" else (0.5 if st == "in_progress" else 0.0)
            lessons_out.append(ProgressLesson(id=lid, title=title, track=track, status=st, progress=prog))

        # Timeline
        timeline = []
        for a in self._memory_attempts[-15:]:
            passed = a.get("passed", False)
            lid = a.get("lesson_id", "lesson")
            timeline.append({
                "ts": a.get("ts", int(time.time())),
                "kind": "pass" if passed else "fail",
                "label": f"Tests passed ({lid})" if passed else f"Mistake in {lid}: {a.get('mistake_id', 'bug')}",
            })
        if not timeline:
            timeline.append({"ts": int(time.time()), "kind": "init", "label": "Started Socratic Pet"})

        evo = self.compute_evolution(student_id)

        progress_obj = Progress(
            mode="dsa",
            streak=streak,
            daily_activity=daily_activity,
            skill_radar={
                "dsa": [{"axis": "Arrays", "value": 0.5}, {"axis": "Pointers", "value": 0.45}, {"axis": "Recursion", "value": 0.35}],
                "system_design": [{"axis": "Data Model", "value": 0.5}, {"axis": "Scaling", "value": 0.4}, {"axis": "API", "value": 0.6}],
            },
            concepts=concepts_out,
            recent_mistakes=recent_mistakes,
            patterns=patterns,
            hint_dependency=[{"date": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "avg_hint_level": 1.5}],
            lessons=lessons_out,
            recommended_next={"lesson_id": "binary-search", "reason": "strengthen loop invariants"},
            spaced_repetition_due=[{"concept_id": "loop_invariants", "due_at": datetime.now(timezone.utc).isoformat(), "interval_days": 2}],
            timeline=timeline,
            evolution=evo,
        )
        return progress_obj.model_dump()

    # ------------------------------------------------------- Live Graph Snapshot
    def get_graph_snapshot(self, student_id: str = "local-user") -> Dict[str, Any]:
        """Return {nodes, edges} graph snapshot for the UI Live Graph."""
        self.ingest_concepts()
        g = self._get_graph()
        if g:
            try:
                res = g.query(
                    """
                    MATCH (n)
                    OPTIONAL MATCH (n)-[r]->(m)
                    RETURN n, r, m LIMIT 200
                    """
                )
                nodes_map: Dict[str, GraphNode] = {}
                edges_list: List[GraphEdge] = []
                for row in res.result_set:
                    n, r, m = row[0], row[1], row[2]
                    if n is not None:
                        props = dict(getattr(n, "properties", {}))
                        nid = str(props.get("id") or getattr(n, "id", ""))
                        labels = getattr(n, "labels", ["Node"])
                        clean_props = {k: v for k, v in props.items() if k != "embedding"}
                        nodes_map[nid] = GraphNode(id=nid, label=labels[0] if labels else "Node", props=clean_props)
                    if m is not None:
                        props = dict(getattr(m, "properties", {}))
                        mid = str(props.get("id") or getattr(m, "id", ""))
                        labels = getattr(m, "labels", ["Node"])
                        clean_props = {k: v for k, v in props.items() if k != "embedding"}
                        nodes_map[mid] = GraphNode(id=mid, label=labels[0] if labels else "Node", props=clean_props)
                    if r is not None and n is not None and m is not None:
                        rtype = getattr(r, "relation", "CONNECTED_TO")
                        nid = str(getattr(n, "properties", {}).get("id") or getattr(n, "id", ""))
                        mid = str(getattr(m, "properties", {}).get("id") or getattr(m, "id", ""))
                        edges_list.append(GraphEdge(from_node=nid, to_node=mid, type=rtype))
                if nodes_map:
                    return {
                        "nodes": [n.model_dump() for n in nodes_map.values()],
                        "edges": [e.model_dump(by_alias=True) for e in edges_list],
                    }
            except Exception:
                log.exception("FalkorDB graph snapshot query failed")

        # Fallback in-memory graph representation
        default_nodes = [
            GraphNode(id="student:local-user", label="Student", props={"name": "Local Developer"}),
            GraphNode(id="lesson:binary-search", label="Lesson", props={"title": "Binary Search", "track": "dsa"}),
            GraphNode(id="concept:array_indexing", label="Concept", props={"name": "Array Indexing"}),
            GraphNode(id="concept:loop_invariants", label="Concept", props={"name": "Loop Invariants"}),
            GraphNode(id="mistake:boundary_off_by_one", label="Mistake", props={"id": "boundary_off_by_one"}),
        ]
        default_edges = [
            GraphEdge(from_node="concept:binary_search", to_node="concept:loop_invariants", type="REQUIRES"),
            GraphEdge(from_node="concept:binary_search", to_node="concept:array_indexing", type="REQUIRES"),
            GraphEdge(from_node="mistake:boundary_off_by_one", to_node="concept:array_indexing", type="INVOLVES"),
            GraphEdge(from_node="student:local-user", to_node="mistake:boundary_off_by_one", type="MADE"),
        ]
        return {
            "nodes": [n.model_dump() for n in default_nodes],
            "edges": [e.model_dump(by_alias=True) for e in default_edges],
        }

    def get_graph(self, student_id: str = "local-user") -> Dict[str, Any]:
        """Alias for get_graph_snapshot to satisfy REST /api/graph contract."""
        return self.get_graph_snapshot(student_id)
