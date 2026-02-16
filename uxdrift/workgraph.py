from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Workgraph:
    wg_dir: Path
    project_dir: Path
    tasks: dict[str, dict[str, Any]]

    def wg_log(self, task_id: str, message: str) -> None:
        subprocess.check_call(["wg", "--dir", str(self.wg_dir), "log", task_id, message])

    def ensure_task(
        self,
        *,
        task_id: str,
        title: str,
        description: str,
        blocked_by: list[str] | None = None,
        tags: list[str] | None = None,
    ) -> None:
        if task_id in self.tasks:
            return

        cmd = ["wg", "--dir", str(self.wg_dir), "add", title, "--id", task_id]
        if description:
            cmd += ["-d", description]
        if blocked_by:
            cmd += ["--blocked-by", *blocked_by]
        if tags:
            for t in tags:
                cmd += ["-t", t]
        subprocess.check_call(cmd)

        # Keep in-memory index in sync so repeated ensure_task calls stay idempotent.
        self.tasks[task_id] = {"kind": "task", "id": task_id, "title": title}


def find_workgraph_dir(explicit: Path | None) -> Path:
    if explicit:
        p = explicit
        if p.name != ".workgraph":
            p = p / ".workgraph"
        if not (p / "graph.jsonl").exists():
            raise FileNotFoundError(f"Workgraph not found at: {p}")
        return p

    cur = Path.cwd()
    for p in [cur, *cur.parents]:
        candidate = p / ".workgraph" / "graph.jsonl"
        if candidate.exists():
            return candidate.parent
    raise FileNotFoundError("Could not find .workgraph/graph.jsonl; pass --dir.")


def load_workgraph(wg_dir: Path) -> Workgraph:
    graph_path = wg_dir / "graph.jsonl"
    tasks: dict[str, dict[str, Any]] = {}
    for line in graph_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        obj = json.loads(line)
        if obj.get("kind") != "task":
            continue
        tid = str(obj.get("id"))
        tasks[tid] = obj

    return Workgraph(wg_dir=wg_dir, project_dir=wg_dir.parent, tasks=tasks)


def choose_task_id(wg: Workgraph) -> str:
    in_progress = [t for t in wg.tasks.values() if str(t.get("status") or "") == "in-progress"]
    if len(in_progress) == 1:
        return str(in_progress[0]["id"])
    if len(in_progress) > 1:
        raise ValueError(f"Multiple in-progress tasks found ({len(in_progress)}); pass --task <id>.")

    open_tasks = [t for t in wg.tasks.values() if str(t.get("status") or "") == "open"]
    if len(open_tasks) == 1:
        return str(open_tasks[0]["id"])
    if len(open_tasks) > 1:
        raise ValueError(f"Multiple open tasks found ({len(open_tasks)}); pass --task <id>.")

    raise ValueError("No open or in-progress tasks found; pass --task <id>.")

