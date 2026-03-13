---
description: Detect phantom completions in tasks.md by running a five-layer verification cascade and producing a structured markdown verification report.
handoffs:
  - speckit.implement
---

## User Input

```text
$ARGUMENTS
```

**Supported options** (parsed from `$ARGUMENTS`):

| Option | Format | Default | Description |
|--------|--------|---------|-------------|
| Task filter | Space/comma-separated task IDs | None — verify all `[X]` tasks | Restrict verification to specific task IDs |
| Diff scope | `--scope branch\|uncommitted\|plan-anchored\|all` | `all` | Which changes count as implementation evidence |

**Examples**:

```text
/speckit.verify-tasks
/speckit.verify-tasks T003 T007
/speckit.verify-tasks --scope branch
/speckit.verify-tasks T003 --scope uncommitted
```

---

## Outline

**Display the following advisory banner to the user before proceeding:**

> ⚠️ **FRESH SESSION ADVISORY**: For maximum reliability, run `/speckit.verify-tasks`
> in a **separate** agent session from the one that performed `/speckit.implement`.
> The implementing agent's context biases it toward confirming its own work.
> This is even more important if the current session ran `/speckit.implement` just prior.
> Open a fresh session, navigate to this repository, and invoke the command there.

---

### Step 1: Prerequisites Check

1. Run the following command from the repository root:

   ```sh
   bash .specify/scripts/bash/check-prerequisites.sh --json
   ```

2. Parse the JSON output. Extract `FEATURE_DIR` as an absolute path.
3. Check that `$FEATURE_DIR/tasks.md` exists.
   - If it does not exist: output `ERROR: No tasks.md found in feature directory: $FEATURE_DIR` and **stop**.
4. Store `FEATURE_DIR` for use in all subsequent steps.

---

### Step 2: Task Parsing

From `$FEATURE_DIR/tasks.md`, extract all tasks marked `[X]` (completed). For each task line:

1. **Identify completed tasks**: Match lines with checkbox `- [X]` or `- [x]` (case-insensitive).
2. **Extract Task ID**: The first identifier-like token after the checkbox — accept any of:
   - Numeric: `1`, `1.1`, `2.3.1`
   - Prefixed: `T001`, `T-003`, `FEAT-05`, `SC-001`
   - If no explicit ID token is found, generate one from the line number: `LINE-{n}`
   - Emit `WARNING: No task ID found on line {n}: "{line}"` for malformed entries; **continue** processing remaining tasks.
3. **Extract optional markers**: `[P]` (parallel), `[US1]`/`[US2]` etc. (user story labels).
4. **Extract file paths**: Scan the description for:
   - Exact paths: `path/to/file.ext`, backtick-wrapped paths `` `src/foo.py` ``
   - Glob patterns: `tests/**/*.test.js`, `src/**`
   - Directory references: `commands/`, `tests/fixtures/`
5. **Extract code references**: Backtick-wrapped symbol names (function names, class names, type definitions, config keys) from the description, e.g. `` `handleClick` ``, `` `UserModel` ``.
6. **Extract acceptance criteria**: Lines indented under the task that begin with `Given`, `When`, `Then`, or `-`.
7. **Record line number** and **nesting depth** (via leading spaces/indentation).
8. Build a **task list** of all extracted tasks. If no `[X]` tasks are found:
   - Output `No completed tasks found to verify.` and **stop** cleanly.

**Task filter (User Story 2)**: If `$ARGUMENTS` contains task IDs (e.g., `T003 T007`), restrict the task list to only those IDs. For any specified ID not found in `tasks.md`, emit `WARNING: Task ID not found: {id} — skipping.`

---

### Step 3: Diff Scope Determination

1. **Parse `--scope` argument** from `$ARGUMENTS`. If absent, default to `all`.
2. **Detect git availability**:

   ```sh
   git rev-parse --git-dir 2>/dev/null
   ```

   If this fails (no `.git`, or git unavailable), set `GIT_AVAILABLE=false`. Skip all git-dependent steps and note in the report: `⚠️ Git unavailable — Layer 2 (Git Diff) skipped for all tasks.`
