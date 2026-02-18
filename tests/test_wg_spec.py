from __future__ import annotations

import unittest

from uxdrift.wg_spec import extract_uxdrift_spec, load_uxdrift_spec_from_description


class TestWgSpec(unittest.TestCase):
    def test_extract_missing(self) -> None:
        self.assertIsNone(extract_uxdrift_spec("no spec here"))

    def test_extract_and_parse(self) -> None:
        desc = (
            "Some description\n\n"
            "```uxdrift\n"
            "schema = 1\n"
            "url = \"http://localhost:3000\"\n"
            "pages = [\"/\", \"/settings\"]\n"
            "goals = [\"No console errors\"]\n"
            "pov = \"doet-norman-v1\"\n"
            "pov_focus = [\"discoverability\", \"feedback\"]\n"
            "llm = true\n"
            "```\n"
            "\nMore text\n"
        )
        spec = load_uxdrift_spec_from_description(desc)
        self.assertIsNotNone(spec)
        assert spec is not None
        self.assertEqual(spec["schema"], 1)
        self.assertEqual(spec["url"], "http://localhost:3000")
        self.assertEqual(spec["pages"], ["/", "/settings"])
        self.assertEqual(spec["goals"], ["No console errors"])
        self.assertEqual(spec["pov"], "doet-norman-v1")
        self.assertEqual(spec["pov_focus"], ["discoverability", "feedback"])
        self.assertEqual(spec["llm"], True)
