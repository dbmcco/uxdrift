from __future__ import annotations

from typing import Any


def build_messages(
    *,
    goals: list[str],
    non_goals: list[str],
    evidence: dict[str, Any],
    images: list[dict[str, Any]],
    pov: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    goals_text = "\n".join([f"- {g}" for g in goals]) if goals else "(none provided)"
    non_goals_text = "\n".join([f"- {g}" for g in non_goals]) if non_goals else "(none provided)"
    pov_block = ""
    if pov:
        lines: list[str] = []
        title = str(pov.get("title") or pov.get("name") or "POV")
        name = str(pov.get("name") or title)
        lines.append(f"Evaluation POV: {title} (`{name}`).")
        principles = pov.get("principles") or []
        if isinstance(principles, list) and principles:
            lines.append("Apply these principles explicitly:")
            for item in principles:
                if not isinstance(item, dict):
                    continue
                pid = str(item.get("id") or "").strip()
                plabel = str(item.get("label") or pid or "").strip()
                phelp = str(item.get("prompt") or "").strip()
                if not pid:
                    continue
                if phelp:
                    lines.append(f"- {plabel} (`{pid}`): {phelp}")
                else:
                    lines.append(f"- {plabel} (`{pid}`)")
        focus = pov.get("focus") or []
        if isinstance(focus, list) and focus:
            focus_text = ", ".join([str(x) for x in focus if str(x).strip()])
            if focus_text:
                lines.append(f"POV focus for this run: {focus_text}")
        lines.append("Every finding must include `principle_tags` mapped to this POV.")
        pov_block = "\n".join(lines) + "\n\n"

    system = (
        "You are uxdrift, a UX evaluator.\n"
        "You will be given goals/non-goals and concrete browser evidence (errors + screenshots + minimal page text).\n"
        "Your job:\n"
        "- Identify glitches, UX issues, and opportunities.\n"
        "- Prioritize by user impact.\n"
        "- Propose concrete fixes and novel ideas.\n"
        "\n"
        f"{pov_block}"
        "\n"
        "Output MUST be valid JSON (no markdown), with this shape:\n"
        "{\n"
        '  "findings": [\n'
        "    {\n"
        '      "severity": "blocker|high|medium|low|info",\n'
        '      "category": "glitch|usability|a11y|performance|copy|visual|flow|trust|other",\n'
        '      "summary": \"...\",\n'
        '      "evidence": [\"...artifact path or brief reference...\"],\n'
        '      "fix": \"...concrete suggestion...\",\n'
        '      "impact": \"...why it matters...\",\n'
        '      "confidence": 0.0,\n'
        '      "principle_tags": ["discoverability", "..."]\n'
        "    }\n"
        "  ],\n"
        '  "pov_scorecard": [\n'
        "    {\n"
        '      "principle": "discoverability",\n'
        '      "score": 0,\n'
        '      "rationale": "..."\n'
        "    }\n"
        "  ],\n"
        '  "novel_ideas": [\"...\"],\n'
        '  "next_experiments": [\"...\"]\n'
        "}\n"
    )

    user_text = (
        "Goals:\n"
        f"{goals_text}\n\n"
        "Non-goals:\n"
        f"{non_goals_text}\n\n"
        "Evidence (JSON):\n"
        f"{evidence}\n"
    )

    user_content: list[dict[str, Any]] = [{"type": "text", "text": user_text}]
    user_content.extend(images)

    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]
