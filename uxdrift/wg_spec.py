from __future__ import annotations

import re
import tomllib
from typing import Any

UXDRIFT_FENCE_INFO = "uxdrift"

_FENCE_RE = re.compile(
    r"```(?P<info>uxdrift)\s*\n(?P<body>.*?)\n```",
    re.DOTALL,
)


def extract_uxdrift_spec(description: str) -> str | None:
    m = _FENCE_RE.search(description or "")
    if not m:
        return None
    return m.group("body").strip()


def parse_uxdrift_spec(spec_text: str) -> dict[str, Any]:
    data = tomllib.loads(spec_text)
    if not isinstance(data, dict):
        raise ValueError("uxdrift spec must parse to a TOML table/object.")
    return data


def load_uxdrift_spec_from_description(description: str) -> dict[str, Any] | None:
    text = extract_uxdrift_spec(description)
    if text is None:
        return None
    return parse_uxdrift_spec(text)

