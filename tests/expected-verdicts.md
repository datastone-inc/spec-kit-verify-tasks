# Expected Verdicts: Test Fixture Validation Reference

**Date**: 2026-03-12
**Purpose**: Document the expected evidence level for every task in every test fixture. Use this to validate that `/speckit.verify-tasks` produces correct results when run against each fixture.

**Pass criteria**:

- Phantom fixture: ALL phantom verdicts must be `NOT_FOUND`, `PARTIAL`, or `WEAK`; all genuine tasks must be `VERIFIED`
- Genuine fixture: ALL tasks must produce `VERIFIED` (zero `NOT_FOUND`)
- Edge-case fixture: Warnings emitted for malformed/missing IDs; behavioral-only tasks produce `SKIPPED`

---

## Fixture 1: Phantom Tasks (`tests/fixtures/phantom-tasks/`)

This fixture contains 10 `[X]` tasks. 5 are genuinely implemented; 5 are planted phantoms.

### Phantom Type Key

- **PH-MISSING**: File does not exist
- **PH-EMPTY**: File exists but class/function body is incomplete
- **PH-DEAD**: Symbol declared but never referenced by any other file
- **PH-WRONGFN**: File exists but the required function is absent (different functions present)
- **PH-BEHAVIORAL**: Class exists but a required method is absent

### Expected Verdicts

| Task | Expected Verdict | Phantom Type | Rationale |
|------|-----------------|--------------|-----------|
| T001 | ✅ VERIFIED | — | `tests/fixtures/phantom-tasks/src/auth.py` exists; `UserAuth` class defined with all methods; imported and used by `tests/fixtures/phantom-tasks/src/main.py` (Layer 4 ✅ wired) |
| T002 | ✅ VERIFIED | — | `validate_token` function fully implemented in `tests/fixtures/phantom-tasks/src/auth.py`; called by `tests/fixtures/phantom-tasks/src/main.py` (Layer 4 ✅ wired) |
| T003 | ✅ VERIFIED | — | `tests/fixtures/phantom-tasks/src/db.py` exists; `DatabaseConnection` class with `connect()` and `disconnect()` present; imported and used by `tests/fixtures/phantom-tasks/src/main.py` (Layer 4 ✅ wired) |
| T004 | ✅ VERIFIED | — | `tests/fixtures/phantom-tasks/src/config.py` exists; `AppConfig` dataclass with `host`, `port`, `debug` fields present; imported and used by `tests/fixtures/phantom-tasks/src/main.py` (Layer 4 ✅ wired) |
| T005 | ❌ NOT_FOUND | **PH-MISSING** | `tests/fixtures/phantom-tasks/src/notifier.py` does not exist — Layer 1 (file existence) fails; no evidence in any layer |
| T006 | 🔍 PARTIAL | **PH-EMPTY** | `tests/fixtures/phantom-tasks/src/cache.py` exists (Layer 1 ✅); `CacheManager` is declared (Layer 3 ✅); but `get()` and `set()` methods are absent (Layer 3 ❌ for method patterns); dead-code check skips (class body empty) |
| T007 | 🔍 PARTIAL | **PH-DEAD** | `tests/fixtures/phantom-tasks/src/routes.py` exists (Layer 1 ✅); `register_routes` function declared (Layer 3 ✅); but no other file imports or calls it (Layer 4 ❌ dead code) |
| T008 | 🔍 PARTIAL | **PH-WRONGFN** | `tests/fixtures/phantom-tasks/src/utils.py` exists (Layer 1 ✅); but `parse_request_body` is not present — only unrelated functions `format_date` and `slugify` exist (Layer 3 ❌); at least one layer positive + at least one negative → PARTIAL |
| T009 | 🔍 PARTIAL | **PH-BEHAVIORAL** | `tests/fixtures/phantom-tasks/src/middleware.py` exists (Layer 1 ✅); `LoggingMiddleware` class declared (Layer 3 ✅); but `__call__` method is absent (Layer 3 ❌ for `__call__` pattern) |
| T010 | ❌ NOT_FOUND | **PH-MISSING** | `tests/fixtures/phantom-tasks/src/events.py` does not exist — Layer 1 fails; no evidence in any layer |

### Summary Scorecard (Expected)

| Verdict | Count |
|---------|-------|
| ✅ VERIFIED | 4 |
| 🔍 PARTIAL | 4 |
| ⚠️ WEAK | 0 |
| ❌ NOT_FOUND | 2 |
| ⏭️ SKIPPED | 0 |

---

## Fixture 2: Genuine Tasks (`tests/fixtures/genuine-tasks/`)

All 10 tasks are genuinely implemented. Zero `NOT_FOUND` verdicts expected.

### Expected Verdicts

