from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from uxdrift.playwright_runner import PageEvidence
from uxdrift.report import build_report, render_markdown


class TestReportMarkdown(unittest.TestCase):
    def test_render_markdown_smoke(self) -> None:
        pages = [
            PageEvidence(
                name="root",
                url="http://example.com/",
                artifacts={"screenshot": "/tmp/x.png"},
                timing_ms={"navigation": 123},
                console={"messages": [], "counts": {"error": 0, "warning": 0}},
                network={"request_failures": [], "http_errors": [], "counts": {"request_failures": 0, "http_errors": 0}},
                page_errors=[],
                extracted={"title": "Example", "text": "Hello"},
            )
        ]
        report = build_report(
            run_meta={"base_url": "http://example.com", "browser": "chromium"},
            pages=pages,
            goals=["Test goal"],
            non_goals=[],
            llm_block=None,
        )
        md = render_markdown(report)
        self.assertIn("# uxdrift report", md)
        self.assertIn("Deterministic Findings", md)
        self.assertIn("Pages", md)

