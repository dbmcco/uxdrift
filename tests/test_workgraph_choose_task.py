from __future__ import annotations

import unittest
from pathlib import Path

from uxrift.workgraph import Workgraph, choose_task_id


class TestChooseTaskId(unittest.TestCase):
    def test_prefers_in_progress(self) -> None:
        wg = Workgraph(
            wg_dir=Path("/tmp/.workgraph"),
            project_dir=Path("/tmp"),
            tasks={
                "a": {"kind": "task", "id": "a", "status": "open"},
                "b": {"kind": "task", "id": "b", "status": "in-progress"},
            },
        )
        self.assertEqual(choose_task_id(wg), "b")

    def test_falls_back_to_open(self) -> None:
        wg = Workgraph(
            wg_dir=Path("/tmp/.workgraph"),
            project_dir=Path("/tmp"),
            tasks={
                "a": {"kind": "task", "id": "a", "status": "open"},
            },
        )
        self.assertEqual(choose_task_id(wg), "a")

    def test_errors_on_multiple(self) -> None:
        wg = Workgraph(
            wg_dir=Path("/tmp/.workgraph"),
            project_dir=Path("/tmp"),
            tasks={
                "a": {"kind": "task", "id": "a", "status": "open"},
                "b": {"kind": "task", "id": "b", "status": "open"},
            },
        )
        with self.assertRaises(ValueError):
            choose_task_id(wg)

