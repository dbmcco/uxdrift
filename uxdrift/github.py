from __future__ import annotations

import subprocess
from typing import Iterable


def create_issue(
    *,
    repo: str,
    title: str,
    body: str,
    labels: Iterable[str] | None = None,
) -> None:
    cmd = ["gh", "issue", "create", "--repo", repo, "--title", title, "--body", body]
    if labels:
        for label in labels:
            lab = str(label).strip()
            if lab:
                cmd += ["--label", lab]
    subprocess.check_call(cmd)