3. **Determine base ref** (when `GIT_AVAILABLE=true`) by trying in order:
   `origin/main`, `origin/master`, `origin/develop`, `main`, `master`
   Use the first one that exists (`git rev-parse --verify {ref} 2>/dev/null`). Store as `BASE_REF`.
4. **Map scope to git command**:

   | Scope | Command |
   |-------|---------|
   | `branch` | `git diff "$BASE_REF"...HEAD --name-only` |
   | `uncommitted` | `git diff HEAD --name-only` |
   | `plan-anchored` | Extract `**Date**: {YYYY-MM-DD}` from `$FEATURE_DIR/plan.md`; run `git log --since="{DATE}" --name-only --pretty=""`. If `plan.md` does not exist or contains no `**Date**:` field, emit `WARNING: plan.md not found or missing date — falling back to scope=all` and use `all` scope instead. |
   | `all` (default) | `git diff "$BASE_REF"..HEAD --name-only` plus `git status --short` for uncommitted changes |

5. Collect the list of **changed files** for the scope. Store as `CHANGED_FILES`.
6. If the repo is a shallow clone (`git rev-parse --is-shallow-repository` returns `true`): emit `WARNING: Shallow clone detected — Layer 2 diff coverage may be incomplete.`

---

### Step 4 (Layer 1): File Existence Verification

For each task in the task list:

1. For each `file_path` in the task's extracted paths:
   - Expand any glob patterns: `find . -path "./{glob}" 2>/dev/null`
   - Check if the file/directory exists: `test -f {path} || test -d {path}`
   - **Rename detection**: If a referenced file does not exist and `GIT_AVAILABLE=true`, check for renames:

     ```sh
     git log --diff-filter=R --summary -- "{file_path}" 2>/dev/null
     git diff "$BASE_REF"..HEAD --diff-filter=R --name-status 2>/dev/null | grep "{filename}"
     ```

     If a rename is detected, record the new path in the layer detail (e.g., `"src/auth.py" renamed to "src/authentication.py"`) and use the new path for subsequent layers.
   - If **all** referenced paths exist (or were resolved via rename) → layer result: `positive`
   - If **any** referenced path is missing (and no rename detected) → layer result: `negative`; record the missing path(s).
   - If the task has no file paths → layer result: `not_applicable`
2. Record `VerificationLayerResult` for `file_existence` per task.

---

### Step 5 (Layer 2): Git Diff Cross-Reference

For each task (skip if `GIT_AVAILABLE=false`):

1. For each `file_path` in the task's extracted paths:
   - Check whether `file_path` appears in `CHANGED_FILES`.
   - For glob patterns, check if any matching file appears in `CHANGED_FILES`.
2. If **at least one** referenced file was modified in scope → layer result: `positive`
3. If **no** referenced file was modified in scope → layer result: `negative`
4. If task has no file paths → layer result: `not_applicable`
5. If `GIT_AVAILABLE=false` → layer result: `skipped`
6. Record `VerificationLayerResult` for `git_diff` per task.

---

### Step 6 (Layer 3): Content Pattern Matching

**Context-sensitivity gate**: Before running content pattern matching, assess how "symbols" manifest in the artifact type referenced by the task. Adapt the search strategy to match the artifact:

| Artifact Type | What counts as a "symbol" | Search strategy |
|---------------|--------------------------|----------------|
| Application code (`.py`, `.js`, `.ts`, `.java`, `.go`, `.rs`, etc.) | Function names, class names, method names, type definitions, exported constants | `grep -n "def {symbol}\|function {symbol}\|class {symbol}\|export.*{symbol}\|const {symbol}"` |
| SQL files (`.sql`, `.ddl`) | Table names, column names, constraint names, index names | `grep -n "CREATE.*{symbol}\|ALTER.*{symbol}\|INSERT.*{symbol}\|{symbol}"` |
| Configuration files (`.yml`, `.yaml`, `.toml`, `.ini`, `.json`, `.env`) | Key names, section headers, environment variable names | `grep -n "{symbol}"` (plain text match — keys are typically unique strings) |
| Shell scripts (`.sh`, `.bash`) | Function names, variable names | `grep -n "{symbol}()\|{symbol}=\|export {symbol}"` |
| Markdown/prompt files (`.md`, `.prompt.md`) | Section headings, step identifiers, key phrases | `grep -n "## .*{symbol}\|### .*{symbol}\|{symbol}"` |
| CI/CD files (`.yml` in `.github/`, `Dockerfile`, `Makefile`) | Job names, stage names, target names, directives | `grep -n "{symbol}"` |
| HTML/template files | Element IDs, component names, class names | `grep -n "id=.*{symbol}\|class=.*{symbol}\|{symbol}"` |

