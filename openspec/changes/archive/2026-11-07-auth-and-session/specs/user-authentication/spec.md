# Spec Delta

## Purpose

Provides secure user authentication, HttpOnly cookie session management, bcrypt password hashing outside event loop, timing attack protection, database-backed rate limiting, and atomic self-registration.

## ADDED Requirements

### Requirement: Strict input validation on authentication contracts
The system SHALL validate all auth input contracts with `extra="forbid"` and reject passwords exceeding 72 UTF-8 bytes with HTTP 422.

#### Scenario: Unknown field is forbidden
- **WHEN** client sends a registration or login request containing undeclared fields (e.g., `rol` or `admin`)
- **THEN** server responds with HTTP 422 and rejects the payload

#### Scenario: Password exceeds 72 bytes triggers 422
- **WHEN** client submits a password whose UTF-8 encoded length exceeds 72 bytes
- **THEN** server responds with HTTP 422 Unprocessable Entity instead of raising an internal server error

### Requirement: Rate limiting on login attempts
The system SHALL evaluate prior failed attempts in `intento_acceso` and respond with HTTP 429 and `Retry-After` header when 5 failed attempts occur within 60 seconds.

#### Scenario: Rate limit exceeded returns 429 with retry header
- **WHEN** client makes a 6th login attempt after 5 consecutive failures for the same email and IP within 60 seconds
- **THEN** server immediately returns HTTP 429 with `Retry-After: 60` without computing bcrypt hash

#### Scenario: Successful login resets failed attempt count
- **WHEN** client completes a successful login
- **THEN** success is recorded in `intento_acceso` and subsequent failure counting only considers attempts after the success

### Requirement: Timing attack mitigation on login
The system SHALL return the exact same response and take comparable time whether the requested email exists or not.

#### Scenario: Nonexistent email runs dummy hash verification
- **WHEN** login is attempted with an email that does not exist in the database
- **THEN** password verification runs against the precomputed dummy hash from application lifespan and returns 401 "Credenciales incorrectas"

#### Scenario: Identical error response for nonexistent or wrong password
- **WHEN** login fails due to incorrect password or non-existent email
- **THEN** server returns HTTP 401 with identical response body `{"detail": "Credenciales incorrectas"}`

### Requirement: HttpOnly cookie session management
The system SHALL deliver signed JWT access tokens exclusively via `access_token` cookie configured with `HttpOnly`, `SameSite=Lax`, and `Max-Age`.

#### Scenario: Successful login sets HttpOnly cookie without token in body
- **WHEN** user provides valid credentials
- **THEN** server sets `access_token` in `Set-Cookie` header with HttpOnly and Lax attributes, and response body excludes the JWT string

#### Scenario: Logout clears access token cookie
- **WHEN** client calls `POST /auth/logout`
- **THEN** server clears `access_token` cookie with Max-Age=0 and returns HTTP 200

### Requirement: Atomic self-registration
The system SHALL create the user, their CLIENTE role assignment, and their customer profile in a single atomic Unit of Work.

#### Scenario: Successful registration creates user, role, and client record
- **WHEN** a new user registers via `POST /auth/registro`
- **THEN** `usuario`, `asignacion_rol` (with CLIENTE), and `cliente` are persisted atomically and server returns HTTP 201

#### Scenario: Existing email conflict returns 409 without orphan records
- **WHEN** registration email already exists in `usuario` or `cliente`
- **THEN** server returns HTTP 409 and rolls back all writes without creating orphan rows

### Requirement: Mandatory password change audit
The system SHALL require users with `debe_cambiar_password = True` to update their password, clearing the flag and auditing the event in the same transaction.

#### Scenario: Password change clears flag and records audit event
- **WHEN** user updates temporary password via `POST /auth/cambiar-password`
- **THEN** password hash is updated, `debe_cambiar_password` is set to False, and `evento_seguridad` record is persisted in the same transaction
