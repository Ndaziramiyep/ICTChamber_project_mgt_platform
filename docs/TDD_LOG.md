# TDD Log

One dated entry per vertical slice, recording the red/green/refactor cycle at a slice level
(not per individual test). Commits driven by this workflow are additionally prefixed with
`test(red):`, `feat(green):`, or `refactor:` so `git log --oneline` doubles as a fine-grained log.

## 2026-07-30 — Project scaffolding

- Created `src/app` and `tests` package skeletons, `pyproject.toml` with dependency and tool
  configuration, `.pre-commit-config.yaml`, `.env`/`.env.test` files, and a Python 3.11 virtual
  environment (required because Beanie 2.x does not yet support Python 3.14, which is this
  machine's default interpreter).
- No production code yet — this entry precedes the first RED test.

## 2026-07-30 — Domain layer: task ordering value object

- RED: `tests/unit/domain/test_task_position_value.py` failed with `ModuleNotFoundError` (module
  did not exist yet).
- GREEN: implemented `calculate_position_between_neighbors`, `requires_position_rebalance`, and
  `generate_sequential_position_values` in `app/domain/value_objects/task_position_value.py`.
- Also added the framework-agnostic entities (`RegisteredUserEntity`, `ProjectBoardEntity`,
  `BoardColumnEntity`, `KanbanTaskEntity`), the repository Protocol interfaces, and the domain
  exception hierarchy (`DomainError` and its `ResourceNotFoundError` / `UnauthorizedAccessError` /
  `ResourceConflictError` / `AuthenticationError` subclasses) alongside the value object, since
  these are declarative and have no independent branching logic to drive through RED first.
- REFACTOR: none needed.

## 2026-07-30 — Authentication vertical slice

- RED: added unit tests for `hash_plain_text_password`/`verify_password_against_hash`,
  `SecurityTokenService`, `UserRegistrationService`, `UserAuthenticationService`, and
  `TokenRefreshService` against modules that did not yet exist (or, for the security wrappers,
  before their logic was written) — confirmed `ModuleNotFoundError` for the three application
  services before writing any implementation.
- GREEN: implemented `core/security_password_hashing.py` (Argon2id via `argon2-cffi`),
  `core/security_token_service.py` (PyJWT access/refresh tokens with a `token_type` claim), the
  three application services, `BeanieUserRepository`, the authentication API schemas, dependency
  providers, `current_user_dependency.get_current_authenticated_user`, and
  `authentication_router` (`/register`, `/login`, `/refresh`, `/me`).
- Added integration tests for `BeanieUserRepository` and the `/api/v1/auth/*` endpoints against
  the real local MongoDB test database — all passing.
- REFACTOR: discovered that pytest-asyncio's default per-test event loop conflicts with a
  session-scoped `AsyncMongoClient`; fixed by setting `asyncio_default_fixture_loop_scope` and
  `asyncio_default_test_loop_scope` to `"session"`. Also discovered that letting the API test
  client run the application's own startup/shutdown lifespan opened a second MongoDB client and
  closed it after each test, severing Beanie's document-model bindings for every later test;
  fixed by relying solely on the session-scoped `real_test_mongo_client` fixture for Beanie
  initialization in tests, and not invoking the application lifespan in `test_http_client`.
- 41 tests passing (unit + integration) at the end of this slice.

## 2026-07-30 — Boards vertical slice

- RED: `tests/unit/application/test_board_management_service.py` failed with `ModuleNotFoundError`.
- GREEN: implemented `BoardManagementService` (create/list/get/update/delete, all owner-checked
  through a shared `_find_board_and_ensure_ownership` guard), `BeanieBoardRepository`, board API
  schemas, dependency providers, and `board_router` (`POST/GET /boards`,
  `GET/PUT/DELETE /boards/{board_identifier}`).
- Added integration tests for `BeanieBoardRepository` and the `/api/v1/boards/*` endpoints,
  including an explicit two-user test proving a non-owner gets 403 on GET/PUT/DELETE for a board
  they do not own.
- Deliberately deferred: `DELETE /boards/{board_identifier}` currently deletes only the board
  record. Cascading deletion of its columns and tasks is tracked to be wired in once the column
  and task repositories exist (see the Tasks-slice entry below).
- REFACTOR: none needed.
- 61 tests passing (unit + integration) at the end of this slice.

## 2026-07-30 — Columns vertical slice

- REFACTOR (pre-emptive): extracted the board-ownership not-found/forbidden check out of
  `BoardManagementService` into a shared `application/services/board_access_guard.py` function,
  since `ColumnManagementService` needed the identical check and duplicating it across two
  services would violate SRP/DRY. Re-ran the full suite to confirm the boards slice still passed
  after the extraction before adding new code.
- RED: `tests/unit/application/test_column_management_service.py` failed with
  `ModuleNotFoundError`.
- GREEN: implemented `ColumnManagementService` (create appends at
  `max(existing_display_orders) + 1`; get/update/delete all resolve the column then reuse
  `find_board_and_ensure_ownership` against its `parent_board_identifier`), `BeanieColumnRepository`
  (with a compound index on `(parent_board_identifier, column_display_order)`), column API schemas,
  dependency providers, and `column_router` (`POST/GET /boards/{board_identifier}/columns`,
  `GET/PUT/DELETE /columns/{column_identifier}`).
- Added integration tests for `BeanieColumnRepository` (including ordering by display order) and
  the column HTTP endpoints, including an ownership-enforcement test proving a non-owning user
  gets 403 when listing columns for a board they do not own.
- Deliberately deferred: `DELETE /columns/{column_identifier}` currently deletes only the column
  record; cascading deletion of its tasks is tracked for the Tasks-slice follow-up, alongside the
  board cascade deferred in the previous entry.
- 79 tests passing (unit + integration) at the end of this slice.

## 2026-07-31 — Tasks vertical slice (CRUD only, reorder deferred)

- REFACTOR (pre-emptive): extracted `ColumnManagementService`'s column-not-found/board-ownership
  check into `application/services/column_access_guard.py`, mirroring the earlier
  `board_access_guard` extraction, since `TaskManagementService.create_task_in_column` needed the
  identical check. Re-ran the full suite (79 passing) before adding new code.
- RED: `tests/unit/application/test_task_management_service.py` failed with
  `ModuleNotFoundError`.
- GREEN: implemented `TaskManagementService` — `create_task_in_column` resolves the column via
  `find_column_and_ensure_board_ownership`, reads
  `find_highest_task_position_value_in_column`, and appends at
  `highest_existing_position + DEFAULT_POSITION_GAP` (or `DEFAULT_POSITION_GAP` for an empty
  column); get/update/delete resolve the task directly and reuse `find_board_and_ensure_ownership`
  against the task's denormalized `parent_board_identifier` (no need to traverse through the
  column). Implemented `BeanieTaskRepository`, task API schemas, dependency providers, and
  `task_router` (`POST/GET /columns/{column_identifier}/tasks`,
  `GET/PUT/DELETE /tasks/{task_identifier}`).
