from __future__ import annotations

import re
from typing import Any


_NORMAN_PRINCIPLES: list[dict[str, str]] = [
    {"id": "discoverability", "label": "Discoverability", "prompt": "Can users see what actions are possible?"},
    {"id": "signifiers", "label": "Signifiers", "prompt": "Do visual/text cues clearly indicate interaction affordances?"},
    {"id": "mapping", "label": "Mapping", "prompt": "Do controls map naturally to expected outcomes?"},
    {"id": "feedback", "label": "Feedback", "prompt": "Does the system communicate status/results clearly and quickly?"},
    {"id": "constraints", "label": "Constraints", "prompt": "Are harmful/impossible actions prevented through sensible constraints?"},
    {"id": "conceptual_model", "label": "Conceptual Model", "prompt": "Does the UI help users form a correct mental model of how it works?"},
    {
        "id": "error_prevention_recovery",
        "label": "Error Prevention & Recovery",
        "prompt": "Does the design prevent errors and support clear recovery paths when errors happen?",
    },
]

_POV_PACKS: dict[str, dict[str, Any]] = {
    "doet-norman-v1": {
        "name": "doet-norman-v1",
        "title": "The Design of Everyday Things (Norman) POV",
        "principles": _NORMAN_PRINCIPLES,
    }
}

_ALIASES: dict[str, str] = {
    "doet": "doet-norman-v1",
    "norman": "doet-norman-v1",
    "doet-norman": "doet-norman-v1",
}


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", value.strip().lower())
    return cleaned.strip("_")


def resolve_pov(pov: str | None, pov_focus: list[str] | None) -> dict[str, Any] | None:
    if not pov:
        return None

    raw = pov.strip().lower()
    candidates = [raw, raw.replace("_", "-"), _slug(raw)]
    resolved_name = None
    pack = None
    for key in candidates:
        key = _ALIASES.get(key, key)
        if key in _POV_PACKS:
            resolved_name = key
            pack = _POV_PACKS[key]
            break
    if not pack:
        # Allow custom POV labels; use caller-specified focus only.
        focus = [_slug(p) for p in (pov_focus or []) if _slug(p)]
        return {
            "name": pov,
            "title": pov,
            "principles": [],
            "focus": focus,
        }

    principles = list(pack.get("principles", []))
    valid_ids = {str(p.get("id")) for p in principles}
    requested_focus = [_slug(p) for p in (pov_focus or []) if _slug(p)]
    focus = [p for p in requested_focus if p in valid_ids] if requested_focus else [str(p.get("id")) for p in principles]
    if not focus:
        focus = [str(p.get("id")) for p in principles]

    return {
        "name": pack.get("name"),
        "title": pack.get("title"),
        "principles": principles,
        "focus": focus,
    }
