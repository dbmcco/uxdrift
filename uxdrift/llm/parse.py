from __future__ import annotations

import json
import re
from typing import Any


def _extract_codeblock_json(text: str) -> str | None:
    # ```json ... ```
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if not m:
        return None
    return m.group(1)


def _extract_first_balanced_object(text: str) -> str | None:
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue

        if ch == '"':
            in_str = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


_VALID_SEVERITIES = frozenset({"blocker", "high", "medium", "low", "info"})


def validate_finding(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Return a cleaned finding dict, or None if required fields are missing/invalid."""
    severity = str(raw.get("severity") or "").strip()
    category = str(raw.get("category") or "").strip()
    summary = str(raw.get("summary") or "").strip()

    if not severity or not category or not summary:
        return None
    if severity not in _VALID_SEVERITIES:
        return None

    cleaned: dict[str, Any] = {"severity": severity, "category": category, "summary": summary}
    for optional in ("fix", "impact", "confidence", "principle_tags", "evidence"):
        if optional in raw:
            cleaned[optional] = raw[optional]
    return cleaned


def validate_findings(raw_list: list[Any]) -> list[dict[str, Any]]:
    """Filter a list of raw finding dicts, dropping any that fail validation."""
    out: list[dict[str, Any]] = []
    for item in raw_list:
        if not isinstance(item, dict):
            continue
        cleaned = validate_finding(item)
        if cleaned is not None:
            out.append(cleaned)
    return out


def parse_json_object(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None

    # Best case: pure JSON.
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    # Common: fenced json codeblock.
    cb = _extract_codeblock_json(text)
    if cb:
        try:
            obj = json.loads(cb)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

    # Fallback: first balanced {...}
    blob = _extract_first_balanced_object(text)
    if blob:
        try:
            obj = json.loads(blob)
            if isinstance(obj, dict):
                return obj
        except Exception:
            return None

    return None

