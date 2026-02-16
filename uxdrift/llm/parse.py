from __future__ import annotations

import json
import re
from typing import Any


def _extract_codeblock_json(text: str) -> str | None:
    # ```json ... ```
    m = re.search(r"```json\\s*(\\{.*?\\})\\s*```", text, flags=re.DOTALL)
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

