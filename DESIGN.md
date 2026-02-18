# uxdrift Design

## Goals

- Make UX evaluation **repeatable** (not a one-off “vibes” review).
- Capture **evidence** (screenshots, console/network errors, minimal page text).
- Use Playwright for **real interaction** (not DOM scraping).
- Use an LLM for **judgment calls** (prioritization, product ideas, novel UX improvements).

## Non-Goals (for MVP)

- Not a full E2E test framework (we can execute flows, but we’re not replacing Playwright Test).
- Not a full Lighthouse replacement.
- No auto-editing of product code.

## Architecture (Model-Mediated)

### Pipes (Code)

- Browser runner:
  - navigate to pages
  - capture screenshots
  - record console errors, JS page errors, request failures, HTTP 4xx/5xx
- Artifact writer:
  - store run metadata + evidence in `.uxdrift/runs/<timestamp>/`
- Optional issue/task emitter (future):
  - create GitHub issues or workgraph follow-up tasks

### Decisions (Model)

- Decide what’s “bad UX” vs “acceptable tradeoff” given goals.
- Rank improvements by impact vs effort.
- Propose novel ideas and experiments.
- Apply an explicit POV pack when provided (for example `doet-norman-v1`) so findings map to stable design principles.

## Report Schema (v1)

Single JSON report with:

- run metadata (time, url, browser, options)
- evidence per page (artifacts + errors)
- deterministic findings (console/network/page errors)
- optional LLM critique (structured findings + ideas)
- optional POV metadata + scorecard (`pov`, `pov_scorecard`, `principle_tags`)

## POV Packs

`uxdrift` can run model critique with a named design POV so reasoning is consistent across runs.

Initial built-in pack:

- `doet-norman-v1`:
  - discoverability
  - signifiers
  - mapping
  - feedback
  - constraints
  - conceptual model
  - error prevention/recovery

## Workgraph Integration

`uxdrift wg check` mirrors the Speedrift pattern:

- finds `.workgraph/graph.jsonl`
- chooses the current task (open/in-progress)
- runs capture/critique
- optionally logs a one-line summary back to the task (`wg log`)
- optionally creates a deterministic follow-up task (`wg add`) blocked by the origin
