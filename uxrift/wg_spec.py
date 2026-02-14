from __future__ import annotations

import re
import tomllib
from typing import Any

UXRIFT_FENCE_INFO = "uxrift"

_FENCE_RE = re.compile(
    r"```(?P<info>uxrift)\s*\n(?P<body>.*?)\n```",
    re.DOTALL,
)


def extract_uxrift_spec(description: str) -> str | None:
    m = _FENCE_RE.search(description or "")
    if not m:
        return None
    return m.group("body").strip()


def parse_uxrift_spec(spec_text: str) -> dict[str, Any]:
    data = tomllib.loads(spec_text)
    if not isinstance(data, dict):
        raise ValueError("uxrift spec must parse to a TOML table/object.")
    return data


def load_uxrift_spec_from_description(description: str) -> dict[str, Any] | None:
    text = extract_uxrift_spec(description)
    if text is None:
        return None
    return parse_uxrift_spec(text)

