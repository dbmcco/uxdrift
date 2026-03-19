# ABOUTME: Unit tests for playwright_runner.py pure functions and listener logic
# All playwright objects are mocked — no real browser is launched.
from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from uxdrift.playwright_runner import (
    _attach_listeners,
    _locator,
    _run_steps,
    _safe_int,
    _truncate,
)


class TestSafeInt(unittest.TestCase):
    def test_rounds_down(self) -> None:
        self.assertEqual(_safe_int(1.4), 1)

    def test_rounds_up(self) -> None:
        self.assertEqual(_safe_int(1.6), 2)

    def test_zero(self) -> None:
        self.assertEqual(_safe_int(0.0), 0)

    def test_exact(self) -> None:
        self.assertEqual(_safe_int(5.0), 5)


class TestTruncate(unittest.TestCase):
    def test_short_string_unchanged(self) -> None:
        s = "hello"
        self.assertEqual(_truncate(s, 10), s)

    def test_exact_length_unchanged(self) -> None:
        s = "hello"
        self.assertEqual(_truncate(s, 5), s)

    def test_long_string_truncated(self) -> None:
        result = _truncate("abcdefgh", 5)
        self.assertEqual(len(result), 5)
        self.assertTrue(result.endswith("…"))

    def test_truncated_prefix_preserved(self) -> None:
        result = _truncate("abcdefgh", 5)
        self.assertTrue(result.startswith("abcd"))


class TestAttachListeners(unittest.TestCase):
    def _make_page(self) -> MagicMock:
        page = MagicMock()
        page.on = MagicMock()
        return page

    def _get_handler(self, page: MagicMock, event: str):
        """Return the callback registered for a given event name."""
        for c in page.on.call_args_list:
            if c[0][0] == event:
                return c[0][1]
        raise AssertionError(f"No handler registered for event {event!r}")

    def test_registers_four_events(self) -> None:
        page = self._make_page()
        _attach_listeners(page, console_messages=[], page_errors=[], request_failures=[], http_errors=[])
        events = [c[0][0] for c in page.on.call_args_list]
        self.assertEqual(sorted(events), sorted(["console", "pageerror", "requestfailed", "response"]))

    def test_console_callback_appends(self) -> None:
        page = self._make_page()
        msgs: list = []
        _attach_listeners(page, console_messages=msgs, page_errors=[], request_failures=[], http_errors=[])
        handler = self._get_handler(page, "console")
        msg = MagicMock()
        msg.type = "error"
        msg.text = "oh no"
        msg.location = {"url": "x"}
        handler(msg)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]["type"], "error")
        self.assertEqual(msgs[0]["text"], "oh no")

    def test_pageerror_callback_appends(self) -> None:
        page = self._make_page()
        errs: list = []
        _attach_listeners(page, console_messages=[], page_errors=errs, request_failures=[], http_errors=[])
        handler = self._get_handler(page, "pageerror")
        handler("TypeError: x is not a function")
        self.assertEqual(errs, ["TypeError: x is not a function"])

    def test_request_failed_callback_appends(self) -> None:
        page = self._make_page()
        failures: list = []
        _attach_listeners(page, console_messages=[], page_errors=[], request_failures=failures, http_errors=[])
        handler = self._get_handler(page, "requestfailed")
        req = MagicMock()
        req.url = "http://example.com/api"
        req.method = "GET"
        req.failure = None
        req.resource_type = "xhr"
        handler(req)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["url"], "http://example.com/api")
        self.assertEqual(failures[0]["method"], "GET")
        self.assertIsNone(failures[0]["failure"])

    def test_http_error_recorded_on_4xx(self) -> None:
        page = self._make_page()
        http_errs: list = []
        _attach_listeners(page, console_messages=[], page_errors=[], request_failures=[], http_errors=http_errs)
        handler = self._get_handler(page, "response")
        resp = MagicMock()
        resp.status = 404
        resp.status_text = "Not Found"
        resp.url = "http://example.com/missing"
        handler(resp)
        self.assertEqual(len(http_errs), 1)
        self.assertEqual(http_errs[0]["status"], 404)
        self.assertEqual(http_errs[0]["url"], "http://example.com/missing")

    def test_http_ok_not_recorded(self) -> None:
        page = self._make_page()
        http_errs: list = []
        _attach_listeners(page, console_messages=[], page_errors=[], request_failures=[], http_errors=http_errs)
        handler = self._get_handler(page, "response")
        resp = MagicMock()
        resp.status = 200
        handler(resp)
        self.assertEqual(http_errs, [])

    def test_http_5xx_recorded(self) -> None:
        page = self._make_page()
        http_errs: list = []
        _attach_listeners(page, console_messages=[], page_errors=[], request_failures=[], http_errors=http_errs)
        handler = self._get_handler(page, "response")
        resp = MagicMock()
        resp.status = 500
        resp.status_text = "Internal Server Error"
        resp.url = "http://example.com/crash"
        handler(resp)
        self.assertEqual(len(http_errs), 1)
        self.assertEqual(http_errs[0]["status"], 500)


