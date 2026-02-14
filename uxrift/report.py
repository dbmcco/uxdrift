from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

from uxrift.playwright_runner import PageEvidence


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def summarize_deterministic_findings(pages: list[PageEvidence]) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for p in pages:
        err_count = int(p.console.get("counts", {}).get("error", 0))
        warn_count = int(p.console.get("counts", {}).get("warning", 0))
        req_fail = int(p.network.get("counts", {}).get("request_failures", 0))
        http_err = int(p.network.get("counts", {}).get("http_errors", 0))
        page_errs = len(p.page_errors)

        if err_count or page_errs:
            findings.append(
                {
                    "severity": "high",
                    "category": "glitch",
                    "summary": f"{p.name}: console/page errors detected",
                    "evidence": [p.artifacts.get("screenshot", "")],
                    "details": {
                        "console_error_count": err_count,
                        "page_error_count": page_errs,
                    },
                }
            )
        if req_fail or http_err:
            findings.append(
                {
                    "severity": "medium",
                    "category": "glitch",
                    "summary": f"{p.name}: request failures or HTTP errors detected",
                    "evidence": [p.artifacts.get("screenshot", "")],
                    "details": {
                        "request_failure_count": req_fail,
                        "http_error_count": http_err,
                    },
                }
            )
        if warn_count:
            findings.append(
                {
                    "severity": "low",
                    "category": "glitch",
                    "summary": f"{p.name}: console warnings detected",
                    "evidence": [p.artifacts.get("screenshot", "")],
                    "details": {"console_warning_count": warn_count},
                }
            )

    return findings


def render_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# uxrift report")
    lines.append("")

    meta = report.get("meta", {})
    lines.append("## Run")
    lines.append("")
    lines.append(f"- Generated: `{report.get('generated_at')}`")
    lines.append(f"- Base URL: `{meta.get('base_url')}`")
    lines.append(f"- Browser: `{meta.get('browser')}`")
    if meta.get("browser_channel"):
        lines.append(f"- Channel: `{meta.get('browser_channel')}`")
    lines.append("")

    findings = report.get("deterministic_findings", [])
    lines.append("## Deterministic Findings")
    lines.append("")
    if not findings:
        lines.append("- (none)")
    else:
        for f in findings:
            sev = f.get("severity", "unknown")
            cat = f.get("category", "unknown")
            summary = f.get("summary", "")
            lines.append(f"- [{sev}] {cat}: {summary}")
    lines.append("")

    llm = report.get("llm", {})
    if llm.get("enabled"):
        lines.append("## LLM Critique")
        lines.append("")
        critique = llm.get("parsed") or {}
        c_findings = critique.get("findings") or []
        if c_findings:
            lines.append("### Findings")
            lines.append("")
            for f in c_findings[:30]:
                sev = f.get("severity", "unknown")
                cat = f.get("category", "unknown")
                summary = f.get("summary", "")
                lines.append(f"- [{sev}] {cat}: {summary}")
            lines.append("")
        ideas = critique.get("novel_ideas") or []
        if ideas:
            lines.append("### Novel Ideas")
            lines.append("")
            for idea in ideas[:30]:
                lines.append(f"- {idea}")
            lines.append("")

    lines.append("## Pages")
    lines.append("")
    for p in report.get("pages", []):
        lines.append(f"### `{p.get('name')}`")
        lines.append("")
        lines.append(f"- URL: `{p.get('url')}`")
        artifacts = p.get("artifacts", {})
        if artifacts.get("screenshot"):
            lines.append(f"- Screenshot: `{artifacts.get('screenshot')}`")
        timing = p.get("timing_ms", {})
        if timing.get("navigation") is not None:
            lines.append(f"- Navigation: `{timing.get('navigation')}ms`")
        console = p.get("console", {})
        counts = console.get("counts", {})
        lines.append(
            f"- Console: `errors={counts.get('error', 0)}` `warnings={counts.get('warning', 0)}`"
        )
        network = p.get("network", {})
        ncounts = network.get("counts", {})
        lines.append(
            f"- Network: `request_failures={ncounts.get('request_failures', 0)}` `http_errors={ncounts.get('http_errors', 0)}`"
        )
        if p.get("page_errors"):
            lines.append(f"- Page errors: `{len(p.get('page_errors'))}`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_report(
    *,
    run_meta: dict[str, Any],
    pages: list[PageEvidence],
    goals: list[str],
    non_goals: list[str],
    llm_block: dict[str, Any] | None,
) -> dict[str, Any]:
    pages_json = []
    for p in pages:
        pages_json.append(
            {
                "name": p.name,
                "url": p.url,
                "artifacts": p.artifacts,
                "timing_ms": p.timing_ms,
                "console": p.console,
                "network": p.network,
                "page_errors": p.page_errors,
                "extracted": p.extracted,
            }
        )

    det = summarize_deterministic_findings(pages)

    report: dict[str, Any] = {
        "schema": 1,
        "generated_at": _utc_now_iso(),
        "meta": run_meta,
        "goals": goals,
        "non_goals": non_goals,
        "pages": pages_json,
        "deterministic_findings": det,
        "llm": llm_block or {"enabled": False},
    }
    return report