If the artifact type is not listed above, fall back to plain `grep -n "{symbol}"` — a direct text match is always valid as a baseline.

> **Accuracy note**: The content pattern matching layer is strongest on application source code where function/class definitions provide clear grep targets. For non-code artifacts (SQL, config, markdown, shell scripts, binary/generated files), matches are less precise and may produce false positives. This is acceptable under the asymmetric error model — a false flag is reviewed and dismissed in seconds during the walkthrough; a missed phantom can ship to production. When Layer 3 results seem uncertain for a non-code artifact, record the result but note the reduced confidence in the layer detail.

For each task:

1. **Determine artifact type** from the file extensions referenced in the task.
2. For each `code_reference` (symbol name) extracted from the task:
   - **Skip files that Layer 1 determined do not exist** (and were not resolved via rename). Only grep files confirmed present.
   - Search each referenced file using the **artifact-appropriate strategy** from the table above.
   - If the artifact type supports definition-prefix matching (application code), also search with definition prefixes to distinguish declaration from usage.
3. If **all** expected symbols are found in the referenced files → layer result: `positive`
4. If **some** symbols are found but others are missing → layer result: `negative` (partial miss)
5. If **no** code references exist in the task → layer result: `not_applicable`
6. Record `VerificationLayerResult` for `content_match` per task.

---

### Step 7 (Layer 4): Dead-Code Detection

**Context-sensitivity gate**: Before running dead-code checks for a task, assess whether cross-file referencing is *expected* for the artifact type:

- **`not_applicable`** (skip this layer) when the task creates artifacts that are consumed by runtime, tooling, or convention rather than imported by application code:
  - SQL migrations, seed files, schema definitions (`.sql`, `.ddl`)
  - Configuration files (`.yml`, `.yaml`, `.toml`, `.ini`, `.json`, `.env`)
  - CI/CD pipelines, Dockerfiles, Makefiles, shell scripts
  - Prompt/command files (`.md` command files, `.prompt.md`)
  - Static assets, HTML templates, CSS files
  - Test files (test functions are invoked by a test runner, not imported by application code)
- **Applicable** (proceed with checks below) when the task creates functions, classes, methods, modules, or API endpoints that are expected to be imported/called/referenced by other application code.

When in doubt about whether an artifact type needs wiring, **default to applicable** — this preserves the asymmetric error model (false positives are acceptable, false negatives are not).

For each task where Layer 3 found symbol definitions (`positive` or partial) **and** the context-sensitivity gate determined dead-code detection is applicable:

1. For each found symbol:
   - **Cross-repository reference scan** — search for the symbol outside its own definition file:

     ```sh
     git grep -n "{symbol}" -- . --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=vendor --exclude-dir=__pycache__ --exclude-dir=.venv --exclude-dir=dist --exclude-dir=build 2>/dev/null || grep -rn "{symbol}" . --exclude-dir=.git --exclude-dir=node_modules --exclude-dir=vendor --exclude-dir=__pycache__ --exclude-dir=.venv --exclude-dir=dist --exclude-dir=build
     ```

     Also check for project-specific directories to exclude: if `.gitignore` exists, respect its patterns for filtering search results. Exclude the file where the symbol is defined.
   - **Filter false positives** — discard matches that are:
     - Inside comment lines (`#`, `//`, `/*`, `<!--`)
     - Inside string literals (surrounded by `"` or `'`)
   - **If external references remain** → symbol is **wired** → layer result contribution: `positive`
   - **If no external references remain** → symbol is **dead code** → layer result contribution: `negative`; record: `"{symbol}" declared in {file} but never imported/called/referenced`
2. **Aggregate** across all symbols:
   - ALL symbols wired → `positive`
   - ANY symbol dead → `negative`
   - No symbols to check → `not_applicable`
3. Record `VerificationLayerResult` for `dead_code` per task.