- Added integration tests for `BeanieTaskRepository` (ordering, highest-position lookup, column
  cascade delete at the repository level) and the task HTTP endpoints, including an ownership test
  proving a non-owner gets 403 listing tasks in a column they do not own, and a test asserting a
  created task carries its board's denormalized identifier correctly.
- 101 tests passing (unit + integration) at the end of this slice.

## 2026-08-02 — Drag-and-drop: column and task reordering, plus a deferred cascade fix

- Context: the frontend flagged that `GET /boards/{id}/columns` and each column's task list are
  always returned in creation order, so its drag-and-drop UI (`use-reorderable-columns.ts`,
  `use-board-task-order.ts`) could only reorder client-side and reset on reload — no endpoint
  persisted column order, task order, or a task's column.
- RED (pre-existing, found while reading the code this slice touches, not introduced by it):
  `tests/unit/application/test_column_management_service.py` was failing 9/9 on `main` —
  `ColumnManagementService.__init__()` did not accept the `task_repository` the test file's
  fixtures already constructed it with, so the "delete cascades to every task in the column" case
  (deferred back in the Columns-slice entry above) was never wired up. Fixed as GREEN alongside
  this slice since it's the same constructor/class being changed.
- GREEN: `ColumnManagementService` now takes `task_repository` and calls
  `delete_tasks_by_parent_column_identifier` before deleting the column. Added
  `reorder_columns_for_board`: validates the given identifier list is exactly the board's existing
  columns (each once), then persists `column_display_order = 0..N-1` in the requested sequence,
  raising `ColumnDoesNotBelongToBoardError` (404) on a mismatched list. Added
  `TaskManagementService.reposition_task_owned_by_authenticated_user`: resolves the moving task and
  the target column (both ownership-checked independently, so a cross-board move is rejected with
  403 rather than silently re-parenting a task into a board the requester doesn't own), locates the
  insertion point among the target column's existing tasks from `previous_task_identifier`/
  `next_task_identifier` (raising `InvalidReorderTargetError`, 404, if either doesn't belong to
  that column or they aren't adjacent), and either computes a single midpoint position via the
  existing `calculate_position_between_neighbors` value object (the common case — one write) or,
  when `requires_position_rebalance` trips, rewrites every sibling's position via
  `generate_sequential_position_values` (the rare case). Added `PUT
  /boards/{board_identifier}/columns/reorder` and `PATCH /tasks/{task_identifier}/position`, their
  request schemas, and wired `task_repository` into `provide_column_management_service`.
- Added unit tests covering both new service methods (ownership/not-found/invalid-target errors,
  top/bottom/midpoint placement, cross-column move, and the rebalance path) and integration tests
  proving both endpoints persist across a fresh `GET` (not just reflected in the response), plus
  the 403/404 authorization and validation boundaries end-to-end.
- REFACTOR: none needed.
- Updated `README.md`'s frontend integration guide to document both endpoints and drop the
  now-inaccurate "reordering endpoints do not exist yet" caveat.
- 125 tests passing (unit + integration) at the end of this slice.
