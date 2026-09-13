# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

## [1.1.0] - 2026-09-13

### Fixed

- Command body references to sibling commands use the agent-neutral `__SPECKIT_COMMAND_*__` token instead of a hard-coded `/speckit.…` spelling, so the rendered advisory is correct for every agent (dot, hyphen, or prefixed separators).
- Repository links in this changelog and the README pointed at the wrong GitHub organisation.
- [#4](https://github.com/datastone-inc/spec-kit-verify-tasks/issues/4) reported that spec-kit 0.4.3 rejected the two-part alias `speckit.verify-tasks` at install time. spec-kit 0.5.1 (2026-04-08) restored alias compatibility for community extensions, and the alias is kept: `/speckit.verify-tasks` and the canonical `/speckit.verify-tasks.run` are both installed. Installation of this release was verified against spec-kit 1.0.6, and `requires.speckit_version` now excludes the affected versions.

### Added

- **Step 3a test gate.** When the completed task list names a canonical test command (`make check`, `pytest`, `cargo test`, `npm test`, or a runner named in the repository's agent guidance) and the environment can run it, the command runs it once in the background and records the exit status and summary lines in the report header. A task whose only claim is "the suite is green" is then `✅ VERIFIED (by execution)` instead of `WEAK`. A run is never fabricated or improvised; when the check cannot run, the report says so.
- **Checkpoint line.** One progress line per `tasks.md` phase (or per ~10 tasks) during the verification cascade, so a long run is not silent.
- **Report immutability rule.** The walkthrough may only append the `## Walkthrough Log` section; it must never re-score a row in the original Flagged or Verified tables.

### Changed

- **Layer 4 no longer blanket-skips SQL.** Schema objects (tables, columns, types, views, indexes) still need no caller, but SQL functions, procedures and triggers are callable code and are checked for callers like any application symbol. When a symbol's legitimate caller lives in a sibling component or another language, Layer 4 searches the whole repository rather than the nearest project root, and includes the caller's language extensions in the grep. A spec or contract saying "component Y calls X" is a checkable assertion, not evidence.
- Minimum spec-kit version raised to 0.12.17, the release that resolves `__SPECKIT_COMMAND_*__` tokens in extension skills.

## [1.0.0] - 2026-03-12

### Added

- `/speckit.verify-tasks` slash command (`commands/speckit.verify-tasks.md`) — five-layer phantom completion detector
- **Layer 1**: File existence verification via `test -f` / `find`
- **Layer 2**: Git diff cross-reference supporting four scopes (`branch`, `uncommitted`, `plan-anchored`, `all`)
- **Layer 3**: Content pattern matching via `grep` for declared symbols
- **Layer 4**: Dead-code / wiring detection via `git grep` across the repository
- **Layer 5**: Semantic assessment with invariant — semantic evidence alone never yields `VERIFIED`
- Five verdict levels: `✅ VERIFIED`, `🔍 PARTIAL`, `⚠️ WEAK`, `❌ NOT_FOUND`, `⏭️ SKIPPED`
- Structured `verify-tasks-report.md` output: summary scorecard, flagged items with per-layer detail, verified items table, machine-parseable verdict lines
- Interactive walkthrough (Step 11) for flagged items with Investigate / Fix / Skip options
- Fresh-session advisory banner in both the command prompt and the generated report
- Historical branch verification notes for deleted-file and plan-anchored edge cases
- Graceful degradation when `git` is unavailable (layers 2 and 4 skipped)
- Shallow-clone warning
- Full error condition table (missing `tasks.md`, no `[X]` tasks, malformed entries, unwritable report path, etc.)
- Project constitution (`.specify/memory/constitution.md`) with eight governing principles
- Test fixtures:
  - `tests/fixtures/phantom-tasks/` — 10 tasks, 5 genuine + 5 planted phantoms (missing file, empty class, dead code, wrong function, behavioral gap)
  - `tests/fixtures/genuine-tasks/` — 10 tasks, all genuinely implemented with verified cross-references
  - `tests/fixtures/edge-cases/` — behavioral-only tasks, malformed entries, glob patterns, zero `[X]` tasks scenario
  - `tests/fixtures/scalability/` — 50-task synthetic fixture for session overflow testing (42 source files)
- `tests/expected-verdicts.md` — expected evidence level with rationale for every task in every fixture
- `.markdownlint.json` configuration

[Unreleased]: https://github.com/datastone-inc/spec-kit-verify-tasks/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/datastone-inc/spec-kit-verify-tasks/releases/tag/v1.1.0
[1.0.0]: https://github.com/datastone-inc/spec-kit-verify-tasks/releases/tag/v1.0.0
