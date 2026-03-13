<!-- markdownlint-disable MD013 MD033 MD041 -->
<p align="center"><img src="assets/datastone_logo.png" width="300" alt="dataStone logo" /></p>
<!-- markdownlint-enable MD033 MD041 -->

# speckit-verify-tasks

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![spec-kit](https://img.shields.io/badge/spec--kit-extension-blueviolet.svg)](https://github.com/speckit)
[![Changelog](https://img.shields.io/badge/changelog-CHANGELOG.md-blue.svg)](CHANGELOG.md)

A [spec-kit](https://github.com/speckit) extension that detects **phantom completions** in `tasks.md`.

A **phantom completion** is a task marked `[X]` as done that was never actually implemented. The checkbox was checked but the code was never written. This happens when an AI agent marks work complete without completing it, when implementation is partial but the task list was not updated, or when a task was copy-marked during a refactor without verifying the underlying work.

`/speckit.verify-tasks` closes this gap by independently verifying every `[X]` task through a five-layer verification cascade, producing a structured markdown report with per-task verdicts, then walking you through each flagged item interactively.

## What it does

When a feature is marked "done" in `tasks.md`, there is no automatic check that the code was actually written. The `/speckit.verify-tasks` command closes that gap by independently verifying every `[X]` task using the following layers:

| Layer | Check | Method |
|-------|-------|--------|
| 1 | File existence | `test -f` / `find` |
| 2 | Git diff presence | `git diff`, `git log` |
| 3 | Content pattern matching | `grep -n` for declared symbols |
| 4 | Wiring / dead-code detection | `git grep` across the repo |
| 5 | Semantic assessment | Agent reads and interprets code structure |

Each task receives one of five verdicts: `✅ VERIFIED`, `🔍 PARTIAL`, `⚠️ WEAK`, `❌ NOT_FOUND`, or `⏭️ SKIPPED`.

## Installation

```sh
specify extension add verify-tasks
```

Or install directly from a specific release:

```sh
specify extension add verify-tasks --from https://github.com/speckit/speckit-verify-tasks/archive/refs/tags/v1.0.0.zip
```

For local development:

```sh
specify extension add --dev /path/to/speckit-verify-tasks
```

## Usage

```sh
/speckit.verify-tasks
/speckit.verify-tasks T003 T007
/speckit.verify-tasks --scope branch
/speckit.verify-tasks T003 --scope uncommitted
```

> ⚠️ **Run in a fresh agent session.** The agent that ran `/speckit.implement` carries context that biases it toward confirming its own work. Always invoke `/speckit.verify-tasks` in a separate session.

### Automatic hook

After `/speckit.implement` finishes, you will be prompted automatically:

> Run `/speckit.verify-tasks` in a **fresh agent session** to check for phantom completions.

The hook is optional — open a new session and run `/speckit.verify-tasks` there.

### Options

| Option | Format | Default | Description |
|--------|--------|---------|-------------|
| Task filter | Space/comma-separated task IDs | all `[X]` tasks | Restrict to specific task IDs |
| Diff scope | `--scope branch\|uncommitted\|plan-anchored\|all` | `all` | Which changes count as evidence |

### Diff scopes

- **`branch`**: files modified vs `origin/main` (or `master`/`develop`)
- **`uncommitted`**: staged and unstaged changes only
- **`plan-anchored`**: all commits since the `**Date**:` field in `plan.md`
- **`all`** (default): branch diff plus uncommitted changes

## Output

The command writes `verify-tasks-report.md` into the feature directory (`$FEATURE_DIR/`) and prints a confirmation. The report contains:

1. **Summary scorecard**: counts per verdict level
2. **Flagged items**: `NOT_FOUND`, `PARTIAL`, `WEAK` tasks with per-layer detail
3. **Verified items**: `VERIFIED` and `SKIPPED` tasks

### Interactive walkthrough

After the report is written, the command enters a sequential walkthrough for each flagged item in severity order (`NOT_FOUND` first, then `PARTIAL`, then `WEAK`). For each item it shows the evidence gap and offers three options:

| Option | What it does |
|--------|--------------|
| **I** (Investigate) | Reads referenced files, runs additional searches, and outputs a detailed analysis of the gap |
| **F** (Fix) | Proposes a specific minimal fix; does not apply it until you confirm with `y` |
| **S** (Skip) | Moves to the next flagged item |

Reply `done` at any point to end the walkthrough early. The agent presents exactly one item per turn and never reveals future items in advance.

## Repository structure

```text
commands/
  speckit.verify-tasks.md      # The slash command (main deliverable)
specs/
  001-verify-tasks-phantom/    # Feature spec for this extension
    spec.md
    plan.md
    tasks.md
    data-model.md
    research.md
    quickstart.md
    checklists/
    contracts/
tests/
  fixtures/
    phantom-tasks/             # 10 tasks, 5 genuine + 5 planted phantoms
    genuine-tasks/             # 10 tasks, all genuinely implemented
    edge-cases/                # Behavioral-only, malformed, and glob tasks
    scalability/               # 50-task synthetic fixture (session overflow test)
  expected-verdicts.md         # Expected evidence level for every fixture task
.specify/
  memory/constitution.md       # Design principles governing the extension
  templates/                   # spec-kit templates
  scripts/bash/                # Prerequisite and setup scripts
.github/
  agents/                      # Agent mode files (*.agent.md)
  prompts/                     # Prompt mode files (*.prompt.md)
```

## Design principles

The extension is governed by eight constitutional principles. The most critical:

- **Asymmetric Error Model**: a missed phantom is catastrophic; a false alarm is acceptable. Ambiguous evidence always yields `PARTIAL`/`WEAK`, never `VERIFIED`.
- **Agent Independence**: verification must run in a session separate from the implementing agent to avoid confirmation bias.
- **Pure Prompt Architecture**: 100% prompt-driven. No Python scripts or external binaries; only shell tools (`grep`, `find`, `git`). Works across Claude Code, GitHub Copilot, Gemini CLI, Cursor, Windsurf, and other spec-kit agents.
- **Verification Cascade**: mechanical layers (1-4) always take precedence. Semantic assessment (layer 5) alone can never produce a `VERIFIED` verdict.

See [`.specify/memory/constitution.md`](.specify/memory/constitution.md) for the full set of principles.

## Requirements

- A spec-kit project with a `tasks.md` inside a feature directory
- An AI agent that supports spec-kit slash commands (Claude Code, GitHub Copilot, Gemini CLI, Cursor, Windsurf, etc.)
- `git` (optional; layers 2 and 4 are skipped gracefully if unavailable)
- The spec-kit prerequisites script at `.specify/scripts/bash/check-prerequisites.sh`

## Troubleshooting

| Message | Meaning | Action |
|---------|---------|--------|
| `ERROR: No tasks.md found in feature directory: {path}` | The prerequisites script could not locate a feature directory, or `tasks.md` is missing from it | Run `/speckit.specify` and `/speckit.tasks` first to create the spec and task list |
| `No completed tasks found to verify.` | No `[X]` tasks exist in `tasks.md` | Mark at least one task complete before running verification |
| `WARNING: Malformed task on line {n}: "{line}" -- skipping` | A line has a broken checkbox syntax or no task ID | Fix the malformed line in `tasks.md`; remaining tasks are still verified |
| `WARNING: Git unavailable -- Layer 2 (Git Diff) skipped for all tasks.` | No `.git` directory found, or `git` is not on PATH | Layers 1, 3, 4, and 5 still run; initialize a git repo for full coverage |
| `WARNING: Shallow clone detected -- Layer 2 diff coverage may be incomplete.` | The repo was cloned with `--depth` | Run `git fetch --unshallow` for complete history |
| `WARNING: plan.md not found -- falling back to scope=all` | `--scope plan-anchored` was requested but `plan.md` does not exist | Use a different scope, or ensure `plan.md` is present in the feature directory |
| `WARNING: No date found in plan.md -- falling back to scope=all` | `plan.md` exists but has no `**Date**: YYYY-MM-DD` field | Add a date field to `plan.md`, or use a different scope |
| `WARNING: Task ID not found: {id} -- skipping.` | A task ID passed as an argument does not exist in `tasks.md` | Check the ID spelling; use `/speckit.verify-tasks` without arguments to verify all tasks |
| `ERROR: Cannot write report to {path}: {reason}` | File system permission or path problem | The report is printed to stdout instead; check directory permissions |

## Authors

**Dave Sharpe** ([dave.sharpe@datastone.ca](mailto:dave.sharpe@datastone.ca)) at **[dataStone Inc.](https://github.com/datastone-inc)**: concept, design, and development

**[Claude (Anthropic)](https://www.anthropic.com)**: co-developed the implementation and test fixtures via GitHub Copilot

## License

[MIT](LICENSE)

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.
