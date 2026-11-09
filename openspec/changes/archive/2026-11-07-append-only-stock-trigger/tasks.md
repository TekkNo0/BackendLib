# Tasks

## 1. Migración Manual de Disparador

- [x] 1.1 Crear migración `parcial/migrations/versions/0003_trigger_solo_agregado.py` con la función PL/pgSQL y el trigger `BEFORE UPDATE OR DELETE`, incluyendo comentario explicativo obligatorio.

## 2. Script de Prueba C-14 y Tests

- [x] 2.1 Crear `parcial/test/solo_agregado.sql` para el Caso C-14 conteniendo INSERT, UPDATE rechazado, DELETE rechazado y SELECT de verificación.
- [x] 2.2 Implementar prueba en `parcial/test/test_trigger.py` verificando el contenido de la migración y la reversibilidad en downgrade.

## Workflow follow-up

- Validar change con `openspec validate --strict`.
- Archivar change con `openspec archive append-only-stock-trigger -y`.
- Actualizar `CHANGES.md`.
