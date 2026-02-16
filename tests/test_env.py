from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

from uxdrift.env import load_dotenv


class TestEnv(unittest.TestCase):
    def test_load_dotenv_sets_missing_vars(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / ".env"
            p.write_text("FOO=bar\n# comment\nBAZ=\"qux\"\n", encoding="utf-8")
            os.environ.pop("FOO", None)
            os.environ.pop("BAZ", None)

            load_dotenv(dotenv_path=p)

            self.assertEqual(os.environ.get("FOO"), "bar")
            self.assertEqual(os.environ.get("BAZ"), "qux")

    def test_load_dotenv_does_not_override(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / ".env"
            p.write_text("FOO=bar\n", encoding="utf-8")
            os.environ["FOO"] = "existing"

            load_dotenv(dotenv_path=p)

            self.assertEqual(os.environ.get("FOO"), "existing")

