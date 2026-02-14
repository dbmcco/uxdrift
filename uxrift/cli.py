from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Literal

from uxrift.env import load_default_dotenv
from uxrift.github import create_issue
from uxrift.llm.critique import critique as llm_critique
from uxrift.playwright_runner import capture_pages
from uxrift.report import build_report, render_markdown, write_json, write_text


class ExitCode:
    ok: int = 0
    usage: int = 2
    findings: int = 3
    error: int = 1


_SEV_ORDER: dict[str, int] = {"info": 0, "low": 1, "medium": 2, "high": 3, "blocker": 4}


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="uxrift", add_help=True)
    sub = p.add_subparsers(dest="cmd", required=True)

    run = sub.add_parser("run", help="Run UX capture + optional LLM critique")
    run.add_argument("--url", required=True, help="Base URL, e.g. http://localhost:3000")
    run.add_argument("--page", action="append", default=[], help="Path to capture (repeatable). Default: /")
    run.add_argument("--out", help="Output dir (default: .uxrift/runs/<timestamp>)")
    run.add_argument("--headful", action="store_true", help="Run with a visible browser window")
    run.add_argument("--browser", default="chromium", choices=["chromium", "firefox", "webkit"])
    run.add_argument("--channel", help='Browser channel (e.g. "chrome"). If unavailable, falls back.')
    run.add_argument("--nav-timeout-ms", type=int, default=15_000)
    run.add_argument("--wait-until", default="domcontentloaded", choices=["load", "domcontentloaded", "networkidle"])
    run.add_argument("--steps", help="JSON file with Playwright interaction steps to run after load")
    run.add_argument("--goal", action="append", default=[], help="Goal text (repeatable)")
    run.add_argument("--goals-file", action="append", default=[], help="File with goals/spec (repeatable)")
    run.add_argument("--non-goal", action="append", default=[], help="Non-goal text (repeatable)")
    run.add_argument("--llm", action="store_true", help="Enable LLM critique (OpenAI-compatible)")
    run.add_argument("--llm-base-url", default=os.environ.get("UXRIFT_LLM_BASE_URL", "https://api.openai.com/v1"))
    run.add_argument("--llm-model", default=os.environ.get("UXRIFT_LLM_MODEL", "gpt-4o-mini"))
    run.add_argument("--github-repo", help="Target repo for follow-up issues (e.g. dbmcco/paia-os)")
    run.add_argument("--create-issues", action="store_true", help="Create GitHub issues for notable findings")
    run.add_argument(
        "--issue-threshold",
        default="high",
        choices=["blocker", "high", "medium", "low", "info"],
        help="Minimum severity to create an issue (default: high)",
    )

    install = sub.add_parser("install-browsers", help="Install Playwright browsers (chromium)")
    install.add_argument("--with-deps", action="store_true", help="Install OS deps too (recommended on Linux CI)")
    install.add_argument("--browser", default="chromium", choices=["chromium", "firefox", "webkit"])

    return p.parse_args(argv)


def _default_out_dir(project_dir: Path) -> Path:
    ts = time.strftime("%Y%m%d-%H%M%S")
    return project_dir / ".uxrift" / "runs" / ts


def _read_text_file(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def _collect_goals(goals: list[str], goal_files: list[str]) -> list[str]:
    out = [g.strip() for g in goals if g.strip()]
    for f in goal_files:
        txt = _read_text_file(Path(f))
        if txt:
            out.append(txt)
    return out


def _truncate(s: str, max_chars: int) -> str:
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 1] + "…"


def _install_browsers(args: argparse.Namespace) -> int:
    cmd = [sys.executable, "-m", "playwright", "install"]
    if args.with_deps:
        cmd.append("--with-deps")
    cmd.append(args.browser)
    subprocess.check_call(cmd)
    return ExitCode.ok


def _sev_at_least(sev: str, threshold: str) -> bool:
    return _SEV_ORDER.get(str(sev), 0) >= _SEV_ORDER.get(str(threshold), 0)


def _create_followup_issues(*, repo: str, threshold: str, report: dict[str, Any]) -> None:
    run_meta = report.get("meta") or {}
    base_url = str(run_meta.get("base_url") or "")
    generated_at = str(report.get("generated_at") or "")

    issues: list[dict[str, Any]] = []

    for f in (report.get("deterministic_findings") or []):
        sev = str(f.get("severity") or "info")
        if not _sev_at_least(sev, threshold):
            continue
        issues.append(
            {
                "severity": sev,
                "category": str(f.get("category") or "glitch"),
                "summary": str(f.get("summary") or "finding"),
                "evidence": f.get("evidence") or [],
                "fix": "",
            }
        )

    llm = report.get("llm") or {}
    parsed = llm.get("parsed") or {}
    for f in (parsed.get("findings") or []):
        sev = str(f.get("severity") or "info")
        if not _sev_at_least(sev, threshold):
            continue
        issues.append(
            {
                "severity": sev,
                "category": str(f.get("category") or "other"),
                "summary": str(f.get("summary") or "finding"),
                "evidence": f.get("evidence") or [],
                "fix": str(f.get("fix") or ""),
            }
        )

    # Best-effort dedupe by (severity, category, summary).
    seen: set[tuple[str, str, str]] = set()
    for it in issues:
        key = (it["severity"], it["category"], it["summary"])
        if key in seen:
            continue
        seen.add(key)

        title = f"[uxrift] {it['category']} ({it['severity']}): {it['summary']}"
        if len(title) > 120:
            title = title[:119] + "…"

        body_lines = [
            f"Generated by uxrift on `{generated_at}`",
            "",
            f"- Base URL: `{base_url}`",
            f"- Severity: `{it['severity']}`",
            f"- Category: `{it['category']}`",
            "",
            "## Summary",
            "",
            it["summary"],
        ]
        if it.get("fix"):
            body_lines += ["", "## Suggested Fix", "", it["fix"]]
        if it.get("evidence"):
            body_lines += ["", "## Evidence", ""]
            for ev in it["evidence"]:
                body_lines.append(f"- {ev}")

        create_issue(repo=repo, title=title, body="\n".join(body_lines) + "\n", labels=["uxrift"])


