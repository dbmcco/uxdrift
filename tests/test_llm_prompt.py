from __future__ import annotations

import unittest

from uxdrift.llm.prompt import build_messages


class TestLlmPrompt(unittest.TestCase):
    def test_prompt_includes_pov_contract(self) -> None:
        messages = build_messages(
            goals=["Improve checkout clarity"],
            non_goals=["No visual redesign"],
            evidence={"meta": {"base_url": "http://localhost:3000"}},
            images=[],
            pov={
                "name": "doet-norman-v1",
                "title": "The Design of Everyday Things (Norman) POV",
                "principles": [
                    {"id": "discoverability", "label": "Discoverability", "prompt": "Can users see available actions?"}
                ],
                "focus": ["discoverability"],
            },
        )
        self.assertEqual(len(messages), 2)
        system = str(messages[0]["content"])
        self.assertIn("Evaluation POV", system)
        self.assertIn("principle_tags", system)
        self.assertIn("pov_scorecard", system)
        self.assertIn("discoverability", system)

