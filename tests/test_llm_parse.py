from __future__ import annotations

import unittest

from uxdrift.llm.parse import parse_json_object


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

