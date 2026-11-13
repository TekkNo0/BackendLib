# SPEC — Frontend de Librería integrado con FastAPI (Global Programación III)

## 1. Problema, objetivo y resultado esperado
El frontend original del Parcial 1 fue eliminado. Se requiere reconstruir la interfaz web de la librería con **HTML, CSS y JavaScript nativos** dentro de `frontend/public/`, respetando la estructura de vistas, semántica, accesibilidad y diseño adaptable del **Parcial 1**, pero conectada directamente a la **API de FastAPI + PostgreSQL** (`backend/`) bajo el prefijo `/api` según los contratos del **Global de Programación III** (en lugar de simular datos en `localStorage`).

**Resultado esperado:** Una aplicación web de una sola entrada (`frontend/public/index.html`) con estilos y scripts locales (`css/`, `js/`), lista para servirse con Nginx y conectarse a `backend/` mediante `/api/...`.

---

## 2. Contexto verificado y referencias
- **Repositorio de trabajo:** `C:\Users\maxim\Documents\Facu\Prog2026\ParcialProg\`
- **Backend verificado (`backend/`):**
  - `GET /health/ready` → `{ "status": "ready" }`
  - `GET /libros/` (`titulo`, `limit`, `offset`) → `PaginatedResponse[LibroDetalleResponse]` (`items`, `total`, `limit`, `offset`)
  - `GET /libros/{id}` → `LibroDetalleResponse` (incluye `editorial`, `genero`, `autores` con `rol` y `orden`)
  - `POST /libros/` → body `{ isbn, titulo, precio, stock_inicial, editorial_id, genero_id (opcional), autores: [{ autor_id, rol, orden }] }` → `201`
  - `PATCH /libros/{id}` → `{ titulo?, precio? }` → `200`
  - `GET /editoriales/` → `PaginatedResponse[EditorialResponse]`
  - `GET /generos/` → `PaginatedResponse[GeneroResponse]`
  - `GET /autores/` y `GET /autores/{id}` → listado y detalle de autores
  - `GET /clientes/`, `GET /clientes/{id}`, `POST /clientes/` (`{ nombre, email }`) → `201` / `409`
  - `GET /ventas/` (`limit`, `offset`), `GET /ventas/{id}`, `POST /ventas/` (`{ cliente_id, renglones: [{ libro_id, cantidad }] }`) → `201` / `409` / `422`
- **Fuentes de requisitos:**
  - *Global de Programación III — Librería web integrada y desplegada en Easypanel* (Ejercicios 1, 2, 3 y casos `G-01` a `G-06`).
  - *Parcial 1: frontend de una librería* (Ejercicios 1 y 2: estructura HTML semántica, CSS adaptable 320 px / 1280 px y accesibilidad).

---

## 3. Alcance incluido y exclusiones explícitas

### Incluido
- **5 vistas navegables** desde `index.html`:
  1. **Catálogo:** buscador por título (case-insensitive, parcial, `trim()`), paginación (`limit` y `offset`, reiniciando `offset` al cambiar filtro), listado con título, ISBN, precio, editorial y género (`«Sin clasificar»` si es `null`), y consulta de detalle (`GET /libros/{id}`) para ver autores (nombre, rol y orden).
  2. **Libros (Alta y listado):** formulario `POST /libros/` con título, ISBN, precio (`> 0`), stock entero (`>= 0`), selector de editorial (`GET /editoriales/`), selector de género opcional con `«Sin clasificar»` (`GET /generos/`), y selector/agregador de autores (verificando por `GET /autores/{id}` o selector de `GET /autores/`, con `rol` [`autor`, `coautor`, `traductor`, `ilustrador`] y `orden`).
  3. **Clientes (Alta y listado):** formulario `POST /clientes/` con `nombre` y `email`, listado y búsqueda/selección por ID (`GET /clientes/{id}` y `GET /clientes/`).
  4. **Ventas (Nueva venta):** selección de cliente, agregado de libros del catálogo, edición de cantidades, eliminación de renglones, borrador en memoria, validaciones (al menos 1 renglón, cantidad entera positiva, un solo renglón por libro), envío `POST /ventas/` con botón deshabilitado durante la petición, y visualización de precios unitarios, subtotales y total devueltos por la API.
  5. **Historial:** listado paginado (`GET /ventas/` con `limit` y `offset`) y apertura de detalle (`GET /ventas/{id}`) mostrando fecha, cliente, renglones e importes históricos.
- **Cliente HTTP centralizado** en `js/api.js` con base `/api`, preservando barras finales en rutas que las llevan.
- **CSS propio externo** (`css/styles.css`) con Flexbox/Grid, adaptable a `320 px` y `1280 px`, sin scroll horizontal de página, foco visible para teclado y tablas con scroll propio.

### Excluido
- Frameworks, librerías externas o CDNs de CSS/JS (todo nativo y local).
- Simulación en `localStorage` (se reemplaza por la API real; solo el borrador de venta en curso vive en memoria).
- Pantalla de login o gestión de usuarios/roles (el backend ya opera con `get_operador_global`).
- Edición/borrado de clientes, ventas o editoriales/géneros/autores desde el frontend.
- Dockerfile/Nginx del frontend (corresponde a la Fase 3 del roadmap, fuera de esta especificación de UI).

---

## 4. Requisitos identificados y escenarios observables

| ID | Grupo | Requisito verificable |
| --- | --- | --- |
| R-01 | Estructura e interfaces | `index.html` con `<header>`, `<nav>`, `<main>`, `<section>` por vista, `<label>` asociado a cada campo, botones descriptivos y `<table>` con `<thead>`/`<tbody>`. |
| R-02 | Calidad / CSS | `css/styles.css` con identidad visual coherente, Flexbox/Grid, responsive en `320 px` y `1280 px` sin scroll horizontal global, foco visible (`:focus-visible`), mensajes de error textuales. |
| R-03 | Cliente HTTP | `js/api.js` centraliza `API_BASE = "/api"`, conserva `/` final (ej. `/api/libros/`, `/api/ventas/`), parsea JSON y propaga `status` y `detail` del servidor. |
| R-04 | Catálogo | `GET /api/libros/` con `titulo`, `limit` (defecto 20) y `offset` (desde 0, reiniciado al filtrar). Muestra `«Sin clasificar»` si `genero` es `null`. Detalle via `GET /api/libros/{id}`. |
| R-05 | Alta de libros y clientes | `POST /api/libros/` (`201`) y `POST /api/clientes/` (`201`). Valida campos en front, muestra resultado cerca del formulario, actualiza vistas tras `201` y muestra `detail` ante `409`/`422`. |
| R-06 | Ventas e historial | Borrador en memoria sin libros repetidos y cantidades enteras `> 0`. `POST /api/ventas/` deshabilita el botón al enviar; limpia en `201` y conserva borrador en `409`/`422`. Historial con `GET /api/ventas/` y `GET /api/ventas/{id}`. |
| R-07 | Datos y estados | Diferencia estados de **carga**, **lista vacía**, **búsqueda sin coincidencias** y **error de conexión**. Inserta texto de usuario de forma segura (`textContent`, sin `innerHTML` inseguro). |

---

## 5. Estructura propuesta en `frontend/public/`
```text
frontend/public/
  index.html
  css/
    styles.css
  js/
    api.js        # Cliente fetch centralizado (/api) y manejo de errores HTTP
    catalogo.js   # Listado paginado, filtro por título y modal/panel de detalle
    altas.js      # Formularios de alta de libros y clientes + carga de selectores
    ventas.js     # Borrador de venta en memoria, envío POST /api/ventas/ e historial
    app.js        # Navegación entre vistas, estado compartido y arranque inicial
