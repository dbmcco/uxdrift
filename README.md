# uxrift

`uxrift` is a Speedrift-adjacent sidecar that:

- drives a real browser (Playwright) to **collect UX evidence** (screenshots, console errors, failed requests)
- optionally asks an LLM to turn that evidence into **glitch reports, UX improvements, and novel ideas**

This repo is intentionally opinionated about *pipes vs decisions*:

- Code is a pipe: collect facts, execute flows, save artifacts.
- Model decides: what matters, why, and what to change next.

## Quickstart

```bash
cd uxrift

# Optional (Linux CI typically needs this; macOS often works with local Chrome channel)
./bin/uxrift install-browsers

# Evidence-only run (no model)
./bin/uxrift run --url http://localhost:3000

# Evidence + LLM critique (OpenAI-compatible; expects OPENAI_API_KEY in env/.env)
./bin/uxrift run --url http://localhost:3000 --llm

# Run a small interaction flow (clicks, waits, extra screenshots)
./bin/uxrift run --url http://localhost:3000 --steps steps.json

# Create GitHub follow-up issues (optional; uses gh CLI auth)
./bin/uxrift run --url http://localhost:3000 --llm --create-issues --github-repo owner/repo
```

Outputs land in `.uxrift/runs/<timestamp>/` (JSON + Markdown + screenshots).

## Workgraph + Speedrift Workflow

`uxrift` can attach runs to Workgraph tasks (similar to Speedrift):

```bash
# From the uxrift repo root (explicit target graph)
./bin/uxrift wg --dir /path/to/repo/.workgraph check --url http://localhost:3000 --write-log --create-followups

# With an explicit task
./bin/uxrift wg --dir /path/to/repo/.workgraph check --task <id> --url http://localhost:3000 --write-log
```

You can also run it from inside the target repo (and omit `--dir`) as long as you call the `uxrift` script by path:

```bash
cd /path/to/repo
/path/to/uxrift/bin/uxrift wg check --url http://localhost:3000 --write-log
```

Default outputs go to `.workgraph/.uxrift/runs/<timestamp>/<task_id>/`.

### Optional per-task spec

In a task description, add:

````md
```uxrift
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

Then you can omit `--url/--page/--steps/--llm` flags and `uxrift` will use the task spec.

## Config

For now, the CLI is flag-driven. The next step is a `uxrift.toml` profile format (pages + flows + goals).

## Safety

- Secrets live in `.env` (gitignored).
- `uxrift run` is read-only with respect to the target app (it only writes local artifacts).
- `uxrift wg check --write-log/--create-followups` will write to Workgraph via `wg` and will create artifacts under `.workgraph/.uxrift/`.
