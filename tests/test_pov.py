from __future__ import annotations

import unittest

from uxdrift.llm.pov import resolve_pov


class TestPov(unittest.TestCase):
    def test_resolve_norman_alias(self) -> None:
        pov = resolve_pov("norman", [])
        self.assertIsNotNone(pov)
        assert pov is not None
        self.assertEqual(pov["name"], "doet-norman-v1")
        self.assertTrue(any(p.get("id") == "discoverability" for p in pov.get("principles", [])))
        self.assertIn("discoverability", pov.get("focus", []))

    def test_resolve_focus_filter(self) -> None:
        pov = resolve_pov("doet-norman-v1", ["feedback", "unknown"])
        self.assertIsNotNone(pov)
        assert pov is not None
        self.assertEqual(pov.get("focus"), ["feedback"])

    def test_custom_pov_passthrough(self) -> None:
        pov = resolve_pov("my-custom-pov", ["clarity"])
        self.assertIsNotNone(pov)
        assert pov is not None
        self.assertEqual(pov.get("name"), "my-custom-pov")
        self.assertEqual(pov.get("focus"), ["clarity"])