```

---

## 6. Estados y manejo de errores
- **Carga:** indicador textual visible mientras dura el `fetch`.
- **Lista vacía vs. sin coincidencias:** si `total === 0` sin filtro → *"No hay registros cargados."*; si `total === 0` con filtro `titulo` → *"No se encontraron libros para «...»."*
- **Error de conexión (red caída / 502 / 503):** mensaje claro sin romper la vista ni borrar formularios.
- **Errores `409` / `422`:** mostrar el `detail` devuelto por FastAPI junto al formulario; en ventas, **conservar intacto el borrador**.

---

## 7. Restricciones técnicas y convenciones
- HTML5, CSS3 y ES Modules nativos (`<script type="module" src="js/app.js"></script>`), cero dependencias externas.
- Todas las rutas relativas (`css/styles.css`, `js/app.js`) para funcionar bajo Nginx en `/`.
- Inserción segura en el DOM mediante `textContent` / creación de nodos (sin concatenar HTML con datos del usuario).

---

## 8. Criterios de aceptación
- [ ] CA-01 — Catálogo pagina, filtra por título reiniciando `offset`, muestra `«Sin clasificar»` y abre detalle con autores (`R-03`, `R-04`, `R-07`).
- [ ] CA-02 — Alta de libro y cliente validan entradas, envían contrato exacto, actualizan vistas en `201` y muestran errores `409`/`422` (`R-05`).
- [ ] CA-03 — Venta exige cliente, `>= 1` renglón, cantidades enteras `> 0`, sin libros repetidos; limpia en `201` y conserva borrador en error; historial y detalle muestran importes históricos (`R-06`).
- [ ] CA-04 — Interfaz navegable por teclado, legible en `320 px` y `1280 px` sin scroll horizontal global (`R-01`, `R-02`).

---

## 9. Supuestos declarados y decisión para confirmar
- **Supuesto 1:** Como el backend ya expone listados (`GET /api/autores/` y `GET /api/clientes/`), además de la consulta por ID (`GET /api/autores/{id}` y `GET /api/clientes/{id}`), se usarán los listados para los selectores y también se permitirá buscar/verificar por ID (luego se documenta en `README.md` como pide el Global).
- **Supuesto 2:** El diseño visual usará una paleta sobria de librería (tonos crema/pizarra/acento cálido) con tipografía del sistema, sin imágenes externas.

**Pregunta antes de pasar a PLAN e IMPLEMENTACIÓN:** ¿Aprobás esta especificación (la estructura de `frontend/public/`, las 5 vistas en una sola página con navegación por pestañas/secciones y los supuestos declarados) para avanzar al **PLAN** y luego implementarla?
