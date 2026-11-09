# Spec Delta

## Purpose

Enforces role-based authorization by querying active database roles on every request, administrator self-protection, route group isolation for mandatory password updates, and historical role lifecycle tracking.

## ADDED Requirements

### Requirement: Role verification against database
The system SHALL evaluate user permissions by querying currently active unrevoked and unexpired roles in `asignacion_rol` on every incoming request, treating token claims as informative only.

#### Scenario: Current active roles fetched from database
- **WHEN** user requests a protected endpoint requiring a specific role
- **THEN** server verifies that an active, unrevoked, unexpired role exists in the database before granting access

#### Scenario: Revoked role immediately denied access
- **WHEN** an administrator revokes a role for an active session
- **THEN** subsequent requests using the same session cookie immediately receive HTTP 403 Forbidden without waiting for token expiration

### Requirement: Administrator self protection
The system SHALL prevent an administrator from revoking their own ADMIN role and ensure at least one active ADMIN role remains in the system.

#### Scenario: Administrator cannot revoke own admin role
- **WHEN** an authenticated administrator attempts to revoke their own ADMIN role
- **THEN** server aborts the revocation and responds with HTTP 409 Conflict

#### Scenario: System prevents zero active administrators
- **WHEN** an administrator attempts to revoke the only remaining active ADMIN role in the system
- **THEN** server aborts the revocation and responds with HTTP 409 Conflict

### Requirement: Mandatory password change gate
The system SHALL isolate protected routes behind a dependency checking `debe_cambiar_password`, restricting users with pending updates to auth and public endpoints.

#### Scenario: User with pending password change blocked on protected routes
- **WHEN** user with `debe_cambiar_password == True` requests any route in the protected route group
- **THEN** server responds with HTTP 403 Forbidden

#### Scenario: User allowed on open routes
- **WHEN** user with `debe_cambiar_password == True` accesses auth endpoints or public catalog
- **THEN** server processes the request normally, allowing `/auth/cambiar-password`

### Requirement: Role assignment validation and historical persistence
The system SHALL validate expiration timestamps to be future dates with explicit timezones, and preserve revoked assignments without physical row deletion.

#### Scenario: Expiration in past or without timezone rejected with 422
- **WHEN** administrator assigns a role with an expiration in the past or lacking timezone offset
- **THEN** server rejects the payload with HTTP 422 Unprocessable Entity

#### Scenario: Reassigning expired role closes old record and opens new
- **WHEN** administrator assigns a role to a user who already had an expired or revoked assignment
- **THEN** previous assignment record remains preserved and a new open assignment is created

### Requirement: Security auditing on user modifications
The system SHALL persist an audit entry in `evento_seguridad` within the same transaction whenever staff is created, roles are assigned or revoked, or passwords are changed.

#### Scenario: Staff creation, role changes, and audits stored atomically
- **WHEN** staff is created or a role is updated
- **THEN** `evento_seguridad` entry is inserted and committed in the exact same Unit of Work block
