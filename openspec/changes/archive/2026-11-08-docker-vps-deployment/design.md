# Design

## Context

Se requiere empaquetar el TP de la librería correspondiente a los capítulos 1 a 4 para su despliegue en el VPS de la cátedra mediante Docker, cumpliendo los ejercicios 9 y 10.
Ver `proposal.md` para la motivación.

## Goals / Non-Goals

**Goals:**
- Estructurar el código del TP Capítulos 1 a 4 en la carpeta `despliegue/`.
- Construir un `Dockerfile` sobre `python:3.12-alpine` con usuario no-root `appuser`, HEALTHCHECK sobre `127.0.0.1:8000/health/ready` y migraciones automáticas al arranque.
- Excluir secretos mediante `.dockerignore` y proveer `env.example`.
- Redactar `DEPLOY.md` con las instrucciones de build, ejecución con `--env-file`, `--add-host` y persistencia.
- Proveer los archivos de evidencia textual D-01 a D-08 en `despliegue/evidencia/`.

**Non-Goals:**
- Utilizar Docker Compose (el servidor ya cuenta con PostgreSQL nativo).
- Incluir en `despliegue/` las modificaciones de los capítulos 5 y 6 (usuarios, roles, cookies, trigger append-only, que corresponden exclusivamente a `parcial/`).

## Decisions

### Decisión 1: Aislamiento del TP en `despliegue/`
- **Elección**: La carpeta `despliegue/` contiene el código del TP de los capítulos 1 a 4 con su propio `main.py`, módulos de catálogo, clientes y ventas básicas, su `alembic.ini` y su migración inicial.
- **Razón**: La consigna especifica explícitamente que el empaquetado y despliegue en VPS se realiza sobre el TP entregado, sin los cambios agregados por el parcial (roles, cookies, UoW, trigger).

### Decisión 2: Dockerfile Alpine minimalista y sin privilegios
- **Elección**: Usar `python:3.12-alpine` (~74.7 MB base), crear el usuario sin privilegios `appuser` (UID 1000) y ejecutar con `USER appuser`. Instalar `requirements.txt` con `--no-cache-dir` antes de copiar el código fuente.
- **Razón**: Cumple estrictamente con el requisito de no exceder los 100 MB de imagen base y asegura la defensa en profundidad en el contenedor.

### Decisión 3: HEALTHCHECK con IP explícita 127.0.0.1
- **Elección**: Definir `HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 CMD wget -qO- http://127.0.0.1:8000/health/ready || exit 1`.
- **Razón**: En Alpine, `wget` resuelve `localhost` a `::1` (IPv6), lo cual falla con `Connection refused` frente a Uvicorn en `0.0.0.0:8000` (IPv4). El uso de `127.0.0.1` garantiza compatibilidad directa.

### Decisión 4: Arranque con migraciones condicionales
- **Elección**: `CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]`.
- **Razón**: Si la base de datos no está disponible o las credenciales fallan, Alembic aborta con código de error impidiendo que Uvicorn quede atendiendo en estado inconsistente.

## Risks / Trade-offs

- **[Riesgo de alcance a PostgreSQL del host en VPS Linux]**: Dentro de un contenedor Docker en Linux, `localhost` no es el servidor host.
  → *Mitigación*: Documentar el uso obligatorio del flag `--add-host=host.docker.internal:host-gateway` en el comando `docker run`.