| Task | Expected Verdict | Rationale |
|------|-----------------|-----------|
| T001 | ✅ VERIFIED | `tests/fixtures/genuine-tasks/src/calculator.py` exists; `Calculator` class with `add()` and `subtract()` present; referenced by `runner.py` and `app.py` |
| T002 | ✅ VERIFIED | `multiply()` and `divide()` present in `Calculator`; both called via `runner.py` and `app.py` |
| T003 | ✅ VERIFIED | `tests/fixtures/genuine-tasks/src/validator.py` exists; `validate_email` function present and imported by `pipeline.py` |
| T004 | ✅ VERIFIED | `validate_phone` function present in `tests/fixtures/genuine-tasks/src/validator.py` |
| T005 | ✅ VERIFIED | `tests/fixtures/genuine-tasks/src/formatter.py` exists; `format_currency` present and imported by `pipeline.py` and `app.py` |
| T006 | ✅ VERIFIED | `format_date` present in `tests/fixtures/genuine-tasks/src/formatter.py` |
| T007 | ✅ VERIFIED | `tests/fixtures/genuine-tasks/src/storage.py` exists; `FileStore` class with `save()` and `load()` present; imported by `app.py` |
| T008 | ✅ VERIFIED | `tests/fixtures/genuine-tasks/src/runner.py` exists; imports `Calculator` and calls `add`, `subtract`, `multiply`, `divide` |
| T009 | ✅ VERIFIED | `tests/fixtures/genuine-tasks/src/pipeline.py` exists; `Pipeline` class with `process()` method that calls `validate_email` and `format_currency`; imported by `app.py` |
| T010 | ✅ VERIFIED | `tests/fixtures/genuine-tasks/src/app.py` exists; imports and uses `FileStore`, `Pipeline`, and `Calculator` |

### Summary Scorecard (Expected)

| Verdict | Count |
|---------|-------|
| ✅ VERIFIED | 10 |
| 🔍 PARTIAL | 0 |
| ⚠️ WEAK | 0 |
| ❌ NOT_FOUND | 0 |
| ⏭️ SKIPPED | 0 |

---

## Fixture 3: Edge Cases (`tests/fixtures/edge-cases/`)

This fixture tests unusual and boundary inputs. Not all entries are valid `[X]` tasks.

### Expected Behaviors

| Entry | Expected Verdict | Expected Warning/Behavior | Rationale |
|-------|-----------------|--------------------------|-----------|
| EC001 | ⏭️ SKIPPED | None | Behavioral-only task (no file paths, no code references) — all mechanical layers N/A; semantic assessment cannot confirm or deny without referenced files |
| EC002 | *(not verified)* | None — task is `[ ]` (incomplete) | Task checkbox is `[ ]` not `[X]` — should not appear in the verified task list |
| EC003 (no ID) | ⚠️ WEAK or ⏭️ SKIPPED | `WARNING: No task ID found on line {n}` | Missing task ID — ID synthesized as `LINE-{n}`; no file paths in the description so likely SKIPPED |
| EC004 | ❌ NOT_FOUND or ⏭️ SKIPPED | None | Glob path `tests/fixtures/edge-cases/tests/**/*.test.py` — no matching files exist; Layer 1 returns `not_applicable` or `negative` depending on glob behavior |
| EC005 | ⏭️ SKIPPED | None | Parent task has no direct file references — SKIPPED |
| EC005.1 | ❌ NOT_FOUND | None | `tests/fixtures/edge-cases/.github/workflows/ci.yml` referenced but does not exist |
| EC005.2 | ❌ NOT_FOUND | None | `ci.yml` referenced but does not exist; `flake8` pattern not found |
| EC006 | *(not verified)* | None — task is `[ ]` | Incomplete task, not in the verification set |
| EC007 | ⏭️ SKIPPED | None | No file paths or code references — pure review/approval task; all mechanical layers N/A |
| EC008 | ❌ NOT_FOUND | None | `tests/fixtures/edge-cases/src/auth.py`, `tests/fixtures/edge-cases/src/db.py`, `tests/fixtures/edge-cases/src/base.py` do not exist; file existence fails |

### Expected Warnings Emitted

1. `WARNING: No task ID found on line {n}: "- [X] Implement the database migration runner..."` — for EC003
2. No other warnings expected (EC002, EC006 are `[ ]` tasks and correctly excluded)

### Summary Scorecard (Expected, for [X] tasks only)

| Verdict | Count |
|---------|-------|
| ✅ VERIFIED | 0 |
| 🔍 PARTIAL | 0 |
| ⚠️ WEAK | 0 |
| ❌ NOT_FOUND | 4 |
| ⏭️ SKIPPED | 4 |

*(EC003 may be WEAK or SKIPPED depending on synthetic ID handling; EC004 may be NOT_FOUND or SKIPPED depending on glob expansion behavior.)*

---

## Validation Instructions

### How to Run Validation

1. Commit any in-progress work so you can cleanly revert test changes
2. Copy a fixture's `tasks.md` over the feature spec's `tasks.md`:
   ```bash
   cp tests/fixtures/phantom-tasks/tasks.md specs/001-verify-tasks-phantom/tasks.md
   ```
3. Run `/speckit.verify-tasks` (no fresh session needed — there is no implementation context to bias results)
4. Compare the generated `verify-tasks-report.md` against the expected verdicts above
5. Revert all test changes:
   ```bash
   git checkout .
   ```

### Pass/Fail Criteria

| Fixture | Pass Condition |
|---------|---------------|
| **phantom-tasks** | T005, T010 are `NOT_FOUND`; T006, T007, T008, T009 are `PARTIAL`; T001–T004 are `VERIFIED` |
| **genuine-tasks** | All 10 tasks are `VERIFIED`; zero `NOT_FOUND` verdicts |
| **edge-cases** | EC001, EC005, EC007 are `SKIPPED`; EC005.1, EC005.2, EC008 are `NOT_FOUND`; `WARNING` emitted for EC003 missing ID |
