# ABOUTME: UXdrift workgraph helpers — SDK base plus uxdrift-specific task chooser.
# ABOUTME: Re-exports Workgraph, find_workgraph_dir, load_workgraph from SDK.

from __future__ import annotations

from speedrift_lane_sdk.workgraph import (  # noqa: F401
    Workgraph,
    find_workgraph_dir,
    load_workgraph,
)


def choose_task_id(wg: Workgraph) -> str:
    """Auto-select a task when --task is not provided."""
    if wg.tasks is None:
        raise ValueError("choose_task_id requires eager-loaded workgraph (use load_workgraph)")

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
