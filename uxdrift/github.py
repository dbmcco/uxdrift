from __future__ import annotations

import logging
import subprocess
from typing import Iterable

_log = logging.getLogger(__name__)


def create_issue(
    *,
    repo: str,
    title: str,
    body: str,
    labels: Iterable[str] | None = None,
) -> None:
    """Create a GitHub issue via the gh CLI. Logs a warning and returns on failure."""
    cmd = ["gh", "issue", "create", "--repo", repo, "--title", title, "--body", body]
    if labels:
        for label in labels:
            lab = str(label).strip()
            if lab:
                cmd += ["--label", lab]
    try:
        subprocess.check_call(cmd)
    except FileNotFoundError:
        _log.warning("gh CLI not found; skipping GitHub issue creation for %r", title)
    except subprocess.CalledProcessError as exc:
        _log.warning("gh issue create failed (exit %d); skipping: %r", exc.returncode, title)

