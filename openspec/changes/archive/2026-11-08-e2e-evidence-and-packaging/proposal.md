# Proposal

## Why

El parcial de Programación III exige la entrega final en formato ZIP con dos carpetas independientes (`parcial/` y `despliegue/`), demostrando la ejecución de los 16 casos de prueba del parcial (C-01 a C-16), archivos `.http` comentados con las respuestas esperadas, el script `solo_agregado.sql` para el trigger inmutable, evidencias de consola para C-14 y C-15 (N+1 resolution), documentación de despliegue y puesta en marcha en `README.md`, y empaquetado libre de archivos `.env`, directorios `.venv` y cachés `__pycache__`.

## What Changes

- **Suite de pruebas HTTP (C-01 a C-16)**: Creación y normalización de los 16 archivos `.http` canónicos en `parcial/test/` con comentarios detallados de respuesta HTTP esperada y sesión REST Client (`# @name`, `# @no-cookie-jar`, cabeceras `Cookie`).
- **Script SQL de trigger inmutable (C-14)**: Consolidación de `parcial/test/solo_agregado.sql` con inserción, prueba de UPDATE rechazada y prueba de DELETE rechazada con ROLLBACK/COMMIT explícito.
- **Evidencias de consola en `parcial/evidencia/`**:
  - `c14_psql_output.txt`: Transcripción de ejecución real en psql demostrando el rechazo de UPDATE y DELETE con el mensaje de error de la función PL/pgSQL.
  - `c15_consultas_n1_output.txt`: Captura de consola con `SQL_ECHO=True` demostrando que `GET /ventas/{id}` ejecuta un número fijo de consultas SQL tanto para una venta con 2 renglones como para una con 4 renglones (sin problema N+1 gracias a `selectinload`).
- **Documentación de puesta en marcha `parcial/README.md`**:
  - Nombres y datos del grupo.
  - Requisitos del sistema y arquitectura en capas.
  - Guía paso a paso desde cero: creación de virtualenv, instalación de dependencias, generación de clave de firma secreta para `.env`, aplicación de migraciones Alembic (`alembic upgrade head`), carga de datos semilla (`python seed.py`) y arranque de servidor Uvicorn.
  - Matriz de endpoints, roles requeridos y casos de prueba C-01 a C-16.
- **Script y procedimiento de empaquetado final**:
  - Script automatizado de empaquetado que genera `Parcial_Cap1a6_Grupo.zip`.
  - Validación estricta que garantiza que el ZIP contenga exclusivamente `parcial/` y `despliegue/`, excluyendo `.venv`, `__pycache__`, `*.pyc`, `.pytest_cache` y archivos `.env`.

## Capabilities

### New Capabilities
- `e2e-verification-and-packaging`: Define los contratos, evidencias y especificaciones de empaquetado final para los casos C-01 a C-16, generación de evidencia psql/N+1 y empaquetado limpio sin secretos ni artefactos transitorios.

### Modified Capabilities
None.

## Impact

- `parcial/test/`: Organización de los 16 archivos `caso_c01_*.http` a `caso_c16_*.http` y `solo_agregado.sql`.
- `parcial/evidencia/`: Creación de `c14_psql_output.txt` y `c15_consultas_n1_output.txt`.
- `parcial/README.md`: Nueva documentación integral del proyecto.
- Raíz del proyecto: Generación del archivo comprimido `Parcial_Cap1a6_Grupo.zip`.
