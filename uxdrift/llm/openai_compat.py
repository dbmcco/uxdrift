from __future__ import annotations

import json
from typing import Any

import httpx


class OpenAICompatError(RuntimeError):
    pass


def chat_completions(
    *,
    base_url: str,
    api_key: str,
    model: str,
    messages: list[dict[str, Any]],
    temperature: float = 0.2,
    max_tokens: int = 1200,
    timeout_s: float = 60.0,
) -> dict[str, Any]:
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    with httpx.Client(timeout=timeout_s) as client:
        r = client.post(url, headers=headers, json=payload)
        if r.status_code >= 400:
            raise OpenAICompatError(f"LLM request failed ({r.status_code}): {r.text[:500]}")
        return r.json()


def extract_text(resp: dict[str, Any]) -> str:
    choices = resp.get("choices") or []
    if not choices:
        return ""
    msg = choices[0].get("message") or {}
    content = msg.get("content")
    if isinstance(content, str):
        return content
    # Some providers might return structured content; best-effort stringify.
    return json.dumps(content, ensure_ascii=False)

