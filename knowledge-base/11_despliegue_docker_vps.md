# Despliegue en VPS y Contenedorización

## Requisitos de la imagen Docker (Ejercicio 9)

- **Imagen base**: `python:3.12-alpine` (estrictamente por debajo de los 100 MB; ocupa ~74.7 MB).
- **Usuario sin privilegios**: La aplicación no corre como `root`. Se crea un usuario `appuser` y se activa con `USER appuser`.
- **Caché de capas**: Copiar e instalar `requirements.txt` con `--no-cache-dir` antes de copiar el código fuente.
- **Sin secretos horneados**: `.dockerignore` excluye `.env`, `.venv`, `.git` y `__pycache__`.
- **Arranque del contenedor**:
  1. Ejecuta migraciones automáticas con `alembic upgrade head`.
  2. Levanta Uvicorn escuchando en `0.0.0.0:8000`.
- **HEALTHCHECK**:
  - Configurado en `Dockerfile` apuntando a `GET http://127.0.0.1:8000/health/ready` usando `wget -qO-`.
  - Nota crítica: No usar `localhost` en Alpine porque resuelve a `::1` (IPv6) y Uvicorn escucha en IPv4 (`0.0.0.0`). Debe apuntar explícitamente a `127.0.0.1`.

## Ejecución del contenedor

```bash
docker run -d --name libreria -p <puerto>:8000 --restart unless-stopped \
  --add-host=host.docker.internal:host-gateway \
  --env-file <archivo-de-variables> libreria
```

- `--add-host=host.docker.internal:host-gateway`: Permite que el contenedor alcance a PostgreSQL si este corre directamente en el host Linux del VPS.

## Documentación y Evidencia (Ejercicio 10 y Casos D-01 a D-08)

El archivo `DEPLOY.md` dentro de `despliegue/` debe detallar:
- URL pública del despliegue.
- Fecha y hora exacta de puesta en marcha.
- Comandos completos de `docker build` y `docker run`.
- Procedimiento de actualización sin pérdida de datos.
- Carpeta `evidencia/` con la salida textual de cada caso:
  - `d01_docker_images.txt`: Tamaño de la imagen base y del proyecto.
  - `d02_docker_ps_healthy.txt`: Estado `healthy` y logs de migraciones.
  - `d03_external_requests.txt`: Respuestas a `/health/ready`, `/libros/` y `/ventas/`.
  - `d04_container_recreation.txt`: Eliminación y recreación del contenedor comprobando persistencia.
  - `d05_missing_database_url.txt`: Verificación de que el contenedor falla sin `DATABASE_URL`.
  - `d06_no_secrets_in_image.txt`: Inspección de variables y filesystem confirmando ausencia de `.env`.
  - `d07_non_root_user.txt`: Verificación de `id` no root.
  - `d08_background_tasks_logs.txt`: Log del comprobante de venta tras la respuesta HTTP.
