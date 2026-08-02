# ICT Chamber Kanban Backend

This repository contains the backend API for the ICT Chamber Kanban project management
platform. It is built with FastAPI and uses MongoDB for persistence, with a layered
architecture that separates API, application services, domain logic, and infrastructure
concerns. This document contains everything a frontend developer needs to build against the
API without reading the backend source.

## Features

## https://ictchamber-project-mgt-platform.onrender.com/docs#/

- User authentication (register/login) and JWT access/refresh token flow
- Board, column, and task management endpoints, each scoped to its owning user
- Domain-driven services with validation and ownership access guards
- MongoDB-backed repositories using Beanie
- Configurable settings via environment variables and a `.env` file

## Tech stack

- Python 3.11+
- FastAPI + Uvicorn
- Pydantic v2 / pydantic-settings
- Beanie (async MongoDB ODM) + MongoDB
- PyJWT (access/refresh tokens) + Argon2 (password hashing)
- Pytest (unit + integration tests)

## Project structure

- `src/app/api`: versioned API routers, request/response schemas, and dependency wiring
- `src/app/application`: service layer implementing business workflows and access guards
- `src/app/domain`: entities, value objects, repository interfaces, and domain exceptions
- `src/app/infrastructure`: Beanie document models and repository implementations
- `src/app/core`: settings, logging, database connection, security, and error handling
- `tests`: unit tests (mocked) and integration tests (real MongoDB + real HTTP)

## Running the backend locally

1. Create and activate a virtual environment

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. Install dependencies

   ```bash
   pip install -e ".[dev]"
   ```

3. Create a `.env` file in the project root (copy `.env.example`) with at least:

   ```bash
   APPLICATION_ENVIRONMENT_NAME=development
   MONGODB_CONNECTION_URI=mongodb://localhost:27017
   MONGODB_DATABASE_NAME=ictchamber
   JWT_SECRET_KEY=replace-with-a-long-random-secret
   JWT_ACCESS_TOKEN_EXPIRY_MINUTES=15
   JWT_REFRESH_TOKEN_EXPIRY_DAYS=7
   ALLOWED_CORS_ORIGINS=http://localhost:3000,http://localhost:5173
   ```

   `ALLOWED_CORS_ORIGINS` is a comma-separated list of origins allowed to call this API from a
   browser — it must include your frontend dev server's origin (see below).

4. Start the development server

   ```bash
   uvicorn app.main:fastapi_application_instance --reload
   ```

The API is now available at `http://127.0.0.1:8000`.

## Testing

Copy `.env.test.example` to `.env.test`, then run:

```bash
pytest
```

Integration tests connect to a real local MongoDB instance (no mocks) using a dedicated test
database that is cleaned between runs.

---

## Frontend integration guide

### Base URL and interactive docs

- Base URL: `http://127.0.0.1:8000` (or wherever `uvicorn` is bound in your environment)
- All application routes are versioned under `/api/v1`
- FastAPI auto-generates live, always-current API docs you can use instead of (or alongside)
  this reference:
  - Swagger UI (try requests in the browser): `http://127.0.0.1:8000/docs`
  - ReDoc: `http://127.0.0.1:8000/redoc`
  - Raw OpenAPI schema (importable into Postman/Insomnia/codegen tools):
    `http://127.0.0.1:8000/openapi.json`

### CORS

The backend only accepts browser requests from origins listed in the `ALLOWED_CORS_ORIGINS`
environment variable. If requests from your dev server are blocked, ask whoever runs the
backend to add your origin (e.g. `http://localhost:5173` for Vite, `http://localhost:3000` for
Next.js/CRA) to that list.

### Authentication flow

Every endpoint **except** `/api/v1/health`, `/api/v1/auth/register`, `/api/v1/auth/login`, and
`/api/v1/auth/refresh` requires a bearer access token on every request:

```http
Authorization: Bearer <access_token_value>
```

**1. Register** — `POST /api/v1/auth/register` (no auth required)

Request body (`UserRegistrationRequestSchema`):

```json
{
  "email_address": "user@example.com",
  "plain_text_password": "at-least-8-characters",
  "display_name": "Jane Doe"
}
```

- `email_address`: must be a valid email
- `plain_text_password`: 8–128 characters
- `display_name`: 1–100 characters

Response: `201 Created` with a `UserProfileResponseSchema` (see below).
Errors: `409 Conflict` if the email is already registered; `422` on validation failure.

**2. Log in** — `POST /api/v1/auth/login` (no auth required)

Request body (`UserLoginRequestSchema`):

```json
{ "email_address": "user@example.com", "plain_text_password": "at-least-8-characters" }
```

Response: `200 OK` with a `TokenPairResponseSchema`:

```json
{
  "access_token_value": "eyJ...",
  "refresh_token_value": "eyJ...",
  "token_type_name": "bearer"
}
```

