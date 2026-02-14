from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

from uxrift.llm.openai_compat import chat_completions, extract_text
from uxrift.llm.parse import parse_json_object
from uxrift.llm.prompt import build_messages


def _image_part_from_path(path: Path) -> dict[str, Any]:
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    url = f"data:image/png;base64,{data}"
    return {"type": "image_url", "image_url": {"url": url}}


def critique(
    *,
    base_url: str,
    api_key: str,
    model: str,
    goals: list[str],
    non_goals: list[str],
    evidence: dict[str, Any],
    screenshot_paths: list[Path],
) -> dict[str, Any]:
    images = []
    # Keep token pressure down: send up to 4 screenshots.
    for p in screenshot_paths[:4]:
        try:
            images.append(_image_part_from_path(p))
        except Exception:
            continue

    messages = build_messages(goals=goals, non_goals=non_goals, evidence=evidence, images=images)
    resp = chat_completions(base_url=base_url, api_key=api_key, model=model, messages=messages)
    text = extract_text(resp)
    parsed = parse_json_object(text)
    return {
        "enabled": True,
        "provider": "openai_compat",
        "base_url": base_url,
        "model": model,
        "raw_text": text,
        "parsed": parsed,
        "usage": resp.get("usage"),
    }

