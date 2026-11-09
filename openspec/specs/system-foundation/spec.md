# system-foundation Specification

## Purpose
Provides core system foundation, application lifecycle management, health check probes, generic asynchronous repository abstractions, unit of work context management, and standardized pagination contracts for the library API.

## Requirements

### Requirement: Configuration without hardcoded secrets
The system SHALL load application settings via pydantic-settings from environment variables, computing the postgresql+asyncpg connection URL dynamically, and SHALL reject startup if required credentials (POSTGRES_PASSWORD or SECRET_KEY) are missing.

#### Scenario: Missing required secret fails fast
- **WHEN** application starts without `POSTGRES_PASSWORD` or `SECRET_KEY` in environment
- **THEN** configuration validation raises an error and prevents server boot

#### Scenario: Computed async database URL
- **WHEN** valid PostgreSQL environment variables are provided
- **THEN** `DATABASE_URL` is constructed using `postgresql+asyncpg` driver scheme

### Requirement: Asynchronous database lifecycle in app state
The system SHALL initialize the async SQLAlchemy engine with configured pool sizes and session factory during application lifespan, storing them on `app.state`, and SHALL dispose the engine gracefully on shutdown.

#### Scenario: Engine and sessionmaker initialized in lifespan
- **WHEN** FastAPI application completes its startup lifespan phase
- **THEN** `app.state.engine` and `app.state.session_factory` are accessible, and sessions default to `expire_on_commit=False`

#### Scenario: Clean disposal on shutdown
- **WHEN** FastAPI application receives shutdown signal
- **THEN** `engine.dispose()` is awaited and all pooled database connections are closed

### Requirement: System health monitoring
The system SHALL expose `/health/live` and `/health/ready` endpoints to monitor process responsiveness and active database connectivity.

#### Scenario: Live probe succeeds without database query
- **WHEN** client issues `GET /health/live`
- **THEN** server returns status code 200 with `{"status": "live"}` without opening a database transaction

#### Scenario: Ready probe verifies database connectivity
- **WHEN** client issues `GET /health/ready` and PostgreSQL responds to `SELECT 1`
- **THEN** server returns status code 200 with `{"status": "ready"}`

#### Scenario: Ready probe responds with service unavailable when database fails
- **WHEN** client issues `GET /health/ready` and database connection is unreachable or drops
- **THEN** server returns status code 503 with service unavailable detail

### Requirement: Generic persistence repositories
The system SHALL provide `BaseRepository[T]` and `SoftDeleteRepository[T]` accepting an active AsyncSession and model class, executing `flush()` instead of `commit()`, and filtering soft-deleted records.

#### Scenario: Repository operations flush without commit
- **WHEN** `add()` or `update()` is invoked on a repository
- **THEN** pending changes are flushed to the active session without committing the transaction

#### Scenario: Soft delete repository filters deleted records
- **WHEN** `get_all()` or `get_by_id()` is called on a soft delete repository
- **THEN** records where `borrado_en` is not null are excluded unless `get_by_id_including_deleted()` is explicitly invoked

### Requirement: Atomic async unit of work context manager
The system SHALL provide an async context manager `UnitOfWork` base class that commits on clean block exit, rolls back on exception, and leaves session closing to the request lifecycle.

#### Scenario: Successful block commits transaction
- **WHEN** an async with block managed by UnitOfWork finishes without unhandled exceptions
- **THEN** transaction commit is executed on the session

#### Scenario: Exception inside block triggers rollback without closing session
- **WHEN** an exception occurs inside a UnitOfWork block
- **THEN** transaction rollback is executed on the session, the exception is re-raised, and the session remains open for request lifecycle teardown

### Requirement: Standardized pagination wrapper
The system SHALL structure paginated responses into `{items, total, page, size, pages}` envelope, validating that requested page does not exceed available pages.

#### Scenario: Valid page within range returns paginated payload
- **WHEN** client requests page 1 with size 20 and records exist
- **THEN** server responds with list of items, calculated total count, current page, size, and total pages

#### Scenario: Page number beyond total pages raises validation error
- **WHEN** client requests a page number greater than total pages
- **THEN** server responds with HTTP 422 Unprocessable Entity
