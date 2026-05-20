from __future__ import annotations

import os
import tempfile
import unittest

from uxdrift import cli
from uxdrift.model_routes import (
    LLM_CRITIQUE_ROUTE,
    base_url_for_route,
    model_for_env_or_route,
    model_for_route,
)


class TestModelRoutes(unittest.TestCase):
    def test_llm_critique_route_preserves_current_defaults(self) -> None:
        self.assertEqual(model_for_route(LLM_CRITIQUE_ROUTE), "gpt-4o-mini")
        self.assertEqual(base_url_for_route(LLM_CRITIQUE_ROUTE), "https://api.openai.com/v1")

    def test_env_override_still_wins(self) -> None:
        old = os.environ.get("UXDRIFT_LLM_MODEL")
        os.environ["UXDRIFT_LLM_MODEL"] = "custom-model"
        try:
            self.assertEqual(
                model_for_env_or_route("UXDRIFT_LLM_MODEL", LLM_CRITIQUE_ROUTE),
                "custom-model",
            )
        finally:
            if old is None:
                os.environ.pop("UXDRIFT_LLM_MODEL", None)
            else:
                os.environ["UXDRIFT_LLM_MODEL"] = old

    def test_cli_defaults_are_registry_backed(self) -> None:
        old_model = os.environ.pop("UXDRIFT_LLM_MODEL", None)
        old_base_url = os.environ.pop("UXDRIFT_LLM_BASE_URL", None)
        try:
            with tempfile.TemporaryDirectory() as td:
                args = cli._parse_args(["run", "--url", "http://localhost:3000", "--out", td])

            self.assertEqual(args.llm_model, "gpt-4o-mini")
            self.assertEqual(args.llm_base_url, "https://api.openai.com/v1")
        finally:
            if old_model is not None:
                os.environ["UXDRIFT_LLM_MODEL"] = old_model
            if old_base_url is not None:
                os.environ["UXDRIFT_LLM_BASE_URL"] = old_base_url
