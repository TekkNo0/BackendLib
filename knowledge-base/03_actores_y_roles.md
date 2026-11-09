# Actores y Roles

## Actores del sistema

| Actor | Descripción | Mecanismo de autenticación / acceso |
|---|---|---|
| **ADMIN** | Personal con máximos privilegios administrativos. Mantiene catálogo, stock, usuarios y roles. | Sesión autenticada vía cookie `access_token` con rol vigente `'ADMIN'` en base de datos. |
| **VENDEDOR** | Personal de atención en mostrador. Registra ventas y atiende clientes. | Sesión autenticada vía cookie `access_token` con rol vigente `'VENDEDOR'` en base de datos. |
| **CLIENTE** | Cliente con acceso web. Consulta exclusivamente sus propias ventas. | Sesión autenticada vía cookie `access_token` con rol vigente `'CLIENTE'` en base de datos. |
| **PÚBLICO** | Visitante no autenticado. Explora el catálogo de libros, géneros, autores y editoriales. | Sin credenciales (acceso directo a grupo abierto). |

## RBAC — Matriz de permisos

| Recurso / Operación | Método y Ruta | ADMIN | VENDEDOR | CLIENTE | PÚBLICO |
|---|---|---|---|---|---|
| Salud del sistema | `GET /health/live`, `/health/ready` | Sí | Sí | Sí | Sí |
| Registro de clientes | `POST /auth/registro` | Sí | Sí | Sí | Sí |
| Autenticación básica | `POST /auth/login`, `POST /auth/logout` | Sí | Sí | Sí | Sí |
| Datos de sesión propia | `GET /auth/yo` | Sí | Sí | Sí | No (401) |
| Cambio de contraseña | `POST /auth/cambiar-password` | Sí | Sí | Sí | No (401) |
| Consulta catálogo de libros | `GET /libros`, `GET /libros/{id}` | Sí | Sí | Sí | Sí |
| Editoriales, géneros, autores (lectura) | `GET /editoriales`, `GET /generos`, `GET /autores` | Sí | Sí | Sí | Sí |
| Libros por entidad | `GET /{entidad}/{id}/libros` | Sí | Sí | Sí | Sí |
| Alta de personal | `POST /usuarios` | Sí | No (403) | No (403) | No (401) |
| Gestión de roles | `GET, POST, DELETE /usuarios/{id}/roles` | Sí | No (403) | No (403) | No (401) |
| Auditoría / Eventos | `GET /eventos` | Sí | No (403) | No (403) | No (401) |
| Catálogo (creación y modificación) | `POST, PATCH /editoriales`, `/generos`, `/autores` | Sí | No (403) | No (403) | No (401) |
| Alta de libro (con autores y stock inicial) | `POST /libros` | Sí | No (403) | No (403) | No (401) |
| Modificación de libro (título, precio) | `PATCH /libros/{id}` | Sí | No (403) | No (403) | No (401) |
| Baja lógica de libro | `DELETE /libros/{id}` | Sí | No (403) | No (403) | No (401) |
| Reposición de stock | `POST /libros/{id}/reponer` | Sí | No (403) | No (403) | No (401) |
| Ver movimientos de stock de libro | `GET /libros/{id}/movimientos` | Sí | No (403) | No (403) | No (401) |
| Gestión de clientes | `POST /clientes`, `GET, PATCH /clientes/{id}`, `POST /clientes/{id}/perfil` | Sí | Sí | No (403) | No (401) |
| Ventas de un cliente | `GET /clientes/{id}/ventas` | Sí | Sí | No (403) | No (401) |
| Registrar venta | `POST /ventas` | Sí | Sí | No (403) | No (401) |
| Listado general de ventas | `GET /ventas` | Sí | Sí | No (403) | No (401) |
| Detalle de una venta | `GET /ventas/{id}` | Sí | Sí | Solo si es dueño (403 ajeno) | No (401) |
| Listado de compras propias | `GET /mis-ventas` | Sí | Sí | Sí (sus ventas) | No (401) |

## Rutas públicas
- `GET /health/live`
- `GET /health/ready`
- `POST /auth/registro`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /libros`, `GET /libros/{id}`
- `GET /editoriales`, `GET /generos`, `GET /autores`
- `GET /editoriales/{id}/libros`, `GET /generos/{id}/libros`, `GET /autores/{id}/libros`
