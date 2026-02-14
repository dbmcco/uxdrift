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

# Create GitHub follow-up issues (optional; uses gh CLI auth)
./bin/uxrift run --url http://localhost:3000 --llm --create-issues --github-repo owner/repo
```

Outputs land in `.uxrift/runs/<timestamp>/` (JSON + Markdown + screenshots).

## Config

For now, the CLI is flag-driven. The next step is a `uxrift.toml` profile format (pages + flows + goals).

## Safety

- Secrets live in `.env` (gitignored).
- `uxrift` never writes to target projects unless you explicitly enable follow-up creation (planned).
