# Guía Operativa de Despliegue en VPS (Docker)

## 1. Datos Generales del Despliegue

- **URL Pública**: `http://187.41.125.146:8000` (Hostinger VPS `srv2136192.hstgr.cloud`)
- **Fecha y Hora de Puesta en Marcha**: 2026-11-08 19:30:00 UTC-3
- **Imagen Docker**: `libreria:latest` construida sobre base `python:3.12-alpine` (< 100 MB de base, ~74.7 MB)
- **Usuario de ejecución**: `appuser` (UID 1000, no-root)

---

## 2. Comandos de Construcción y Ejecución

### 2.1 Construcción de la Imagen
```bash
docker build -t libreria:latest .
```

### 2.2 Ejecución del Contenedor
```bash
docker run -d --name libreria \
  -p 8000:8000 \
  --restart unless-stopped \
  --add-host=host.docker.internal:host-gateway \
  --env-file /etc/libreria.env \
  libreria:latest
```

### Explicación de los Parámetros y Flags:
- `-p 8000:8000`: Publica exclusivamente el puerto de la aplicación asignado.
- `--restart unless-stopped`: Reinicia el contenedor automáticamente ante caídas o reinicios del servidor físico.
- `--add-host=host.docker.internal:host-gateway`: Permite que el contenedor alcance la base de datos PostgreSQL alojada en el host Linux del VPS sin usar `localhost`.
- `--env-file /etc/libreria.env`: Inyecta la variable `DATABASE_URL` y `SQL_ECHO=false` desde un archivo seguro fuera del repositorio y de la imagen Docker.

---

## 3. Correcciones Realizadas al TP para Ejecución en Contenedor

- **HEALTHCHECK en Alpine**:
  - En Alpine Linux, `wget` resuelve `localhost` a `::1` (IPv6), mientras que Uvicorn escucha en IPv4 (`0.0.0.0`). Una llamada a `http://localhost:8000/` fallaba con `Connection refused`.
  - Se configuró explícitamente `wget -qO- http://127.0.0.1:8000/health/ready` para asegurar verificación exitosa del estado `healthy`.

---

## 4. Estrategia de Actualización sin Pérdida de Datos

Para actualizar la aplicación cuando haya cambios en el código o en las migraciones:
1. Reconstruir la imagen con la nueva versión:
   ```bash
   docker build -t libreria:latest .
   ```
2. Eliminar el contenedor anterior:
   ```bash
   docker rm -f libreria
   ```
3. Volver a iniciar el contenedor:
   ```bash
   docker run -d --name libreria \
     -p 8000:8000 \
     --restart unless-stopped \
     --add-host=host.docker.internal:host-gateway \
     --env-file /etc/libreria.env \
     libreria:latest
   ```

**Garantía de Persistencia**:
Los datos de la librería nunca se pierden porque residen en el motor PostgreSQL del VPS y no en el contenedor efímero. Al iniciar, el contenedor ejecuta `alembic upgrade head`, aplicando sólo las migraciones nuevas sin repetir las existentes.

---

## 5. Registro de Evidencias de Despliegue (Casos D-01 a D-08)

Las evidencias completas de cada caso se encuentran en la carpeta `despliegue/evidencia/`:
- `d01_docker_images.txt`: Tamaño de imagen base `python:3.12-alpine` (< 100 MB) y tamaño de la imagen final del proyecto.
- `d02_docker_ps_healthy.txt`: Salida de `docker ps` mostrando `status: healthy` y `docker logs` con migraciones automáticas.
- `d03_external_requests.txt`: Respuestas a peticiones `GET /health/ready`, `GET /libros/` y `POST /ventas/`.
- `d04_container_recreation.txt`: Demostración de `docker rm -f libreria` y reinicio manteniendo datos y sin repetir migraciones.
- `d05_missing_database_url.txt`: Verificación de terminación controlada con error cuando falta `DATABASE_URL`.
- `d06_no_secrets_in_image.txt`: Inspección del filesystem (`ls -a /app`) y del entorno (`env`) confirmando ausencia de `.env` y secretos horneados.
- `d07_non_root_user.txt`: Salida de `id` en el contenedor confirmando usuario sin privilegios `appuser` (UID 1000).
- `d08_background_tasks_logs.txt`: Captura de `docker logs` mostrando el aviso de despacho del comprobante tras responder la petición.
