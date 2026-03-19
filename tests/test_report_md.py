from __future__ import annotations

import unittest

from uxdrift.types import PageEvidence
from uxdrift.report import build_report, render_markdown


def _clean_page(name: str = "root") -> PageEvidence:
    return PageEvidence(
        name=name,
        url=f"http://example.com/{name}",
        artifacts={"screenshot": f"/tmp/{name}.png"},
        timing_ms={"navigation": 200},
        console={"messages": [], "counts": {"error": 0, "warning": 0}},
        network={"request_failures": [], "http_errors": [], "counts": {"request_failures": 0, "http_errors": 0}},
        page_errors=[],
        extracted={"title": name, "text": "Hello", "performance_navigation": None},
    )


class TestBuildReport(unittest.TestCase):
    def test_build_report_schema_keys(self) -> None:
        report = build_report(
            run_meta={"base_url": "http://example.com", "browser": "chromium"},
            pages=[_clean_page()],
            goals=["Test goal"],
            non_goals=["Not this"],
            llm_block=None,
        )
        for key in ("schema", "generated_at", "meta", "goals", "non_goals", "pov", "pages", "deterministic_findings", "llm"):
            self.assertIn(key, report, f"missing key: {key}")

    def test_build_report_schema_version(self) -> None:
        report = build_report(
            run_meta={}, pages=[], goals=[], non_goals=[], llm_block=None
        )
        self.assertEqual(report["schema"], 1)

    def test_build_report_llm_default(self) -> None:
        report = build_report(
            run_meta={}, pages=[], goals=[], non_goals=[], llm_block=None
        )
        self.assertEqual(report["llm"], {"enabled": False})

    def test_build_report_pov_default_empty_dict(self) -> None:
        report = build_report(
            run_meta={}, pages=[], goals=[], non_goals=[], llm_block=None
        )
        self.assertEqual(report["pov"], {})


class TestReportMarkdown(unittest.TestCase):
    def test_render_markdown_smoke(self) -> None:
        report = build_report(
            run_meta={"base_url": "http://example.com", "browser": "chromium"},
            pages=[_clean_page()],
            goals=["Test goal"],
            non_goals=[],
            llm_block=None,
        )
        md = render_markdown(report)
        self.assertIn("# uxdrift report", md)
        self.assertIn("Deterministic Findings", md)
        self.assertIn("Pages", md)

    def test_render_no_llm_no_findings(self) -> None:
        report = build_report(
            run_meta={"base_url": "http://example.com", "browser": "chromium"},
            pages=[_clean_page()],
            goals=[],
            non_goals=[],
            llm_block=None,
        )
        md = render_markdown(report)
        self.assertNotIn("LLM Critique", md)
        self.assertIn("(none)", md)  # no deterministic findings placeholder

    def test_render_multiple_pages(self) -> None:
        report = build_report(
            run_meta={"base_url": "http://example.com", "browser": "chromium"},
            pages=[_clean_page("page1"), _clean_page("page2")],
            goals=[],
            non_goals=[],
            llm_block=None,
        )
        md = render_markdown(report)
        self.assertIn("page1", md)
        self.assertIn("page2", md)

    def test_render_with_browser_channel(self) -> None:
        report = build_report(
            run_meta={"base_url": "http://x.com", "browser": "chromium", "browser_channel": "chrome"},
            pages=[],
            goals=[],
            non_goals=[],
            llm_block=None,
        )
        md = render_markdown(report)
        self.assertIn("Channel", md)
        self.assertIn("chrome", md)

    def test_render_step_screenshots_in_output(self) -> None:
        page = PageEvidence(
            name="checkout",
            url="http://example.com/checkout",
            artifacts={"screenshot": "/tmp/main.png", "step_screenshots": ["/tmp/step1.png", "/tmp/step2.png"]},
            timing_ms={"navigation": 100},
            console={"messages": [], "counts": {"error": 0, "warning": 0}},
            network={"request_failures": [], "http_errors": [], "counts": {"request_failures": 0, "http_errors": 0}},
            page_errors=[],
            extracted={"title": "Checkout", "text": ""},
        )
        report = build_report(run_meta={}, pages=[page], goals=[], non_goals=[], llm_block=None)
        md = render_markdown(report)
        self.assertIn("step1.png", md)
        self.assertIn("step2.png", md)

    def test_render_with_llm_findings(self) -> None:
        llm_block = {
            "enabled": True,
            "parsed": {
                "findings": [{"severity": "high", "category": "usability", "summary": "CTA missing", "principle_tags": ["signifiers"]}],
                "pov_scorecard": [],
                "novel_ideas": ["Try bigger button"],
            },
        }
        report = build_report(run_meta={}, pages=[], goals=[], non_goals=[], llm_block=llm_block)
        md = render_markdown(report)
        self.assertIn("LLM Critique", md)
        self.assertIn("CTA missing", md)
        self.assertIn("signifiers", md)
        self.assertIn("Try bigger button", md)

    def test_render_markdown_with_pov_and_scorecard(self) -> None:
        report = build_report(
            run_meta={"base_url": "http://example.com", "browser": "chromium"},
            pages=[_clean_page()],
            goals=["Test goal"],
            non_goals=[],
            pov={"name": "doet-norman-v1", "focus": ["discoverability", "feedback"]},
            llm_block={
                "enabled": True,
                "parsed": {
                    "findings": [
                        {
                            "severity": "medium",
                            "category": "usability",
                            "summary": "Checkout CTA is hard to find",
                            "principle_tags": ["discoverability", "signifiers"],
                        }
                    ],
                    "pov_scorecard": [
                        {"principle": "discoverability", "score": 2, "rationale": "Primary action is visually weak"}
                    ],
                    "novel_ideas": [],
                    "next_experiments": [],
                },
            },
        )
        md = render_markdown(report)
        self.assertIn("## POV", md)
        self.assertIn("POV Scorecard", md)
        self.assertIn("discoverability", md)
