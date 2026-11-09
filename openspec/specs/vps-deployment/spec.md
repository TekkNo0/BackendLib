# vps-deployment Specification

## Purpose
Define el empaquetado Docker del TP Capítulos 1 a 4 con imagen Alpine minimalista, usuario sin privilegios, migración al arranque, verificación de salud y documentación operativa para el VPS.

## Requirements

### Requirement: Imagen Docker Alpine minimalista y segura
El sistema SHALL proveer un Dockerfile basado en `python:3.12-alpine` (menor a 100 MB de base), ejecutando bajo un usuario sin privilegios `appuser` (no root), instalando dependencias con `--no-cache-dir` y garantizando la ausencia de secretos horneados mediante `.dockerignore`.

#### Scenario: Base Alpine menor a 100MB
- **WHEN** se construye o inspecciona la imagen base `python:3.12-alpine`
- **THEN** su tamaño en disco se mantiene por debajo de 100 MB (~74.7 MB)

#### Scenario: Ejecución bajo usuario no root
- **WHEN** se ejecuta el contenedor o se inspecciona con `id`
- **THEN** el identificador de usuario `uid` y `gid` es distinto de 0 correspondiente a `appuser`

#### Scenario: Ausencia de secretos y archivos de entorno en la imagen
- **WHEN** se inspecciona el sistema de archivos de la imagen construida
- **THEN** no existen archivos `.env`, `.venv`, `.git` ni cadenas de credenciales grabadas en las capas

### Requirement: Ciclo de vida y verificación de salud del contenedor
El sistema SHALL ejecutar `alembic upgrade head` al arrancar antes de iniciar Uvicorn y proveer un HEALTHCHECK mediante `wget -qO- http://127.0.0.1:8000/health/ready` evitando fallos de IPv6 en Alpine.

#### Scenario: Migraciones al arranque y verificación healthy
- **WHEN** el contenedor inicia conectado a la base de datos
- **THEN** aplica las migraciones pendientes y el estado del contenedor pasa a `healthy`

#### Scenario: Terminación controlada ante base de datos inaccesible
- **WHEN** el contenedor inicia sin variables de entorno válidas o con base caída
- **THEN** el comando de migraciones falla de inmediato y el contenedor se detiene con código de error

### Requirement: Guía de despliegue y evidencia operativa
El sistema SHALL incluir el archivo `DEPLOY.md` con la URL pública, comandos de construcción y ejecución con `--env-file`, estrategia de actualización sin pérdida de datos, y los registros de evidencia para los casos D-01 a D-08 en `despliegue/evidencia/`.

#### Scenario: Documentación de comandos de build y ejecución en VPS
- **WHEN** un operador consulta `DEPLOY.md`
- **THEN** encuentra los comandos exactos de `docker build` y `docker run` con flag `--add-host=host.docker.internal:host-gateway`

#### Scenario: Registro completo de evidencias D-01 a D-08
- **WHEN** se revisa la carpeta `despliegue/evidencia/`
- **THEN** se encuentran disponibles los archivos `d01_docker_images.txt` hasta `d08_background_tasks_logs.txt` con sus salidas documentadas
