# ABOUTME: Tests for uxdrift/github.py — gh CLI wrapper with safe error handling
from __future__ import annotations

import subprocess
import unittest
from unittest.mock import call, patch

from uxdrift.github import create_issue


class TestCreateIssue(unittest.TestCase):
    def test_create_issue_calls_gh(self) -> None:
        with patch("subprocess.check_call") as mock_call:
            create_issue(repo="org/repo", title="Bug found", body="Details here")
        mock_call.assert_called_once()
        args = mock_call.call_args[0][0]
        self.assertIn("gh", args)
        self.assertIn("--repo", args)
        self.assertIn("org/repo", args)
        self.assertIn("--title", args)
        self.assertIn("Bug found", args)
        self.assertIn("--body", args)
        self.assertIn("Details here", args)

    def test_create_issue_with_labels(self) -> None:
        with patch("subprocess.check_call") as mock_call:
            create_issue(repo="org/repo", title="T", body="B", labels=["ux", "p1"])
        args = mock_call.call_args[0][0]
        # --label ux and --label p1 should both appear
        label_idx = [i for i, a in enumerate(args) if a == "--label"]
        self.assertEqual(len(label_idx), 2)
        label_values = [args[i + 1] for i in label_idx]
        self.assertIn("ux", label_values)
        self.assertIn("p1", label_values)

    def test_create_issue_no_labels(self) -> None:
        with patch("subprocess.check_call") as mock_call:
            create_issue(repo="org/repo", title="T", body="B", labels=None)
        args = mock_call.call_args[0][0]
        self.assertNotIn("--label", args)

    def test_create_issue_empty_labels_ignored(self) -> None:
        with patch("subprocess.check_call") as mock_call:
            create_issue(repo="org/repo", title="T", body="B", labels=["", "  "])
        args = mock_call.call_args[0][0]
        self.assertNotIn("--label", args)

    def test_subprocess_error_does_not_raise(self) -> None:
        with patch("subprocess.check_call", side_effect=subprocess.CalledProcessError(1, "gh")):
            # Must not raise — just log
            create_issue(repo="org/repo", title="T", body="B")

    def test_gh_not_found_does_not_raise(self) -> None:
        with patch("subprocess.check_call", side_effect=FileNotFoundError("No such file")):
            create_issue(repo="org/repo", title="T", body="B")
