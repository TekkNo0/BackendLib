# Spec Delta

## ADDED Requirements

### Requirement: Append-only stock movement trigger
The system SHALL enforce database-level immutability on movimiento_stock via a PostgreSQL trigger that rejects all UPDATE and DELETE statements with an error.

#### Scenario: Attempted update rejected
- **WHEN** an UPDATE query is executed on an existing record in `movimiento_stock`
- **THEN** PostgreSQL raises an exception and aborts the transaction without altering any data

#### Scenario: Attempted delete rejected
- **WHEN** a DELETE query is executed on an existing record in `movimiento_stock`
- **THEN** PostgreSQL raises an exception and aborts the transaction without removing any data
