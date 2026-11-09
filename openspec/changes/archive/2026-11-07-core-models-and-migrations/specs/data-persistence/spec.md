# Spec Delta

## Purpose

Defines relational database models, table relationships, partial unique indexes, check constraints, and Alembic versioned schema migrations for security, catalog, client, and sales domains.

## ADDED Requirements

### Requirement: Relational schema representation in SQLModel
The system SHALL define table models using SQLModel for usuario, asignacion_rol, intento_acceso, evento_seguridad, editorial, genero, autor, libro_autor, libro, cliente, perfil_cliente, venta, renglon_venta, and movimiento_stock.

#### Scenario: Security and access entities declared
- **WHEN** security models are inspected
- **THEN** `usuario` contains email, nombre, password_hash, activo, and debe_cambiar_password; `asignacion_rol` references usuario_id with role check constraint ('ADMIN', 'VENDEDOR', 'CLIENTE'); and `evento_seguridad` records textual actor and accion

#### Scenario: Customer optional user linkage
- **WHEN** `cliente` model is inspected
- **THEN** `usuario_id` is a nullable foreign key with unique constraint, and `cliente.usuario` evaluates to a single scalar object or None rather than a list

#### Scenario: Catalog and soft-delete libro model
- **WHEN** `libro` model is inspected
- **THEN** it defines `borrado_en` as a nullable `timestamptz` column, numeric price with `CHECK precio > 0`, and integer stock with `CHECK stock >= 0`

### Requirement: Database integrity constraints and indexes
The system SHALL declare partial unique indexes with `postgresql_where` for ISBN among active books and for open role assignments, plus composite indexes on access attempts and explicit indexes on all foreign keys.

#### Scenario: Check constraint on numeric values
- **WHEN** invalid monetary or stock values are inserted into `libro`, `renglon_venta`, or `movimiento_stock`
- **THEN** database check constraints enforce `precio > 0`, `stock >= 0`, `cantidad > 0` for renglones, and `cantidad <> 0` for movimientos

#### Scenario: Partial unique index for active ISBN
- **WHEN** multiple books are recorded with the same ISBN
- **THEN** uniqueness is enforced only where `borrado_en IS NULL`, allowing a previously soft-deleted ISBN to be registered again

#### Scenario: Partial unique index for unrevoked roles
- **WHEN** assigning a role to a user
- **THEN** uniqueness is enforced for `(usuario_id, rol)` where `revocada_en IS NULL`, allowing historical revoked role records to persist

### Requirement: Schema evolution exclusively via Alembic
The system SHALL manage the database schema exclusively through versioned Alembic migrations with asyncpg support, prohibiting the use of `create_all()`.

#### Scenario: Schema creation without create_all
- **WHEN** bootstrapping a fresh database
- **THEN** schema is created by executing `alembic upgrade head`, ensuring migrations track the complete structural history

#### Scenario: Upgrade and downgrade reversibility
- **WHEN** `alembic downgrade base` followed by `alembic upgrade head` is executed
- **THEN** migrations revert cleanly to empty schema and rebuild all tables, foreign keys, and indexes without errors