def _run(args: argparse.Namespace) -> int:
    project_dir = Path(__file__).resolve().parent.parent
    load_default_dotenv(project_dir=project_dir)

    out_dir = Path(args.out) if args.out else _default_out_dir(project_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    pages = args.page or ["/"]
    steps = None
    if args.steps:
        raw = Path(args.steps).read_text(encoding="utf-8")
        parsed = json.loads(raw)
        if not isinstance(parsed, list):
            raise ValueError("--steps must be a JSON array")
        steps = parsed

    ev_pages, run_meta = capture_pages(
        base_url=args.url,
        pages=pages,
        out_dir=out_dir,
        headful=bool(args.headful),
        browser=args.browser,
        browser_channel=args.channel,
        nav_timeout_ms=int(args.nav_timeout_ms),
        wait_until=args.wait_until,
        steps=steps,
    )

    goals = _collect_goals(args.goal, args.goals_file)
    non_goals = [g.strip() for g in (args.non_goal or []) if g.strip()]

    llm_block: dict[str, Any] | None = None
    if args.llm:
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("UXRIFT_LLM_API_KEY")
        if not api_key:
            raise ValueError("LLM enabled but OPENAI_API_KEY (or UXRIFT_LLM_API_KEY) is not set.")
        screenshot_paths: list[Path] = []
        for p in ev_pages:
            step_shots = p.artifacts.get("step_screenshots")
            if isinstance(step_shots, list):
                for s in step_shots:
                    if isinstance(s, str) and s:
                        screenshot_paths.append(Path(s))
            shot = p.artifacts.get("screenshot")
            if isinstance(shot, str) and shot:
                screenshot_paths.append(Path(shot))
        evidence_for_llm = {
            "meta": run_meta,
            "deterministic_counts": {
                "console_errors": sum(int(p.console.get("counts", {}).get("error", 0)) for p in ev_pages),
                "console_warnings": sum(int(p.console.get("counts", {}).get("warning", 0)) for p in ev_pages),
                "request_failures": sum(int(p.network.get("counts", {}).get("request_failures", 0)) for p in ev_pages),
                "http_errors": sum(int(p.network.get("counts", {}).get("http_errors", 0)) for p in ev_pages),
                "page_errors": sum(len(p.page_errors) for p in ev_pages),
            },
            "pages": [
                {
                    "name": p.name,
                    "url": p.url,
                    "timing_ms": p.timing_ms,
                    "console_counts": p.console.get("counts"),
                    "console_error_samples": [
                        _truncate(str(m.get("text") or ""), 400)
                        for m in (p.console.get("messages") or [])
                        if m.get("type") == "error"
                    ][:10],
                    "console_warning_samples": [
                        _truncate(str(m.get("text") or ""), 400)
                        for m in (p.console.get("messages") or [])
                        if m.get("type") == "warning"
                    ][:10],
                    "network_counts": p.network.get("counts"),
                    "http_error_samples": (p.network.get("http_errors") or [])[:10],
                    "request_failure_samples": (p.network.get("request_failures") or [])[:10],
                    "page_error_count": len(p.page_errors),
                    "page_error_samples": [_truncate(e, 400) for e in p.page_errors][:10],
                    "title": p.extracted.get("title"),
                    "text": p.extracted.get("text"),
                    "performance_navigation": p.extracted.get("performance_navigation"),
                    "screenshot": p.artifacts.get("screenshot"),
                }
                for p in ev_pages
            ],
        }
        llm_block = llm_critique(
            base_url=args.llm_base_url,
            api_key=api_key,
            model=args.llm_model,
            goals=goals,
            non_goals=non_goals,
            evidence=evidence_for_llm,
            screenshot_paths=screenshot_paths,
        )

    report = build_report(run_meta=run_meta, pages=ev_pages, goals=goals, non_goals=non_goals, llm_block=llm_block)

    report_json = out_dir / "report.json"
    report_md = out_dir / "report.md"
    write_json(report_json, report)
    write_text(report_md, render_markdown(report))

    if args.create_issues:
        if not args.github_repo:
            raise ValueError("--create-issues requires --github-repo <owner/repo>")
        _create_followup_issues(repo=str(args.github_repo), threshold=str(args.issue_threshold), report=report)

    # Exit non-zero if we have deterministic high-ish findings, or LLM produced blockers/high.
    det = report.get("deterministic_findings") or []
    if any(f.get("severity") in ("high", "medium") for f in det):
        return ExitCode.findings

    llm_parsed = (report.get("llm") or {}).get("parsed") or {}
    if any(f.get("severity") in ("blocker", "high") for f in (llm_parsed.get("findings") or [])):
        return ExitCode.findings

    return ExitCode.ok


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv or sys.argv[1:])
    try:
        if args.cmd == "install-browsers":
            return _install_browsers(args)
        if args.cmd == "run":
            return _run(args)
        raise ValueError(f"Unknown command: {args.cmd}")
    except KeyboardInterrupt:
        return ExitCode.error
