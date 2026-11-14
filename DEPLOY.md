# DEPLOY — Despliegue en VPS con EasyPanel

## 1. Información general del despliegue
* **URL pública (HTTPS):** `https://lospythons-libreria-frontend.vruizu.easypanel.host`
* **Endpoint de salud público:** `https://lospythons-libreria-frontend.vruizu.easypanel.host/api/health/ready` (`200 OK` → `{"status":"ready"}`)
* **Repositorio Git:** `https://github.com/TekkNo0/BackendLib.git`
* **Rama:** `main`
* **Revisión desplegada (commit):** `ac5ab33` (`ac5ab33cb45f2d237a4fd90630e20c0bee82a135`)
* **Proyecto en EasyPanel:** `lospythons-libreria`

---

## 2. Arquitectura de servicios en EasyPanel

El proyecto cuenta con tres servicios en la misma red privada de EasyPanel:

1. **`db` (Servicio Postgres):**
   * Base de datos: `libreria`
   * Host interno: `lospythons-libreria_db`
   * Puerto interno privado: `5432` (sin exposición pública)

2. **`backend` (Servicio App — FastAPI):**
   * **Build Path:** `/backend`
   * **Builder:** `Dockerfile` (`backend/Dockerfile`)
   * **Puerto interno:** `8000` (`uvicorn app.main:app --host 0.0.0.0 --port 8000`)
   * **Dominio público:** eliminado (solo accesible por red interna como `lospythons-libreria_backend:8000`)

3. **`frontend` (Servicio App — Nginx):**
   * **Build Path:** `/frontend`
   * **Builder:** `Dockerfile` (`frontend/Dockerfile`, imagen base `nginx:1.30-alpine`)
   * **Dominio público:** `https://lospythons-libreria-frontend.vruizu.easypanel.host` → protocolo interno **HTTP**, puerto destino **80**

---

## 3. Configuración del Proxy Nginx (`frontend/default.conf.template`)

Nginx sirve los archivos estáticos desde `/usr/share/nginx/html` y reenvía todas las peticiones bajo `/api/` hacia el backend por la red interna:

```nginx
location / {
    try_files $uri $uri/ =404;
}

location /api/ {
    proxy_pass http://${API_UPSTREAM}/;
}
```

La barra final de `proxy_pass` reescribe `/api/libros/` → `/libros/` al llegar a FastAPI. La variable `API_UPSTREAM` se sustituye al iniciar el contenedor mediante `NGINX_ENVSUBST_FILTER=^API_UPSTREAM$`.

---

## 4. Variables de entorno (sin valores reales)

Ver archivo de referencia `backend/env.example`.

### Servicio `backend`
* `DATABASE_URL`: cadena de conexión asincrónica con formato `postgresql+asyncpg://<USUARIO>:<PASSWORD>@lospythons-libreria_db:5432/libreria` (sin parámetros `?sslmode=...` incompatibles con `asyncpg`).
* `SECRET_KEY`: clave secreta para firma de tokens JWT.

### Servicio `frontend`
* `API_UPSTREAM`: `lospythons-libreria_backend:8000`

---

## 5. Migraciones y carga inicial

* **Migraciones automáticas:** el `CMD` de `backend/Dockerfile` ejecuta `alembic upgrade head` antes de iniciar `uvicorn`, aplicando las revisiones:
  * `0001_initial_tp`
  * `0002_parcial_modelos`
  * `0003_trigger_solo_agregado`
  * `0004_libro_genero_nullable`
* **Carga inicial de datos ficticios:** ejecutada una vez desde la consola (**Shell**) del servicio `backend` en EasyPanel:
  ```sh
  python seed.py
  python -c "from urllib.request import urlopen; print(urlopen('http://127.0.0.1:8000/health/ready').status)"
  ```
  Salida observada: `200`.

---

## 6. Pasos para actualizar el despliegue

1. Realizar los cambios en local y subirlos a la rama `main` de GitHub (`git push origin main`).
2. En EasyPanel (`lospythons-libreria`), abrir el servicio modificado (`backend` o `frontend`) y pulsar **Deploy**.
3. Si hubo cambios de esquema en `backend/migrations/versions/`, verificar en **Logs** que `alembic upgrade head` se ejecutó correctamente antes de `Uvicorn running on http://0.0.0.0:8000`.
4. Comprobar en `https://lospythons-libreria-frontend.vruizu.easypanel.host/api/health/ready` que la respuesta sea `200 OK` y que los datos existentes persistan en PostgreSQL.
