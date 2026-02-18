from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, TypedDict


Severity = Literal["blocker", "high", "medium", "low", "info"]


class Finding(TypedDict, total=False):
    severity: Severity
    category: str
    summary: str
    evidence: list[str]
    fix: str
    impact: str
    confidence: float
    principle_tags: list[str]


@dataclass(frozen=True)
class RunOptions:
    base_url: str
    pages: list[str]
    out_dir: str | None
    headful: bool
    browser: Literal["chromium", "firefox", "webkit"]
    browser_channel: str | None
    nav_timeout_ms: int
    wait_until: Literal["load", "domcontentloaded", "networkidle"]
    llm_enabled: bool
    llm_base_url: str
    llm_model: str
    goals: list[str]
    non_goals: list[str]


Json = dict[str, Any]