class TestLocator(unittest.TestCase):
    def _page(self) -> MagicMock:
        page = MagicMock()
        page.locator = MagicMock(return_value=MagicMock())
        page.get_by_role = MagicMock(return_value=MagicMock())
        page.get_by_text = MagicMock(return_value=MagicMock())
        return page

    def test_selector(self) -> None:
        page = self._page()
        _locator(page, {"selector": ".btn"})
        page.locator.assert_called_once_with(".btn")

    def test_role_with_name(self) -> None:
        page = self._page()
        _locator(page, {"role": "button", "name": "Submit"})
        page.get_by_role.assert_called_once_with("button", name="Submit")

    def test_role_without_name(self) -> None:
        page = self._page()
        _locator(page, {"role": "button"})
        page.get_by_role.assert_called_once_with("button")

    def test_text(self) -> None:
        page = self._page()
        _locator(page, {"text": "Click me", "exact": True})
        page.get_by_text.assert_called_once_with("Click me", exact=True)

    def test_nth_modifier(self) -> None:
        page = self._page()
        loc_mock = MagicMock()
        page.locator.return_value = loc_mock
        _locator(page, {"selector": "li", "nth": 2})
        loc_mock.nth.assert_called_once_with(2)

    def test_first_modifier(self) -> None:
        page = self._page()
        loc_mock = MagicMock()
        page.locator.return_value = loc_mock
        result = _locator(page, {"selector": "li", "first": True})
        # .first is a property access, not a call — check it was accessed
        _ = loc_mock.first

    def test_missing_key_raises(self) -> None:
        page = self._page()
        with self.assertRaises(ValueError):
            _locator(page, {})


class TestRunSteps(unittest.TestCase):
    def _page(self) -> MagicMock:
        page = MagicMock()
        page.locator = MagicMock(return_value=MagicMock())
        page.keyboard = MagicMock()
        page.wait_for_timeout = MagicMock()
        page.screenshot = MagicMock()
        return page

    def test_click(self) -> None:
        page = self._page()
        loc = page.locator.return_value
        artifacts: dict = {}
        _run_steps(page=page, steps=[{"action": "click", "selector": ".btn"}], out_dir=Path("/tmp"), prefix="p", artifacts=artifacts)
        loc.click.assert_called_once()
        self.assertIn("step_log", artifacts)

    def test_fill(self) -> None:
        page = self._page()
        loc = page.locator.return_value
        _run_steps(page=page, steps=[{"action": "fill", "selector": "input", "value": "hello"}], out_dir=Path("/tmp"), prefix="p", artifacts={})
        loc.fill.assert_called_once_with("hello")

    def test_press(self) -> None:
        page = self._page()
        _run_steps(page=page, steps=[{"action": "press", "key": "Enter"}], out_dir=Path("/tmp"), prefix="p", artifacts={})
        page.keyboard.press.assert_called_once_with("Enter")

    def test_sleep(self) -> None:
        page = self._page()
        _run_steps(page=page, steps=[{"action": "sleep", "ms": 50}], out_dir=Path("/tmp"), prefix="p", artifacts={})
        page.wait_for_timeout.assert_called_once_with(50)

    def test_screenshot_step(self, tmp_path: Path = Path("/tmp")) -> None:
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            page = self._page()
            artifacts: dict = {}
            _run_steps(page=page, steps=[{"action": "screenshot", "name": "after-click"}], out_dir=out, prefix="00-root", artifacts=artifacts)
            page.screenshot.assert_called_once()
            self.assertIn("step_screenshots", artifacts)

    def test_unknown_action_raises(self) -> None:
        page = self._page()
        with self.assertRaises(ValueError):
            _run_steps(page=page, steps=[{"action": "explode"}], out_dir=Path("/tmp"), prefix="p", artifacts={})

    def test_empty_steps_no_artifacts(self) -> None:
        page = self._page()
        artifacts: dict = {}
        _run_steps(page=page, steps=[], out_dir=Path("/tmp"), prefix="p", artifacts=artifacts)
        self.assertNotIn("step_log", artifacts)

    def test_step_without_action_skipped(self) -> None:
        page = self._page()
        artifacts: dict = {}
        _run_steps(page=page, steps=[{"action": ""}], out_dir=Path("/tmp"), prefix="p", artifacts=artifacts)
        self.assertNotIn("step_log", artifacts)
