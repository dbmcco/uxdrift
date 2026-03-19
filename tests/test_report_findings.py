# ABOUTME: Tests for report.summarize_deterministic_findings — all severity branches
from __future__ import annotations

import unittest

from uxdrift.types import PageEvidence
from uxdrift.report import summarize_deterministic_findings


def _page(
    name: str = "root",
    console_errors: int = 0,
    console_warnings: int = 0,
    request_failures: int = 0,
    http_errors: int = 0,
    page_errors: list[str] | None = None,
    screenshot: str = "/tmp/shot.png",
) -> PageEvidence:
    return PageEvidence(
        name=name,
        url=f"http://example.com/{name}",
        artifacts={"screenshot": screenshot},
        timing_ms={"navigation": 100},
        console={
            "messages": [],
            "counts": {"error": console_errors, "warning": console_warnings},
        },
        network={
            "request_failures": [],
            "http_errors": [],
            "counts": {"request_failures": request_failures, "http_errors": http_errors},
        },
        page_errors=page_errors or [],
        extracted={"title": name, "text": ""},
    )


class TestSummarizeDeterministicFindings(unittest.TestCase):
    def test_clean_page_no_findings(self) -> None:
        findings = summarize_deterministic_findings([_page()])
        self.assertEqual(findings, [])

    def test_console_errors_produce_high(self) -> None:
        findings = summarize_deterministic_findings([_page(console_errors=2)])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "high")
        self.assertEqual(findings[0]["category"], "glitch")
        self.assertEqual(findings[0]["details"]["console_error_count"], 2)

    def test_page_errors_produce_high(self) -> None:
        findings = summarize_deterministic_findings([_page(page_errors=["TypeError: x"])])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "high")
        self.assertEqual(findings[0]["details"]["page_error_count"], 1)

    def test_console_errors_and_page_errors_single_high_finding(self) -> None:
        # Both conditions → still one "high" finding per page
        findings = summarize_deterministic_findings(
            [_page(console_errors=1, page_errors=["Error"])]
        )
        high = [f for f in findings if f["severity"] == "high"]
        self.assertEqual(len(high), 1)

    def test_request_failures_produce_medium(self) -> None:
        findings = summarize_deterministic_findings([_page(request_failures=3)])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "medium")
        self.assertEqual(findings[0]["details"]["request_failure_count"], 3)

    def test_http_errors_produce_medium(self) -> None:
        findings = summarize_deterministic_findings([_page(http_errors=1)])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "medium")
        self.assertEqual(findings[0]["details"]["http_error_count"], 1)

    def test_warnings_produce_low(self) -> None:
        findings = summarize_deterministic_findings([_page(console_warnings=5)])
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["severity"], "low")
        self.assertEqual(findings[0]["details"]["console_warning_count"], 5)

    def test_multiple_issues_multiple_findings(self) -> None:
        page = _page(
            console_errors=1,
            request_failures=2,
            console_warnings=3,
        )
        findings = summarize_deterministic_findings([page])
        severities = {f["severity"] for f in findings}
        self.assertIn("high", severities)
        self.assertIn("medium", severities)
        self.assertIn("low", severities)
        self.assertEqual(len(findings), 3)

    def test_multiple_pages_aggregated(self) -> None:
        pages = [
            _page(name="page1", console_errors=1),
            _page(name="page2", request_failures=1),
        ]
        findings = summarize_deterministic_findings(pages)
        self.assertEqual(len(findings), 2)
        names_in_summaries = [f["summary"] for f in findings]
        self.assertTrue(any("page1" in s for s in names_in_summaries))
        self.assertTrue(any("page2" in s for s in names_in_summaries))

    def test_finding_references_screenshot(self) -> None:
        findings = summarize_deterministic_findings([_page(console_errors=1, screenshot="/shots/s.png")])
        self.assertEqual(len(findings), 1)
        self.assertIn("/shots/s.png", findings[0]["evidence"])

    def test_empty_pages_list(self) -> None:
        self.assertEqual(summarize_deterministic_findings([]), [])
