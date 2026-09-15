# Tasks: Phantom Completion Test Fixture

**Feature**: Phantom Detection Fixture
**Purpose**: Synthetic fixture with 12 completed tasks — 4 genuinely implemented, 6 planted phantom completions, and a convergence phase with one planted record gap and one planted code gap. Used to validate that `/speckit.verify-tasks` correctly flags phantoms while passing genuine completions, and tags each `PARTIAL` as `code` or `record`.

---

## Tasks

- [X] T001 Create user authentication module with `UserAuth` class in `tests/fixtures/phantom-tasks/src/auth.py`
- [X] T002 Implement `validate_token(token)` function in `tests/fixtures/phantom-tasks/src/auth.py` that checks JWT expiry and signature
- [X] T003 Add `DatabaseConnection` class to `tests/fixtures/phantom-tasks/src/db.py` with `connect()` and `disconnect()` methods
- [X] T004 Create `tests/fixtures/phantom-tasks/src/config.py` with `AppConfig` dataclass holding `host`, `port`, and `debug` fields
- [X] T005 Implement `send_notification(user_id, message)` function in `tests/fixtures/phantom-tasks/src/notifier.py`
- [X] T006 Add `CacheManager` class to `tests/fixtures/phantom-tasks/src/cache.py` with `get(key)` and `set(key, value)` methods
- [X] T007 Create `tests/fixtures/phantom-tasks/src/routes.py` with `register_routes(app)` function that wires all API endpoints
- [X] T008 Implement `parse_request_body(request)` helper in `tests/fixtures/phantom-tasks/src/utils.py`
- [X] T009 Add `LoggingMiddleware` class to `tests/fixtures/phantom-tasks/src/middleware.py` with `__call__` method
- [X] T010 Create `tests/fixtures/phantom-tasks/src/events.py` with `EventEmitter` class and `emit(event_name, data)` method

## Phase 2: Convergence

<!-- Appended in the shape /speckit.converge writes: "<desc> per <source-ref> (<gap-type>)". -->
<!-- T011: record gap — issue_token exists and is wired, but lives in src/auth.py, not the file the task names. -->
- [X] T011 Add `issue_token(user_id)` to `tests/fixtures/phantom-tasks/src/tokens.py` so callers can mint a session token per FR-002 (missing)
<!-- T012: code gap — register_routes is still a dead stub and main.py never calls it. -->
- [X] T012 Call `register_routes(app)` from `tests/fixtures/phantom-tasks/src/main.py` so all API endpoints are wired at startup per US1/AC2 (partial)
