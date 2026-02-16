from __future__ import annotations

from typing import Any


def build_messages(
    *,
    goals: list[str],
    non_goals: list[str],
    evidence: dict[str, Any],
    images: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    goals_text = "\n".join([f"- {g}" for g in goals]) if goals else "(none provided)"
    non_goals_text = "\n".join([f"- {g}" for g in non_goals]) if non_goals else "(none provided)"

    system = (
        "You are uxdrift, a UX evaluator.\n"
        "You will be given goals/non-goals and concrete browser evidence (errors + screenshots + minimal page text).\n"
        "Your job:\n"
        "- Identify glitches, UX issues, and opportunities.\n"
        "- Prioritize by user impact.\n"
        "- Propose concrete fixes and novel ideas.\n"
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
        '      "confidence": 0.0\n'
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

