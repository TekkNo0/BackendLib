# Proposal

## Why

Para cumplir con los ejercicios 9 y 10 del Parcial de la UTN, se debe empaquetar el TP de la librería (capítulos 1 a 4) en una imagen Docker optimizada basada en `python:3.12-alpine` (< 100 MB de base), ejecutar el contenedor en un VPS con usuario sin privilegios (`appuser`), aplicar migraciones automáticas al arrancar (`alembic upgrade head`), configurar el HEALTHCHECK sin errores de IPv6, desacoplar credenciales mediante `--env-file`, y generar el documento operativo `DEPLOY.md` junto con los archivos de evidencia para los casos D-01 a D-08.

## What Changes

- Estructura completa del proyecto TP en `despliegue/`:
  - Código fuente del TP capítulos 1 a 4 (`app/`, `alembic.ini`, `migrations/`, `requirements.txt`).
  - `Dockerfile` basado en `python:3.12-alpine`:
    - Creación de usuario no-root `appuser`.
    - Instalación de dependencias con `--no-cache-dir` antes de copiar el código para optimizar capas de caché.
    - HEALTHCHECK explícito con `wget -qO- http://127.0.0.1:8000/health/ready`.
    - Entrypoint de arranque que ejecuta `alembic upgrade head` y luego `uvicorn app.main:app --host 0.0.0.0 --port 8000`.
  - `.dockerignore`: exclusión estricta de `.env`, `.venv`, `.git`, `__pycache__`, `*.pyc` y `evidencia/`.
  - `env.example`: plantilla limpia de variables de entorno sin secretos reales.
  - `DEPLOY.md`: guía operativa con URL pública, comandos `docker build` y `docker run`, flags de red para Linux (`--add-host=host.docker.internal:host-gateway`), estrategia de actualización sin pérdida de datos, y registro de evidencias D-01 a D-08.
  - Carpeta `despliegue/evidencia/`: archivos de texto con los comandos y salidas de los casos D-01 a D-08.

## Capabilities

### New Capabilities
- `vps-deployment`: Empaquetado y puesta en línea en VPS del TP Capítulos 1 a 4 en contenedor Alpine no-root con migraciones al arranque, verificación de salud y sin secretos horneados.

### Modified Capabilities
<!-- None -->

## Impact

- Creación del proyecto aislado `despliegue/`.
- `despliegue/Dockerfile`, `despliegue/.dockerignore`, `despliegue/env.example`, `despliegue/DEPLOY.md`.
- Generación de evidencias D-01 a D-08 en `despliegue/evidencia/`.
- Tests automatizados en `test_deployment.py` para validar la sintaxis del Dockerfile, .dockerignore y variables de entorno.