Store both tokens client-side (choice of storage — memory, secure cookie, `localStorage` — is
up to the frontend's own security requirements). Attach `access_token_value` as a bearer token
on every subsequent request. Access tokens expire after `JWT_ACCESS_TOKEN_EXPIRY_MINUTES`
(default 15 minutes); refresh tokens expire after `JWT_REFRESH_TOKEN_EXPIRY_DAYS` (default 7
days). Error: `401 Unauthorized` on bad credentials.

**3. Refresh an expired access token** — `POST /api/v1/auth/refresh` (no auth required)

Request body (`TokenRefreshRequestSchema`):

```json
{ "refresh_token_value": "eyJ..." }
```

Response: `200 OK` with an `AccessTokenResponseSchema`:

```json
{ "access_token_value": "eyJ...", "token_type_name": "bearer" }
```

Recommended client pattern: on any `401` response, call `/auth/refresh` with the stored refresh
token, store the new access token, and retry the original request once. If the refresh itself
returns `401`, the refresh token has also expired — send the user back to login.

**4. Current user** — `GET /api/v1/auth/me` (auth required)

Returns the authenticated user's `UserProfileResponseSchema`. Call this on app load (with a
stored access token) to restore the session without asking the user to log in again.

`UserProfileResponseSchema`:

```json
{
  "user_identifier": "665f1b2c9e1a2b3c4d5e6f70",
  "email_address": "user@example.com",
  "display_name": "Jane Doe",
  "account_created_at": "2026-07-31T10:15:00Z",
  "is_account_active": true
}
```

### Data model and ownership rules

- All identifiers (`user_identifier`, `board_identifier`, `column_identifier`,
  `task_identifier`) are opaque MongoDB ObjectId strings. Treat them as opaque strings — never
  parse or construct them on the frontend.
- All timestamps (`created_at`, `updated_at`, `account_created_at`) are ISO 8601 UTC datetimes.
- Hierarchy: a **board** belongs to a user; a **column** belongs to a board; a **task** belongs
  to a column (and also carries a denormalized `parent_board_identifier` for convenience).
- Every resource is scoped to its owning user. Attempting to read/write another user's board
  (or a column/task under it) returns `403 Forbidden`, not `404` — this confirms the resource
  exists but is not yours.

### Resource endpoints

| Method | Path | Description | Request body | Success response |
| --- | --- | --- | --- | --- |
| POST | `/api/v1/boards` | Create a board | `BoardCreationRequestSchema` | `201` `BoardResponseSchema` |
| GET | `/api/v1/boards` | List your boards | – | `200` `BoardResponseSchema[]` |
| GET | `/api/v1/boards/{board_identifier}` | Get one board | – | `200` `BoardResponseSchema` |
| PUT | `/api/v1/boards/{board_identifier}` | Rename/describe a board | `BoardUpdateRequestSchema` | `200` `BoardResponseSchema` |
| DELETE | `/api/v1/boards/{board_identifier}` | Delete a board | – | `204 No Content` |
| POST | `/api/v1/boards/{board_identifier}/columns` | Add a column to a board | `ColumnCreationRequestSchema` | `201` `ColumnResponseSchema` |
| GET | `/api/v1/boards/{board_identifier}/columns` | List a board's columns | – | `200` `ColumnResponseSchema[]` |
| GET | `/api/v1/columns/{column_identifier}` | Get one column | – | `200` `ColumnResponseSchema` |
| PUT | `/api/v1/columns/{column_identifier}` | Rename a column | `ColumnUpdateRequestSchema` | `200` `ColumnResponseSchema` |
| DELETE | `/api/v1/columns/{column_identifier}` | Delete a column | – | `204 No Content` |
| POST | `/api/v1/columns/{column_identifier}/tasks` | Add a task to a column | `TaskCreationRequestSchema` | `201` `TaskResponseSchema` |
| GET | `/api/v1/columns/{column_identifier}/tasks` | List a column's tasks | – | `200` `TaskResponseSchema[]` |
| GET | `/api/v1/tasks/{task_identifier}` | Get one task | – | `200` `TaskResponseSchema` |
| PUT | `/api/v1/tasks/{task_identifier}` | Edit a task's title/description | `TaskUpdateRequestSchema` | `200` `TaskResponseSchema` |
| PATCH | `/api/v1/tasks/{task_identifier}/position` | Move/reorder a task | `TaskRepositionRequestSchema` | `200` `TaskResponseSchema` |
| DELETE | `/api/v1/tasks/{task_identifier}` | Delete a task | – | `204 No Content` |
| PUT | `/api/v1/boards/{board_identifier}/columns/reorder` | Reorder a board's columns | `ColumnReorderRequestSchema` | `200` `ColumnResponseSchema[]` |
| GET | `/api/v1/health` | Liveness check (no auth) | – | `200` `{"status": "healthy"}` |

Deleting a board cascades to its columns and tasks; deleting a column cascades to its tasks.

Lists are returned pre-sorted: columns by `column_display_order` ascending, tasks by
`task_position_value` ascending. New columns/tasks are appended after the current highest value
in their parent.

#### Drag-and-drop: reordering columns

`PUT /api/v1/boards/{board_identifier}/columns/reorder` persists a full new left-to-right order
for every column on the board in one call. `ColumnReorderRequestSchema`:

