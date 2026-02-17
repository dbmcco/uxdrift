# uxdrift

`uxdrift` is a Speedrift-suite sidecar that:

- drives a real browser (Playwright) to **collect UX evidence** (screenshots, console errors, failed requests)
- optionally asks an LLM to turn that evidence into **glitch reports, UX improvements, and novel ideas**

This repo is intentionally opinionated about *pipes vs decisions*:

- Code is a pipe: collect facts, execute flows, save artifacts.
- Model decides: what matters, why, and what to change next.

## Ecosystem Map

This project is part of the Speedrift suite for Workgraph-first drift control.

- Spine: [Workgraph](https://graphwork.github.io/)
- Orchestrator: [driftdriver](https://github.com/dbmcco/driftdriver)
- Baseline lane: [coredrift](https://github.com/dbmcco/coredrift)
- Optional lanes: [specdrift](https://github.com/dbmcco/specdrift), [datadrift](https://github.com/dbmcco/datadrift), [depsdrift](https://github.com/dbmcco/depsdrift), [uxdrift](https://github.com/dbmcco/uxdrift), [therapydrift](https://github.com/dbmcco/therapydrift), [yagnidrift](https://github.com/dbmcco/yagnidrift), [redrift](https://github.com/dbmcco/redrift)

## Quickstart

```bash
pipx install git+https://github.com/dbmcco/uxdrift.git

# Optional (Linux CI typically needs this; macOS often works with local Chrome channel)
uxdrift install-browsers

# Evidence-only run (no model)
uxdrift run --url http://localhost:3000

# Evidence + LLM critique (OpenAI-compatible; expects OPENAI_API_KEY in env/.env)
uxdrift run --url http://localhost:3000 --llm

# Run a small interaction flow (clicks, waits, extra screenshots)
uxdrift run --url http://localhost:3000 --steps steps.json

# Create GitHub follow-up issues (optional; uses gh CLI auth)
uxdrift run --url http://localhost:3000 --llm --create-issues --github-repo owner/repo
```

Local clone development shortcut (no pipx needed):

```bash
cd uxdrift
./bin/uxdrift run --url http://localhost:3000
```

Outputs land in `.uxdrift/runs/<timestamp>/` (JSON + Markdown + screenshots).

## Workgraph + Speedrift Workflow

`uxdrift` can attach runs to Workgraph tasks (similar to Speedrift):

```bash
# From anywhere (explicit target graph)
uxdrift wg --dir /path/to/repo/.workgraph check --url http://localhost:3000 --write-log --create-followups

# With an explicit task
uxdrift wg --dir /path/to/repo/.workgraph check --task <id> --url http://localhost:3000 --write-log
```

You can also run it from inside the target repo (and omit `--dir`):

```bash
cd /path/to/repo
uxdrift wg check --url http://localhost:3000 --write-log
```

Default outputs go to `.workgraph/.uxdrift/runs/<timestamp>/<task_id>/`.

### Optional per-task spec

In a task description, add:

````md
```uxdrift
schema = 1
url = "http://localhost:3000"
pages = ["/"]
steps = "path/to/steps.json"
goals = ["No console errors", "No 404s"]
non_goals = ["No branding review"]
llm = true
llm_model = "gpt-4o-mini"
```
````

Then you can omit `--url/--page/--steps/--llm` flags and `uxdrift` will use the task spec.

## Config

For now, the CLI is flag-driven. The next step is a `uxdrift.toml` profile format (pages + flows + goals).

## Safety

- Secrets live in `.env` (gitignored).
- `uxdrift run` is read-only with respect to the target app (it only writes local artifacts).
- `uxdrift wg check --write-log/--create-followups` will write to Workgraph via `wg` and will create artifacts under `.workgraph/.uxdrift/`.
