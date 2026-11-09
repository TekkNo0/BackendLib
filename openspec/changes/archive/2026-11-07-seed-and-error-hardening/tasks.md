# Tasks

## 1. Manejo Global de Excepciones y Ocultamiento de Internals (RN-01, RN-15)

- [x] 1.1 Implementar `parcial/app/core/exceptions.py` con manejadores para `IntegrityError`, `RequestValidationError` y `Exception`.
- [x] 1.2 Registrar los manejadores globales en `parcial/main.py`.

## 2. Script de Datos Iniciales (Seed Data)

- [x] 2.1 Implementar `parcial/seed.py` con inserción idempotente de usuarios requeridos, catálogo completo, clientes, Venta 1 histórica con movimientos de salida y auditoría inicial.

## 3. Pruebas Automatizadas

- [x] 3.1 Implementar suite de pruebas en `parcial/test/test_seed_and_hardening.py` validando la ejecución del seeder y la traducción de `IntegrityError` a HTTP 409 sin fuga de detalles internos.

## Workflow follow-up

- [x] Validar change con `openspec validate --strict`.
- [x] Archivar change con `openspec archive seed-and-error-hardening -y`.
- [x] Actualizar `CHANGES.md`.
