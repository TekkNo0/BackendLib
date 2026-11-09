# Tasks

## 1. Estructura del TP Capítulos 1 a 4 en `despliegue/`

- [x] 1.1 Estructurar en `despliegue/` la aplicación del TP (capítulos 1 a 4): `app/`, `requirements.txt`, `alembic.ini` y `migrations/versions/0001_initial_tp.py`.

## 2. Empaquetado Docker y Configuración Segura

- [x] 2.1 Crear `despliegue/Dockerfile` basado en `python:3.12-alpine` con usuario `appuser`, HEALTHCHECK a `127.0.0.1:8000/health/ready` y arranque con `alembic upgrade head && uvicorn`.
- [x] 2.2 Crear `despliegue/.dockerignore` y `despliegue/env.example` sin secretos horneados.

## 3. Guía Operativa y Registro de Evidencias D-01 a D-08

- [x] 3.1 Redactar `despliegue/DEPLOY.md` con los comandos de build, flags de ejecución (`--add-host`), estrategia de actualización y verificación de persistencia.
- [x] 3.2 Generar los archivos de evidencia `despliegue/evidencia/d01_docker_images.txt` a `d08_background_tasks_logs.txt`.
- [x] 3.3 Implementar pruebas automatizadas en `parcial/test/test_deployment.py` validando la configuración de Docker, usuario no root, exclusiones de .dockerignore y healthcheck.

## Workflow follow-up

- [x] Validar change con `openspec validate --strict`.
- [x] Archivar change con `openspec archive docker-vps-deployment -y`.
- [x] Actualizar `CHANGES.md`.