---

### Step 8 (Layer 5): Semantic Assessment

For tasks where mechanical layers (1–4) are inconclusive or the task has no mechanically verifiable indicators:

1. **Read the relevant files** referenced in the task.
2. Read `$FEATURE_DIR/spec.md` (if available) for context on the described behavior.
3. Evaluate whether the described behavior appears to be implemented based on code structure, flow, and intent.
4. **Always label this result as interpretive**:
   - `⚠️ Interpretive: {explanation of what was assessed and why}`
5. Layer result — assess evidence of the *specific behavior described in the task*:
   - `positive` — the logic flow for the described behavior visibly exists: the feature's entry point is present and connected, the relevant logic is traceable through the code, and the output or effect the task describes is achievable from the current implementation
   - `negative` — the described behavior has no visible implementation: files may exist but contain no logic relevant to the task's stated purpose
   - `not_applicable` — no files are readable or the task description contains no behavior to evaluate

> **Invariant**: Semantic assessment (`layer 5`) alone **NEVER yields `VERIFIED`** for a task that has mechanically verifiable indicators (file paths or code references). It can only elevate a result to `WEAK` when mechanical layers are `not_applicable` or `skipped`.

---

### Step 9: Evidence Level Assignment

For each task, combine the five layer results into a final `TaskVerdict` using these rules:

| Evidence Level | Criteria |
|----------------|----------|
| `✅ VERIFIED` | ALL applicable mechanical layers (1–4) return `positive` |
| `🔍 PARTIAL` | At least one mechanical layer returns `positive` AND at least one returns `negative` |
| `⚠️ WEAK` | ONLY semantic layer returns `positive`, OR mechanical evidence is ambiguous (symbols found only in comments/strings) |
| `❌ NOT_FOUND` | No layers return `positive` — no evidence of implementation found |
| `⏭️ SKIPPED` | ALL mechanical layers return `not_applicable` — task has no verifiable indicators |

**Key rules**:

- Ambiguous evidence → `PARTIAL` or `WEAK`, **never** `VERIFIED`
- `SKIPPED` tasks are not failures — they are behavioral-only tasks with no mechanically checkable outputs
- `not_applicable` layers do not count against `VERIFIED`; only `negative` layers prevent it
- `skipped` layers (e.g., Layer 2 when git is unavailable, Layer 4 when context-sensitivity gate deems it not applicable) are treated identically to `not_applicable` — they do not count as applicable and do not prevent `VERIFIED`. A skipped layer represents an environment limitation or inapplicable check, not an evidence gap.

---

### Step 10: Verification Report Generation

Write the verification report to `$FEATURE_DIR/verify-tasks-report.md` (overwrite if it already exists).

Report structure:

```markdown
# Verification Report: {Feature Name}

**Date**: {today's date ISO} | **Scope**: {scope_type} | **Tasks Verified**: {count}

---

> ⚠️ **FRESH SESSION ADVISORY**: For maximum reliability, run `/speckit.verify-tasks`
> in a separate agent session from the one that performed `/speckit.implement`.
> The implementing agent's context biases it toward confirming its own work.

---

## Summary Scorecard

| Verdict | Count |
|---------|-------|
| ✅ VERIFIED | {n} |
| 🔍 PARTIAL | {n} |
| ⚠️ WEAK | {n} |
| ❌ NOT_FOUND | {n} |
| ⏭️ SKIPPED | {n} |

---

## Flagged Items

### ❌ NOT_FOUND

| Task | Verdict | Summary |
|------|---------|---------|
| {task_id} | ❌ NOT_FOUND | {one-line summary} |

{per-task detail block for each NOT_FOUND task}

### 🔍 PARTIAL

| Task | Verdict | Summary |
|------|---------|---------|
| {task_id} | 🔍 PARTIAL | {one-line summary} |

{per-task detail block for each PARTIAL task}

### ⚠️ WEAK

| Task | Verdict | Summary |
|------|---------|---------|
| {task_id} | ⚠️ WEAK | {one-line summary} |

{per-task detail block for each WEAK task}

---

## Verified Items

| Task | Verdict | Summary |
|------|---------|---------|
| {task_id} | ✅ VERIFIED | {one-line summary} |

---

## Unassessable Items

| Task | Verdict | Summary |
|------|---------|---------|
| {task_id} | ⏭️ SKIPPED | {one-line summary} |
```

