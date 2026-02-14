from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any, Literal

from playwright.sync_api import ConsoleMessage, Page, Response, sync_playwright


@dataclass(frozen=True)
class PageEvidence:
    name: str
    url: str
    artifacts: dict[str, str]
    timing_ms: dict[str, int]
    console: dict[str, Any]
    network: dict[str, Any]
    page_errors: list[str]
    extracted: dict[str, Any]


def _safe_int(v: float) -> int:
    return int(round(v))


def _truncate(s: str, max_chars: int) -> str:
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 1] + "…"


def _attach_listeners(
    page: Page,
    *,
    console_messages: list[dict[str, Any]],
    page_errors: list[str],
    request_failures: list[dict[str, Any]],
    http_errors: list[dict[str, Any]],
) -> None:
    def on_console(msg: ConsoleMessage) -> None:
        try:
            console_messages.append(
                {
                    "type": msg.type,
                    "text": msg.text,
                    "location": msg.location,
                }
            )
        except Exception as e:  # pragma: no cover
            console_messages.append({"type": "listener_error", "text": f"console listener error: {e}"})

    def on_page_error(err: Any) -> None:
        page_errors.append(str(err))

    def on_request_failed(req: Any) -> None:
        request_failures.append(
            {
                "url": req.url,
                "method": req.method,
                "failure": getattr(req.failure, "error_text", None) if req.failure else None,
                "resource_type": req.resource_type,
            }
        )

    def on_response(resp: Response) -> None:
        try:
            status = resp.status
            if status >= 400:
                http_errors.append({"url": resp.url, "status": status, "status_text": resp.status_text})
        except Exception:  # pragma: no cover
            return

    page.on("console", on_console)
    page.on("pageerror", on_page_error)
    page.on("requestfailed", on_request_failed)
    page.on("response", on_response)

def capture_pages(
    *,
    base_url: str,
    pages: list[str],
    out_dir: Path,
    headful: bool,
    browser: Literal["chromium", "firefox", "webkit"],
    browser_channel: str | None,
    nav_timeout_ms: int,
    wait_until: Literal["load", "domcontentloaded", "networkidle"],
) -> tuple[list[PageEvidence], dict[str, Any]]:
    out_dir.mkdir(parents=True, exist_ok=True)

    started = time.time()

    # Launch browser outside "with sync_playwright()" context so we can return evidence cleanly.
    # sync_playwright() owns the driver process; we keep all usage inside this function.
    with sync_playwright() as p:
        browser_type = getattr(p, browser)
        launched_channel: str | None = None
        preferred_channel = browser_channel
        if preferred_channel is None and browser == "chromium":
            # Local Chrome is commonly installed even when Playwright browsers are not.
            preferred_channel = "chrome"

        if preferred_channel and browser == "chromium":
            try:
                b = browser_type.launch(headless=not headful, channel=preferred_channel)
                launched_channel = preferred_channel
            except Exception:
                b = browser_type.launch(headless=not headful)
        else:
            b = browser_type.launch(headless=not headful)

        context = b.new_context()
        page = context.new_page()

        evidence: list[PageEvidence] = []
        for idx, path in enumerate(pages):
            name = path if path != "/" else "root"
            url = base_url.rstrip("/") + path

            console_messages: list[dict[str, Any]] = []
            page_errors: list[str] = []
            request_failures: list[dict[str, Any]] = []
            http_errors: list[dict[str, Any]] = []

            _attach_listeners(
                page,
                console_messages=console_messages,
                page_errors=page_errors,
                request_failures=request_failures,
                http_errors=http_errors,
            )

            nav_started = time.time()
            page.goto(url, wait_until=wait_until, timeout=nav_timeout_ms)
            nav_ended = time.time()

            screenshot_path = out_dir / f"{idx:02d}-{name}.png"
            page.screenshot(path=str(screenshot_path), full_page=True)

            extracted_title = ""
            extracted_text = ""
            try:
                extracted_title = page.title()
            except Exception:
                extracted_title = ""
            try:
                extracted_text = page.inner_text("body")
            except Exception:
                extracted_text = ""

            nav_entries = {}
            try:
                nav_entries = page.evaluate(
                    "() => {\n"
                    "  const nav = performance.getEntriesByType('navigation');\n"
                    "  if (!nav || nav.length === 0) return null;\n"
                    "  const n = nav[0];\n"
                    "  return {\n"
                    "    type: n.type,\n"
                    "    startTime: n.startTime,\n"
                    "    duration: n.duration,\n"
                    "    domContentLoadedEventEnd: n.domContentLoadedEventEnd,\n"
                    "    loadEventEnd: n.loadEventEnd,\n"
                    "  };\n"
                    "}"
                )
            except Exception:
                nav_entries = None

            evidence.append(
                PageEvidence(
                    name=name,
                    url=url,
                    artifacts={"screenshot": str(screenshot_path)},
                    timing_ms={
                        "navigation": _safe_int((nav_ended - nav_started) * 1000),
                    },
                    console={
                        "messages": console_messages,
                        "counts": {
                            "error": sum(1 for m in console_messages if m.get("type") == "error"),
                            "warning": sum(1 for m in console_messages if m.get("type") == "warning"),
                        },
                    },
                    network={
                        "request_failures": request_failures,
                        "http_errors": http_errors,
                        "counts": {
                            "request_failures": len(request_failures),
                            "http_errors": len(http_errors),
                        },
                    },
                    page_errors=page_errors,
                    extracted={
                        "title": extracted_title,
                        "text": _truncate(extracted_text, 12_000),
                        "performance_navigation": nav_entries,
                    },
                )
            )

        context.close()
        b.close()

    ended = time.time()
    meta = {
        "base_url": base_url,
        "pages": pages,
        "browser": browser,
        "browser_channel": launched_channel,
        "headful": headful,
        "nav_timeout_ms": nav_timeout_ms,
        "wait_until": wait_until,
        "timing_ms": {"total": _safe_int((ended - started) * 1000)},
    }
    return evidence, meta
