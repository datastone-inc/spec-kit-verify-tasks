# Quickstart: Verify-Tasks Phantom Completion Detector

**Feature Branch**: `001-verify-tasks-phantom`

---

## What This Extension Does

`verify-tasks` detects **phantom completions** — tasks marked `[X]` in `tasks.md` where the corresponding code is missing, incomplete, or not wired up. It runs a five-layer verification cascade and produces a structured markdown report.

---

## Prerequisites

- A spec-kit project with a `tasks.md` file in the feature's spec directory
- Git repository with commit history (optional but recommended — Layer 2 is skipped without git)
- Standard POSIX shell utilities: `grep`, `find`, `git`

---

## Installation

```bash
specify extension add verify-tasks
```

This installs:

- `commands/speckit.verify-tasks.md` — the slash command
- `tests/` — synthetic test fixtures for validation

---

## Usage

### Basic: Verify All Completed Tasks

```
/speckit.verify-tasks
```

Verifies every `[X]` task in `tasks.md` using the `all` diff scope (most inclusive).

### Targeted: Re-Verify Specific Tasks

```
/speckit.verify-tasks T-003 T-007
```

Only verifies the specified task IDs. Useful after fixing flagged items.

### Scoped: Use a Specific Diff Scope

```
/speckit.verify-tasks --scope branch
```

Options: `branch`, `uncommitted`, `plan-anchored`, `all` (default).

### Combined

```
/speckit.verify-tasks T-003 --scope uncommitted
```

---

## Output

The command produces `verify-tasks-report.md` in the feature's spec directory with:

1. **Summary Scorecard** — counts per evidence level
2. **Flagged Items** — sorted by severity (NOT_FOUND → PARTIAL → WEAK)
3. **Verified Items** — tasks that passed all checks
4. **Interactive Walkthrough** — guided resolution for each flagged item

### Evidence Levels

| Verdict | Meaning |
|---------|---------|
| ✅ VERIFIED | All mechanical checks pass — strong evidence of implementation |
| 🔍 PARTIAL | Some evidence found but gaps exist |
| ⚠️ WEAK | Evidence is indirect or requires semantic interpretation |
| ❌ NOT_FOUND | No evidence of implementation — probable phantom completion |
| ⏭️ SKIPPED | Task has no mechanically verifiable indicators |

---

## Important: Fresh Session Advisory

**Always run `/speckit.verify-tasks` in a separate agent session from the one that ran `/speckit.implement`.**

The implementing agent's context biases it toward confirming its own work. Independent verification in a fresh session eliminates this confirmation bias.

---

## Verification Cascade (How It Works)

For each `[X]` task, five verification layers run in order:

1. **File Existence** — Do the referenced files exist?
2. **Git Diff Cross-Reference** — Were the files modified in the specified diff scope?
3. **Content Pattern Matching** — Do expected symbols/patterns appear in the files?
4. **Dead-Code Detection** — Are declared symbols actually referenced/called/imported?
5. **Semantic Assessment** — Does the described behavior appear to be implemented?

A task reaches `VERIFIED` only when ALL applicable mechanical layers (1–4) produce positive evidence. Semantic assessment alone never yields `VERIFIED`.

---

## Development: Running Test Fixtures

The `tests/` directory contains synthetic test fixtures with repo-relative file paths:

```
tests/
├── fixtures/
│   ├── phantom-tasks/     # 10 tasks: 5 genuine + 5 planted phantom completions
│   ├── genuine-tasks/     # 10 tasks: all genuinely implemented
│   ├── edge-cases/        # Behavioral-only, malformed, glob, and multi-file tasks
│   └── scalability/       # 50 tasks: session overflow stress test
└── expected-verdicts.md   # Expected evidence level for every fixture task
```

### Running a fixture

1. **Commit** any in-progress work so you can cleanly revert afterward:
   ```bash
   git add -A && git commit -m "WIP: save before fixture test"
   ```

2. **Copy** a fixture's `tasks.md` over the feature spec's `tasks.md`:
   ```bash
   cp tests/fixtures/phantom-tasks/tasks.md specs/001-verify-tasks-phantom/tasks.md
   ```

3. **Run** `/speckit.verify-tasks` in an agent chat session (no fresh session needed — there is no implementation context to bias results)

4. **Compare** the generated `specs/001-verify-tasks-phantom/verify-tasks-report.md` against `tests/expected-verdicts.md`

5. **Revert** all test changes:
   ```bash
   git checkout .
   ```

### Why fixture paths are repo-relative

Each fixture's `tasks.md` references files using full repo-relative paths (e.g., `tests/fixtures/phantom-tasks/src/auth.py` instead of `src/auth.py`). This is because `/speckit.verify-tasks` resolves file paths from the repository root, not from the fixture directory.