**Per-task detail block** (include for every flagged task):

```markdown
**{task_id}**: {first 80 chars of task description}

| Layer | Result | Detail |
|-------|--------|--------|
| 1. File Existence | ✅ / ❌ / ⏭️ N/A | {what was checked and found} |
| 2. Git Diff       | ✅ / ❌ / ⏭️ N/A | {which files were/were not in diff} |
| 3. Content Match  | ✅ / ❌ / ⏭️ N/A | {which symbols were/were not found} |
| 4. Dead-Code Check| ✅ / ❌ / ⏭️ N/A | {which symbols are wired vs dead} |
| 5. Semantic       | ✅ / ⚠️ Interp / ⏭️ N/A | ⚠️ Interpretive: {assessment} |
```

**Machine-parseable verdict line** (included at the end of each task's section):

```text
| {TASK_ID} | {EMOJI} {VERDICT} | {one-line summary} |
```

After writing the report, output: `✅ Report written to: {FEATURE_DIR}/verify-tasks-report.md`

---

### Step 11: Interactive Walkthrough (User Story 4)

After report generation, enter the sequential flagged-item walkthrough. Present **exactly one flagged item at a time** in severity order (`NOT_FOUND` first, then `PARTIAL`, then `WEAK`).

**If there are no flagged items**, skip this step entirely and output:

```text
✅ No flagged items — verification complete.
Report: {FEATURE_DIR}/verify-tasks-report.md
```

**Walkthrough loop** (one item per turn):

1. Display the current flagged item:

   ```text
   ─────────────────────────────────────────────────
   Flagged item {n} of {total}: {task_id}
   {task description}
   Verdict: {EMOJI} {evidence_level}

   Evidence gap:
   {per-layer detail showing which layer(s) failed and why}

   **Recommended:** Skip — review the report and address gaps manually

   | Option | Description |
   |--------|-------------|
   | I | Investigate further — read referenced files, run additional searches |
   | F | Attempt fix — propose a specific fix (you must confirm before any change is applied) |
   | S | Skip — move to the next flagged item |

   You can reply with the option letter ("I", "F", or "S"), or say "done" to end the walkthrough early.
   ─────────────────────────────────────────────────
   ```

2. Wait for the user's reply before proceeding.
   - If the user replies `"I"` or `"investigate"`: read the referenced files, run additional grep searches, and output a detailed analysis of the evidence gap. Then re-display the options for the same item.
   - If the user replies `"F"` or `"fix"`: propose a specific, minimal fix. **Do not apply it.** Present the proposed change and ask: `Apply this fix? (y/n)`. Only apply on explicit `y` or `yes`.
   - If the user replies `"S"`, `"skip"`, `"s"`, or any acceptance variant: move to the next flagged item.
   - If the user replies `"done"`, `"stop"`, or `"exit"`: end the walkthrough immediately.
   - If the reply is ambiguous: ask for a quick disambiguation without advancing to the next item.
3. Never reveal future queued items in advance.
4. After all items are processed (or the user ends early), output:

   ```text
   ─────────────────────────────────────────────────
   ✅ Walkthrough complete. {n} of {total} flagged items addressed.
   Report: {FEATURE_DIR}/verify-tasks-report.md
   ─────────────────────────────────────────────────
   ```

---

### Historical Branch Verification Notes (User Story 3)

When running `/speckit.verify-tasks --scope branch` against a previously-completed feature branch, be aware of these edge cases:

**Deleted files**: Files that existed on the feature branch but were deleted in subsequent commits will not exist at the current working tree path. Layer 1 (File Existence) will return `negative`. Include a note in the flagged item detail: `Note: File may have been deleted in a subsequent commit. Consider using git show {ref}:{path} to verify original presence.`

**Plan-anchored scope**: Extract the plan creation date from `plan.md` using the `**Date**: {YYYY-MM-DD}` field. Use this as the `--since` anchor for `git log`. This captures all commits made during the implementation period. Example:

```sh
git log --since="2026-03-12" --name-only --pretty=""
```

**Usage example for historical branch**:

```sh
git checkout feature/001-verify-tasks-phantom
/speckit.verify-tasks --scope branch
```

This diffs `origin/main...HEAD` and checks only files modified on the feature branch, giving the most accurate picture of what was implemented during the feature's development.

---

### Error Conditions

Handle the following error and warning cases early, before or during verification:

| Condition | Behavior |
|-----------|----------|
| `tasks.md` not found in `FEATURE_DIR` | `ERROR: No tasks.md found in feature directory: {path}` — stop immediately |
| No `[X]` tasks found | `No completed tasks found to verify.` — clean exit, no report written |
| Malformed task entry (missing ID, broken checkbox) | `WARNING: Malformed task on line {n}: "{line}" — skipping` — continue with remaining tasks |
| `--scope plan-anchored` but no `plan.md` | `WARNING: plan.md not found — falling back to scope=all` |
| `--scope plan-anchored` but no date in `plan.md` | `WARNING: No date found in plan.md — falling back to scope=all` |
| Git unavailable (no `.git`, command not found) | `WARNING: Git unavailable — Layer 2 (Git Diff) skipped for all tasks.` — continue |
| Shallow clone | `WARNING: Shallow clone detected — Layer 2 diff coverage may be incomplete.` — continue |
| Task filter references non-existent ID | `WARNING: Task ID not found: {id} — skipping.` — verify remaining specified tasks |
| `verify-tasks-report.md` cannot be written | `ERROR: Cannot write report to {path}: {reason}` — output report to stdout instead |

---

<!--
## Cross-Agent Compatibility Checklist

This command uses ONLY the following capabilities. Verified available on all spec-kit supported agents:

### Shell Commands Used

| Command | Purpose | Available on |
|---------|---------|-------------|
| `bash .specify/scripts/bash/check-prerequisites.sh --json` | Feature directory discovery | Claude Code ✅, GitHub Copilot ✅, Gemini CLI ✅, Cursor ✅, Windsurf ✅ |
| `git rev-parse --git-dir` | Detect git repository | All agents with shell access ✅ |
| `git rev-parse --verify {ref}` | Check if git ref exists | All agents with shell access ✅ |
| `git rev-parse --is-shallow-repository` | Detect shallow clone | All agents with shell access ✅ |
| `git diff {ref}..HEAD --name-only` | Get changed files (branch scope) | All agents with shell access ✅ |
| `git diff HEAD --name-only` | Get uncommitted changes | All agents with shell access ✅ |
| `git log --since="{date}" --name-only --pretty=""` | Get commits since date | All agents with shell access ✅ |
| `git status --short` | Get working tree status | All agents with shell access ✅ |
| `git grep -n "{symbol}"` | Cross-repo symbol search | All agents with shell access ✅ |
| `grep -n "{pattern}" {file}` | Symbol search within file | All agents with shell access ✅ |
| `grep -rn "{symbol}" .` | Recursive symbol fallback | All agents with shell access ✅ |
| `find . -path "./{glob}" 2>/dev/null` | Glob expansion | All agents with shell access ✅ |
| `test -f {path}` / `test -d {path}` | File/dir existence check | All agents with shell access ✅ |

### Agent Native Capabilities

| Capability | Usage | Notes |
|-----------|-------|-------|
| Read file | Reading tasks.md, plan.md, spec.md, source files | Native to all agents |
| Write file | Writing verify-tasks-report.md | Native to all agents |
| Parse JSON | Parsing check-prerequisites.sh output | String parsing — no JSON library needed |

### Syntax Notes

- All shell commands use POSIX-compatible syntax (no bash-isms in the core logic)
- `grep` patterns use basic regex — no Perl-compatible regex (no `-P` flag)
- No `awk`, `sed`, or `jq` required — all parsing is via `grep` and `find`
- No agent-specific APIs used (no Claude-specific, no Copilot-specific features)
- File paths use forward slashes throughout (works on macOS, Linux, Windows WSL)

### Verified Agent Compatibility

- ✅ Claude Code — all features available
- ✅ GitHub Copilot (VS Code) — all features available via terminal tool
- ✅ Gemini CLI — all features available
- ✅ Cursor — all features available via terminal
- ✅ Windsurf — all features available via terminal
-->