```json
{ "ordered_column_identifiers": ["665f...columnC", "665f...columnA", "665f...columnB"] }
```

The list must contain every column currently belonging to the board, each exactly once — after a
column drag-and-drop, send the client's full new column order. The response is the reordered
`ColumnResponseSchema[]` with `column_display_order` reassigned to match (`0, 1, 2, ...`).
Errors: `404` (`ColumnDoesNotBelongToBoardError`) if the list omits a column or references one that
isn't part of this board; `403` if the requester doesn't own the board.

#### Drag-and-drop: moving/reordering tasks

`PATCH /api/v1/tasks/{task_identifier}/position` moves a task to a new column and/or a new
position among its siblings — this covers both an in-column reorder and a cross-column move (the
same endpoint handles both). `TaskRepositionRequestSchema`:

```json
{
  "target_column_identifier": "665f...column",
  "previous_task_identifier": "665f...taskAbove",
  "next_task_identifier": "665f...taskBelow"
}
```

- `target_column_identifier`: the column the task should end up in (same as its current column for
  an in-column reorder, or a different one to move it across columns).
- `previous_task_identifier` / `next_task_identifier`: the identifiers of the tasks that should end
  up immediately before/after it in `target_column_identifier`, taken from the client's own reordered
  list. Either may be omitted (or `null`) to mean "top of the column" / "bottom of the column"; omit
  both to drop the task at the bottom.
- The task's new `task_position_value` is computed server-side (a value between its new neighbors);
  the response's updated `TaskResponseSchema` reflects it, and it need not be recomputed
  client-side.

Errors: `404` (`TaskNotFoundError`/`ColumnNotFoundError`) if the task or target column doesn't
exist; `404` (`InvalidReorderTargetError`) if `previous_task_identifier`/`next_task_identifier`
don't belong to `target_column_identifier` or aren't adjacent siblings there; `403` if the
requester doesn't own the task's board or the target column's board.

#### Schema field reference

`BoardCreationRequestSchema` / `BoardUpdateRequestSchema`:

| Field | Type | Constraints |
| --- | --- | --- |
| `board_title` | string | 1–200 characters, required |
| `board_description` | string \| null | optional, ≤2000 characters |

`BoardResponseSchema`:

```json
{
  "board_identifier": "665f...",
  "owning_user_identifier": "665f...",
  "board_title": "Sprint 12",
  "board_description": "Backend sprint board",
  "created_at": "2026-07-31T10:15:00Z",
  "updated_at": "2026-07-31T10:15:00Z"
}
```

`ColumnCreationRequestSchema` / `ColumnUpdateRequestSchema`:

| Field | Type | Constraints |
| --- | --- | --- |
| `column_title` | string | 1–200 characters, required |

`ColumnResponseSchema`:

```json
{
  "column_identifier": "665f...",
  "parent_board_identifier": "665f...",
  "column_title": "In Progress",
  "column_display_order": 2,
  "created_at": "2026-07-31T10:15:00Z",
  "updated_at": "2026-07-31T10:15:00Z"
}
```

`TaskCreationRequestSchema` / `TaskUpdateRequestSchema`:

| Field | Type | Constraints |
| --- | --- | --- |
| `task_title` | string | 1–200 characters, required |
| `task_description` | string \| null | optional, ≤4000 characters |

`TaskResponseSchema`:

```json
{
  "task_identifier": "665f...",
  "parent_column_identifier": "665f...",
  "parent_board_identifier": "665f...",
  "task_title": "Wire up login form",
  "task_description": "Use the /auth/login endpoint",
  "task_position_value": 100.0,
  "created_at": "2026-07-31T10:15:00Z",
  "updated_at": "2026-07-31T10:15:00Z"
}
```

### Error format

Every failed request (any 4xx/5xx) returns the same JSON shape, so the frontend can handle
errors generically in one place (e.g. an HTTP client interceptor):

```json
{
  "error_code": "BoardNotFoundError",
  "error_message": "Board with identifier '665f...' was not found.",
  "error_details": null
}
```

| Status | Meaning | Typical cause |
| --- | --- | --- |
| 401 | Unauthorized | Missing/invalid/expired bearer token, or bad login credentials |
| 403 | Forbidden | Authenticated, but not the owner of the requested resource |
| 404 | Not found | The resource does not exist |
| 409 | Conflict | e.g. registering an email that's already taken |
| 422 | Validation error | Request body failed validation; see `error_details.validation_errors` for field-level messages |
| 500 | Server error | Unexpected backend failure |

### Suggested frontend setup

- Configure your HTTP client (fetch/axios) with `baseURL` = the backend base URL above and
  inject the `Authorization` header from stored auth state.
- Add a response interceptor that, on `401`, attempts one `/auth/refresh` call and retries;
  on failure, clears auth state and redirects to login.
- Add a response interceptor/error boundary that reads `error_message` (and
  `error_details.validation_errors` when present) from the uniform error body for user-facing
  error messages.
- Treat all list endpoints as already sorted — no client-side sort is needed for column/task
  order today.
