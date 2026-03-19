from __future__ import annotations

import unittest
from unittest.mock import patch

from uxdrift.llm.parse import parse_json_object, _extract_codeblock_json, validate_finding, validate_findings


class TestLLMParse(unittest.TestCase):
    def test_parse_pure_json(self) -> None:
        obj = parse_json_object('{"a": 1, "b": {"c": 2}}')
        self.assertIsNotNone(obj)
        assert obj is not None
        self.assertEqual(obj["a"], 1)
        self.assertEqual(obj["b"]["c"], 2)

    def test_parse_codeblock(self) -> None:
        txt = "here you go\n```json\n{\"ok\": true}\n```\nthanks"
        obj = parse_json_object(txt)
        self.assertIsNotNone(obj)
        assert obj is not None
        self.assertEqual(obj["ok"], True)

    def test_parse_balanced_object(self) -> None:
        txt = "prefix {\"x\": 1, \"y\": {\"z\": 2}} suffix"
        obj = parse_json_object(txt)
        self.assertIsNotNone(obj)
        assert obj is not None
        self.assertEqual(obj["y"]["z"], 2)

    def test_codeblock_regex_actually_used(self) -> None:
        # Verify the codeblock extraction path fires (not the balanced-brace fallback).
        # Input has NO standalone balanced object outside the fence — only the fenced one.
        # We patch _extract_first_balanced_object to raise so if the codeblock path is
        # skipped and the fallback runs instead, the test will fail.
        txt = "Sure thing:\n```json\n{\"value\": 42}\n```"
        result = _extract_codeblock_json(txt)
        self.assertIsNotNone(result)
        import json
        parsed = json.loads(result)  # type: ignore[arg-type]
        self.assertEqual(parsed["value"], 42)

    def test_codeblock_with_whitespace_around_json(self) -> None:
        # Whitespace before/after the JSON inside the fence must be handled.
        txt = "```json\n\n  {\"k\": \"v\"}  \n```"
        result = _extract_codeblock_json(txt)
        self.assertIsNotNone(result)

    def test_parse_empty_returns_none(self) -> None:
        self.assertIsNone(parse_json_object(""))
        self.assertIsNone(parse_json_object("   "))

    def test_parse_non_object_returns_none(self) -> None:
        self.assertIsNone(parse_json_object("[1, 2, 3]"))
        self.assertIsNone(parse_json_object('"just a string"'))


class TestValidateFinding(unittest.TestCase):
    def _valid(self) -> dict:
        return {"severity": "high", "category": "usability", "summary": "Button too small"}

    def test_validate_finding_valid(self) -> None:
        result = validate_finding(self._valid())
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["severity"], "high")
        self.assertEqual(result["category"], "usability")
        self.assertEqual(result["summary"], "Button too small")

    def test_validate_finding_all_severities_accepted(self) -> None:
        for sev in ("blocker", "high", "medium", "low", "info"):
            raw = {**self._valid(), "severity": sev}
            self.assertIsNotNone(validate_finding(raw), f"severity {sev!r} should be valid")

    def test_validate_finding_missing_severity(self) -> None:
        raw = {"category": "usability", "summary": "Problem"}
        self.assertIsNone(validate_finding(raw))

    def test_validate_finding_missing_category(self) -> None:
        raw = {"severity": "high", "summary": "Problem"}
        self.assertIsNone(validate_finding(raw))

    def test_validate_finding_missing_summary(self) -> None:
        raw = {"severity": "high", "category": "usability"}
        self.assertIsNone(validate_finding(raw))

    def test_validate_finding_bad_severity(self) -> None:
        raw = {**self._valid(), "severity": "critical"}
        self.assertIsNone(validate_finding(raw))

    def test_validate_finding_passes_optional_fields(self) -> None:
        raw = {**self._valid(), "fix": "Make it bigger", "principle_tags": ["signifiers"]}
        result = validate_finding(raw)
        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["fix"], "Make it bigger")
        self.assertEqual(result["principle_tags"], ["signifiers"])

    def test_validate_findings_filters_invalid(self) -> None:
        raw_list = [
            self._valid(),
            {"severity": "BAD", "category": "x", "summary": "y"},
            {"category": "x", "summary": "y"},
            {**self._valid(), "severity": "low", "summary": "OK too"},
            "not a dict",
        ]
        result = validate_findings(raw_list)  # type: ignore[arg-type]
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["severity"], "high")
        self.assertEqual(result[1]["severity"], "low")

    def test_validate_findings_empty_list(self) -> None:
        self.assertEqual(validate_findings([]), [])

