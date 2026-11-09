# Spec Delta

## Purpose

Define y estandariza los requisitos de verificación integral extremo a extremo (E2E), generación de evidencias de consola y auditoría de inmutabilidad, y empaquetado del entregable final sin artefactos temporales ni secretos expuestos.

## ADDED Requirements

### Requirement: E2E Test Suite and HTTP Cases Verification
The test suite SHALL provide 16 canonical test cases in HTTP REST client format covering all functional, transactional, and security scenarios C-01 through C-16 with expected response codes and structures documented in comments.

#### Scenario: Route parameter validation (C-01)
- **WHEN** an authenticated user calls a route expecting an integer path parameter with non-integer data
- **THEN** the system returns HTTP 422 Unprocessable Entity without executing the business handler.

#### Scenario: Registration and conflicts (C-02)
- **WHEN** registering with an existing user email or client email
- **THEN** the system returns HTTP 409 with a descriptive business error without persisting orphaned rows.

#### Scenario: Cookie based authentication (C-03)
- **WHEN** user authenticates successfully
- **THEN** the JWT token is delivered solely in an HttpOnly cookie and Bearer tokens are rejected on protected routes.

#### Scenario: Constant-time authentication error (C-04)
- **WHEN** authenticating with bad password or non-existent email
- **THEN** the system responds with 401 and uniform response time.

#### Scenario: Rate limiting protection (C-05)
- **WHEN** six consecutive login attempts fail from the same IP and email
- **THEN** the sixth returns HTTP 429 with Retry-After header and all five failures are recorded in database.

#### Scenario: Role authorization and data isolation (C-06)
- **WHEN** a client accesses another client sale or a vendor creates a book
- **THEN** the system returns HTTP 403 Forbidden.

#### Scenario: Immediate role revocation (C-07)
- **WHEN** an administrator revokes a role while the subject session is open
- **THEN** the next request with that session receives HTTP 403.

#### Scenario: Administrator self-protection (C-08)
- **WHEN** an administrator attempts to revoke their own ADMIN role
- **THEN** the system rejects the operation with HTTP 409.

#### Scenario: Mandatory password change interception (C-09)
- **WHEN** a user with mandatory password change accesses any route outside auth
- **THEN** the system returns HTTP 403 until the password is changed.

#### Scenario: Atomic sale execution (C-10)
- **WHEN** a valid sale with two items is processed
- **THEN** the system responds 201 with server-calculated total, discounts stock, inserts movements, and emits background voucher.

#### Scenario: Insufficient stock rollback (C-11)
- **WHEN** a sale requests more stock than available
- **THEN** the system returns HTTP 409 and executes full rollback leaving catalog stock untouched.

#### Scenario: Invalid book or client sale (C-12)
- **WHEN** a sale references a non-existent client, non-existent book, or soft-deleted book
- **THEN** the system returns HTTP 409 without persisting changes.

#### Scenario: Replenishment, soft delete, and ISBN reuse (C-13)
- **WHEN** an admin restocks, soft deletes, and creates a new book with the same ISBN
- **THEN** restock returns 200, delete returns 204, and re-registration returns 201.

#### Scenario: Pagination and search security (C-16)
- **WHEN** catalog is queried with SQL injection attempts, valid filters, or invalid pagination params
- **THEN** SQL injection yields empty items, filters return matched records, and invalid page/size returns 422.

### Requirement: Immutability Trigger psql Evidence (C-14)
The system SHALL provide verified console output in `c14_psql_output.txt` documenting execution of `solo_agregado.sql` in PostgreSQL rejecting UPDATE and DELETE on `movimiento_stock`.

#### Scenario: Trigger rejects modification
- **WHEN** an UPDATE or DELETE statement is executed against `movimiento_stock`
- **THEN** the trigger raises a fatal exception and rolls back the operation.

### Requirement: Eager Loading N+1 Prevention Evidence (C-15)
The system SHALL provide verified console output in `c15_consultas_n1_output.txt` demonstrating that `GET /ventas/{id}` executes a constant number of SQL queries regardless of item count.

#### Scenario: Constant SQL query count
- **WHEN** fetching details for a sale with 2 items and a sale with 4 items
- **THEN** both executions generate the exact same count of SQL statements in the server query log.

### Requirement: Clean Packaging and Zero-Secret Deliverable
The packaging script SHALL assemble `Parcial_Cap1a6_Grupo.zip` containing strictly `parcial/` and `despliegue/` directories while omitting all virtual environments, bytecodes, caches, and `.env` files.

#### Scenario: Packaging exclusions verified
- **WHEN** the archive is created and inspected
- **THEN** no `.env`, `.venv`, `__pycache__`, or `.pytest_cache` entries exist within the zip archive.
