# Global de Programación III — Librería Web Integrada

**Universidad Tecnológica Nacional (UTN) — Tecnicatura Universitaria en Programación**  
**Grupo:** Los Pythons  
**Integrantes:** Máximo Monardez, Joaquín Méndez, Facundo Chacón, Matías Ruiz, Thiago Oviedo, Tiago Guillot  
**Año lectivo:** 2026

---

## 1. Descripción del proyecto

Aplicación web integrada para la gestión de catálogo, altas de libros y clientes, registro de ventas e historial de la librería:

* **`frontend/`:** interfaz web en HTML5, CSS3 y JavaScript nativo (ES Modules, sin frameworks ni CDNs) servida mediante **Nginx 1.30 (Alpine)** con proxy inverso en `/api/` hacia el backend.
* **`backend/`:** API REST asincrónica construida con **FastAPI**, **SQLModel / SQLAlchemy 2.0 (Async)**, **Alembic** y **PostgreSQL**.

### Decisión documentada sobre selectores de autores y clientes
De acuerdo con el apartado *Consultas por ID* de la consigna:
* El backend expone tanto consultas individuales (`GET /autores/{id}`, `GET /clientes/{id}`) como listados paginados (`GET /autores/`, `GET /clientes/`).
* En el frontend se utilizan ambos mecanismos: los selectores principales cargan los listados (`GET /api/autores/` y `GET /api/clientes/`) y además se ofrecen campos de búsqueda/verificación directa por ID (`GET /api/autores/{id}` y `GET /api/clientes/{id}`).

---

## 2. Ejecución local paso a paso

### Requisitos previos
* Python 3.12+
* PostgreSQL 16+ corriendo localmente (con base de datos creada, por ejemplo `libreria`)
* Docker Desktop (para levantar el contenedor Nginx del frontend)

### Paso 1 · Levantar el Backend (`backend/`)
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item env.example .env
# Editar .env con los datos reales de tu PostgreSQL local (sin subir .env a Git)

alembic upgrade head
python seed.py
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Paso 2 · Carga de datos de prueba (`seed.py`)
El script `backend/seed.py` es idempotente y carga usuarios operadores, editoriales (`Sudamericana`, `Minotauro`, `Emecé`), géneros (`Novela`, `Cuento`, `Fantasía`), autores, 5 libros iniciales, 3 clientes ficticios y 1 venta de ejemplo. Si ya se ejecutó previamente, omite duplicar registros.

### Paso 3 · Construir y ejecutar el Frontend (`frontend/`)
En otra terminal (con Docker Desktop iniciado):
```powershell
cd frontend
docker build -t libreria-frontend .
docker run --rm --name libreria-frontend -p 127.0.0.1:8080:80 -e API_UPSTREAM=host.docker.internal:8000 libreria-frontend
```

### Paso 4 · Comprobar en el navegador
* Web: `http://127.0.0.1:8080/`
* Salud de la API a través del proxy: `http://127.0.0.1:8080/api/health/ready` (debe responder `200 OK` con `{"status":"ready"}`).

---

## 3. Casos de verificación ejecutados (`G-01` a `G-07`)

Todos los casos fueron ejecutados sobre la URL pública desplegada y su evidencia se encuentra en `evidencia/`:

| Caso | Descripción | Evidencia | Resultado |
| --- | --- | --- | --- |
| **G-01** | Catálogo: búsqueda sin coincidencias (`"minecraft"`) y detalle de libro con autores (`Rayuela`). | `evidencia/g01.png`, `evidencia/g01d.png` | Aprobado |
| **G-02** | Alta de libro (`Wigetta`, stock 1, género `Sin clasificar`, autoría) y rechazo `409` al repetir ISBN `1001`. | `evidencia/g02.png`, `evidencia/g02d.png` | Aprobado |
| **G-03** | Alta de cliente (`Julian Gonzales`, ID 4) y rechazo `409` al repetir email. | `evidencia/g03.png`, `evidencia/g03d.png` | Aprobado |
| **G-04** | Venta válida con 2 renglones (`Wigetta` + `Ficciones`, total `$37000.00`), recarga y apertura desde Historial. | `evidencia/g04.png`, `evidencia/g04d.png` | Aprobado |
| **G-05** | Cambio de precio con `PATCH /api/libros/6` a `$25000.00`; la venta `#2` conserva `$15000.00` y total `$37000.00`. | `evidencia/g05.png`, `evidencia/g05d.png` | Aprobado |
| **G-06** | Rechazos `409` (ID inexistente) y `422` (renglones repetidos); el historial conserva únicamente las ventas previas. | `evidencia/g06.png`, `evidencia/g06d.png` | Aprobado |
| **G-07** | Redespliegue en EasyPanel, salud HTTPS `200` en `/api/health/ready` y persistencia de datos en PostgreSQL. | `evidencia/g07.png`, `evidencia/g07d.png`, `evidencia/g07dd.png`, `evidencia/g07ddd.png` | Aprobado |
