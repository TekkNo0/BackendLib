# PLAN — Implementación del Frontend (`frontend/public/`)

Checklist de tareas atómicas derivadas de `frontend/SPEC.md`:

- [ ] **T-01 · Estructura HTML semántica (`frontend/public/index.html`)**
  - **Cubre:** `R-01`, `R-04`, `R-05`, `R-06` (`CA-01`, `CA-02`, `CA-03`, `CA-04`)
  - **Archivos:** `frontend/public/index.html`
  - **Dependencias:** Ninguna.
  - **Detalle:** `<header>`, `<nav>` con 5 pestañas (`Catálogo`, `Libros`, `Clientes`, `Ventas`, `Historial`), `<main>` con 5 `<section>` (una activa a la vez), `<dialog>` para detalle de libro y detalle de venta, etiquetas `<label for="...">` asociadas a cada control, `<table>` con `<thead>`/`<tbody>`, zonas de estado/errores accesibles (`aria-live="polite"`).
  - **Comprobación:** Estructura HTML válida sin dependencias externas y rutas relativas locales.

- [ ] **T-02 · Estilos CSS propios y adaptables (`frontend/public/css/styles.css`)**
  - **Cubre:** `R-02` (`CA-04`)
  - **Archivos:** `frontend/public/css/styles.css`
  - **Dependencias:** `T-01`.
  - **Detalle:** Variables CSS (paleta librería), Flexbox/Grid responsive para `320 px` y `1280 px`, contenedores `.table-wrap { overflow-x: auto }` para tablas sin scroll horizontal de página, `:focus-visible` marcado para navegación por teclado, estilos de mensajes textuales de éxito/error/carga/vacío y `<dialog>`.
  - **Comprobación:** Inspección visual en `320 px` y `1280 px` sin `scrollWidth > clientWidth` en `document.documentElement`.

- [ ] **T-03 · Cliente HTTP centralizado (`frontend/public/js/api.js`)**
  - **Cubre:** `R-03`, `R-07` (`CA-01`, `CA-02`, `CA-03`)
  - **Archivos:** `frontend/public/js/api.js`
  - **Dependencias:** Ninguna.
  - **Detalle:** `API_BASE = "/api"`, helper `request(path, options)` que conserva barras finales, arma query params, lanza `ApiError(status, detail, isNetworkError)` ante `!res.ok` o fallo de red, y expone funciones para `libros`, `editoriales`, `generos`, `autores`, `clientes`, `ventas` y `health`.
  - **Comprobación:** Verificación de sintaxis JS y revisión de URLs con `/` final (`/api/libros/`, `/api/ventas/`, `/api/clientes/`, `/api/editoriales/`, `/api/generos/`, `/api/autores/`).

- [ ] **T-04 · Módulo de Catálogo (`frontend/public/js/catalogo.js`)**
  - **Cubre:** `R-04`, `R-07` (`CA-01`)
  - **Archivos:** `frontend/public/js/catalogo.js`
  - **Dependencias:** `T-01`, `T-03`.
  - **Detalle:** Carga `GET /api/libros/` con `titulo`, `limit` (20) y `offset` (reinicia `offset = 0` al buscar). Renderiza `«Sin clasificar»` cuando `genero` es `null`. Diferencia carga, lista vacía, búsqueda sin coincidencias y error de conexión. Abre detalle `GET /api/libros/{id}` en `<dialog>` mostrando autores (`nombre`, `rol`, `orden`).
  - **Comprobación:** Flujo completo de búsqueda, paginación y apertura de detalle.

- [ ] **T-05 · Módulo de Altas: Libros y Clientes (`frontend/public/js/altas.js`)**
  - **Cubre:** `R-05`, `R-07` (`CA-02`)
  - **Archivos:** `frontend/public/js/altas.js`
  - **Dependencias:** `T-01`, `T-03`.
  - **Detalle:** Carga selectores de editoriales, géneros (incluyendo `«Sin clasificar»`) y autores (con selector + verificación por ID `GET /api/autores/{id}` + lista de autorías con `rol` y `orden`). Valida campos de libro y envía `POST /api/libros/`. Valida nombre/email de cliente, envía `POST /api/clientes/`, lista clientes y permite buscar por ID `GET /api/clientes/{id}`. Muestra mensajes de `201`, `409` y `422` cerca de cada formulario y actualiza vistas relacionadas.
  - **Comprobación:** Alta exitosa (`201`) y manejo de conflictos (`409` ISBN/email repetido) y `422`.

- [ ] **T-06 · Módulo de Ventas e Historial (`frontend/public/js/ventas.js`)**
  - **Cubre:** `R-06`, `R-07` (`CA-03`)
  - **Archivos:** `frontend/public/js/ventas.js`
  - **Dependencias:** `T-01`, `T-03`.
  - **Detalle:** Borrador en memoria (cliente seleccionado + renglones sin libros duplicados, editar cantidad, quitar renglón). Valida `>= 1` renglón y cantidades enteras `> 0`. Envía `POST /api/ventas/` deshabilitando el botón; en `201` muestra precios unitarios/subtotales/total devueltos, limpia borrador y refresca historial/catálogo; en `409`/`422` conserva el borrador. Historial paginado `GET /api/ventas/` + detalle `GET /api/ventas/{id}` en `<dialog>`.
  - **Comprobación:** Confirmación de venta, conservación de borrador ante error e importes históricos en detalle.

- [ ] **T-07 · Orquestador principal (`frontend/public/js/app.js`)**
  - **Cubre:** `R-01`, `R-04`, `R-05`, `R-06` (`CA-01`..`CA-04`)
  - **Archivos:** `frontend/public/js/app.js`
  - **Dependencias:** `T-04`, `T-05`, `T-06`.
  - **Detalle:** Inicializa navegación entre las 5 vistas, coordina recarga de selectores/listados cuando se crea un libro, cliente o venta, y carga inicial de datos.
  - **Comprobación:** Navegación completa entre pestañas y sincronización de datos entre vistas.
