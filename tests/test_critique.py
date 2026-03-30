from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from uxdrift.llm.critique import critique


class TestCritiqueRedactsBaseUrl(unittest.TestCase):
    """base_url in the critique return dict must be hostname-only (CWE-200)."""

    @patch("uxdrift.llm.critique.chat_completions")
    def test_base_url_redacted_to_hostname(self, mock_chat: unittest.mock.MagicMock) -> None:
        mock_chat.return_value = {
            "choices": [{"message": {"content": '{"findings": []}'}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        result = critique(
            base_url="https://api.openai.com/v1",
            api_key="sk-test",
            model="gpt-4o-mini",
            goals=["Test"],
            non_goals=[],
            evidence={"meta": {}},
            screenshot_paths=[],
        )

        # Must NOT contain the full URL path
        self.assertNotIn("/v1", result["base_url"])
        # Must contain just the hostname
        self.assertEqual(result["base_url"], "api.openai.com")

    @patch("uxdrift.llm.critique.chat_completions")
    def test_base_url_redacted_custom_provider(self, mock_chat: unittest.mock.MagicMock) -> None:
        mock_chat.return_value = {
            "choices": [{"message": {"content": '{"findings": []}'}}],
            "usage": {},
        }

        result = critique(
            base_url="http://localhost:11434/v1",
            api_key="ollama",
            model="llama3",
            goals=[],
            non_goals=[],
            evidence={},
            screenshot_paths=[],
        )

        self.assertEqual(result["base_url"], "localhost:11434")

    @patch("uxdrift.llm.critique.chat_completions")
    def test_base_url_redacted_plain_hostname(self, mock_chat: unittest.mock.MagicMock) -> None:
        mock_chat.return_value = {
            "choices": [{"message": {"content": '{"findings": []}'}}],
            "usage": {},
        }

        result = critique(
            base_url="https://my-llm.example.com",
            api_key="key",
            model="m",
            goals=[],
            non_goals=[],
            evidence={},
            screenshot_paths=[],
        )

        self.assertEqual(result["base_url"], "my-llm.example.com")
