# PARCIAL: La librería con acceso, transacciones y despliegue en el VPS
**UTN - Tecnicatura Universitaria en Programación - Programación III**
**Unidad 1 a 6: Del objeto a la transacción**

---

## 1. Objetivos

El parcial continúa el TP de la librería (capítulos 1 a 4) y lo lleva hasta el capítulo 6: al catálogo, los clientes y las ventas ya construidos se les agrega el acceso con usuarios y roles (capítulo 5), una capa de repositorios con Unit of Work que agrupa las escrituras de cada operación (capítulo 6) y, aparte, el despliegue del TP de los capítulos 1 a 4 en el VPS, dentro de un contenedor.

Al finalizar, el proyecto entregado debe demostrar que el grupo puede:
1. Reorganizar una API asincrónica en capas —Router → Service → UoW → Repository → Model— donde cada capa sabe lo suyo y nada más.
2. Evolucionar un esquema ya versionado con Alembic: una migración autogenerada y leída antes de aplicarla, y otra escrita a mano para lo que la comparación automática no ve.
3. Autenticar con contraseñas guardadas con bcrypt y un token en una cookie `HttpOnly`, sin frenar el servidor y sin revelar qué cuentas existen.
4. Autorizar consultando los roles en la base en cada petición, con vigencia, y distinguir siempre entre 401 y 403.
5. Agrupar en una sola transacción las escrituras de una operación de negocio, de modo que un fallo en el medio no deje datos a medias.
6. Delegar en la base las garantías que la base puede dar: unicidad entre los vigentes, claves foráneas, comprobaciones y el sólo agregado.
7. Empaquetar el TP de la librería (capítulos 1 a 4) en una imagen de Docker y ponerlo en línea en el VPS con una configuración que no filtra secretos ni expone lo que no debe.

---

## 2. Alcance y Cambios respecto al TP Capítulos 1 a 4

### Qué queda afuera
- No se evalúa la concurrencia (capítulo 7). Dos ventas del último ejemplar de un libro...
- Tampoco hay colas de tareas con Redis (capítulo 8): el aviso al cliente se resuelve con `BackgroundTasks` en el mismo proceso con `await asyncio.sleep(0.5)` simulado.

### Tabla de Cambios
- **Usuarios, roles e intentos de acceso**: Nuevo. Tablas `usuario`, `asignacion_rol`, `intento_acceso` y `evento_seguridad`; módulo `usuarios`.
- **cliente**: Se agrega `usuario_id`, nulo permitido y UNIQUE: un cliente puede tener, o no, acceso por la web.
- **libro**: Se agrega el borrado lógico (`borrado_en`). El ISBN deja de ser un UNIQUE común y pasa a ser único entre los vigentes (`WHERE borrado_en IS NULL`).
- **Stock**: Nuevo `movimiento_stock`, de sólo agregado. El stock ya no se edita por PATCH: cambia con el alta, la reposición y las ventas.
- **Registro de una venta**: Además de crear la venta y sus renglones, descuenta el stock de cada libro y deja un movimiento por renglón, todo en una sola transacción.
- **Capas**: Todos los módulos pasan a repositorios + Unit of Work; los servicios dejan de recibir la sesión.
- **Configuración**: Settings con `pydantic-settings`, sin secretos por defecto.
- **Listados**: Devuelven el envoltorio `{items, total, page, size, pages}` en lugar de limit y offset.
- **Despliegue**: Nuevo, y aparte. El TP de los capítulos 1 a 4, tal como se entregó, se empaqueta en una imagen con un `Dockerfile`, se corre con `docker run` y se pone en línea en el VPS. No lleva ninguna de las demás modificaciones de esta tabla.

---

## 3. Requisitos Técnicos

- **Python**: 3.12
- **FastAPI**: 0.111 (todos los handlers con `async def`)
- **SQLModel**: 0.0.24 (modelos de tabla)
- **SQLAlchemy**: 2.0, asincrónico (motor, sesión y carga anticipada)
- **asyncpg**: 0.30 (driver asincrónico de PostgreSQL)
- **PostgreSQL**: 16
- **Alembic**: 1.13, plantilla asincrónica
- **pydantic-settings**: 2.0
- **bcrypt**: 4.0
- **PyJWT**: 2.8
- **uvicorn**: `fastapi[standard]`
- **Docker**: 20.10+ (python:3.12-alpine)

---

## 4. Modelo de Dominio y Tablas

### Tablas Existentes del TP (sin cambios o adaptadas):
- `editorial`: `id`, `nombre` (UNIQUE)
- `genero`: `id`, `nombre` (UNIQUE)
- `autor`: `id`, `nombre`, `nacionalidad`
- `libro_autor`: `libro_id`, `autor_id`, `rol`, `orden`
- `perfil_cliente`: `id`, `cliente_id`, `telefono`, `direccion`
- `cliente`: `id`, `nombre`, `email` (UNIQUE), `usuario_id` (nulo permitido, UNIQUE, FK -> usuario.id)
- `libro`: `id`, `isbn`, `titulo`, `precio` (Numeric/Decimal, CHECK precio > 0), `stock` (CHECK stock >= 0), `editorial_id`, `genero_id`, `borrado_en` (timestamptz nullable). Índice único parcial en `isbn` `WHERE borrado_en IS NULL`.
- `venta`: `id`, `cliente_id`, `fecha` (timestamptz), `total` (Decimal/Numeric)
- `renglon_venta`: `id`, `venta_id`, `libro_id`, `cantidad` (CHECK cantidad > 0), `precio_unitario` (Decimal/Numeric)

### Tablas Nuevas:
- `usuario`: `id` (int PK), `email` (str UNIQUE), `nombre` (str), `password_hash` (str), `activo` (bool, default True), `debe_cambiar_password` (bool, default False)
- `asignacion_rol`: `id` (int PK), `usuario_id` (FK), `rol` (CHECK 'ADMIN', 'VENDEDOR', 'CLIENTE'), `desde` (timestamptz), `vence_en` (timestamptz nulo), `revocada_en` (timestamptz nulo), `otorgada_por` (int nulo FK a usuario.id). Índice único parcial `(usuario_id, rol) WHERE revocada_en IS NULL`.
- `intento_acceso`: `id` (int PK), `cuando` (timestamptz), `email` (str), `ip` (str), `exito` (bool). Índice `(email, ip, cuando)`.
- `evento_seguridad`: `id` (int PK), `cuando` (timestamptz), `actor` (str), `accion` (str).
- `movimiento_stock`: `id` (int PK), `libro_id` (FK), `venta_id` (FK nulo), `usuario_id` (FK), `cantidad` (int, CHECK cantidad <> 0), `motivo` (str), `cuando` (timestamptz). Tabla de SÓLO AGREGADO protegida por disparador (trigger) en PostgreSQL.

---

## 5. Reglas de Negocio (RN-01 a RN-16)

- **RN-01**: Correo usuario, cliente, editorial y género son únicos. ISBN único entre vigentes (`WHERE borrado_en IS NULL`). Base garantiza unicidad, responde 409 con mensaje propio sin filtrar mensaje de base.
- **RN-02**: Auto-registro crea usuario, rol CLIENTE y cliente en un solo Unit of Work. Si cliente ya existe, 409 y no se apropia.
- **RN-03**: Usuario tiene a lo sumo una asignación abierta por rol. Índice único parcial `(usuario_id, rol) WHERE revocada_en IS NULL`. 409 en conflicto.
- **RN-04**: Permisos se deciden con roles vigentes en la base en cada petición. Token sólo informativo.
- **RN-05**: Un administrador no puede revocarse su propio rol ADMIN, y el sistema nunca queda sin administradores vigentes (comprobación en servicio; 409).
- **RN-06**: Usuario con `debe_cambiar_password == True` sólo puede acceder a `/auth` y rutas abiertas. El resto da 403.
- **RN-07**: Tras 5 intentos fallidos con mismo correo desde misma IP en 60s, responde 429 con cabecera `Retry-After` sin calcular hash bcrypt. Login exitoso reinicia la cuenta de fallos posteriores.
- **RN-08**: Login responde lo mismo ("Credenciales incorrectas") y tarda lo mismo exista o no el correo (verificación contra hash ficticio creado en lifespan).
- **RN-09**: Venta nace con renglones (al menos uno, sin duplicados), precio copiado del libro y total calculado por servidor. No modificable (no PATCH).
- **RN-10**: Registrar venta descuenta stock y crea movimientos de stock por renglón en un solo Unit of Work atómico. Si falta stock, 409 y rollback total.
- **RN-11**: Stock sólo cambia mediante movimientos: alta (stock inicial), reposición, venta. No PATCH sobre stock.
- **RN-12**: `movimiento_stock` es sólo agregado: trigger de base de datos rechaza UPDATE y DELETE con excepción.
- **RN-13**: Libro borrado lógicamente (`borrado_en IS NOT NULL`) no aparece en catálogo, no se puede vender ni reponer (409), pero ventas pasadas lo muestran.
- **RN-14**: Cliente sólo ve sus propias ventas (`/mis-ventas` y `/ventas/{id}` validando dueño; 403 si intenta ver ajena).
- **RN-15**: Ningún error expone trazas o texto interno de BD (IntegrityError mapeado a 409/422). Entradas inválidas nunca dan 500.
- **RN-16**: Alta de personal, cambio de rol y cambio de contraseña dejan registro en `evento_seguridad` en la misma transacción que el cambio.

---

## 6. Estructura Obligatoria del Proyecto

```
parcial/
  main.py
  seed.py
  app/
    core/
      config.py
      database.py
      security.py
      dependencies.py
      repository.py
      paginacion.py
      unit_of_work.py
    modules/
      health/
        router.py
      usuarios/
        models.py, schemas.py, repository.py, unit_of_work.py, service.py, router.py
      editoriales/
        models.py, schemas.py, repository.py, unit_of_work.py, service.py, router.py
      generos/
        models.py, schemas.py, repository.py, unit_of_work.py, service.py, router.py
      autores/
        models.py, schemas.py, repository.py, unit_of_work.py, service.py, router.py
      libros/
        models.py, schemas.py, repository.py, unit_of_work.py, service.py, router.py
      clientes/
        models.py, schemas.py, repository.py, unit_of_work.py, service.py, router.py
      ventas/
        models.py, schemas.py, repository.py, unit_of_work.py, service.py, router.py
  migrations/
    alembic.ini
    env.py
    versions/
  test/
    *.http
    solo_agregado.sql
  evidencia/
    caso_c14.txt
    caso_c15.txt
  requirements.txt
  env.example
  README.md

despliegue/
  (Código TP Capítulos 1 a 4)
  Dockerfile
  .dockerignore
  env.example
  DEPLOY.md
  evidencia/
    caso_d01.txt ... caso_d08.txt
```

---

## 7. Entorno y Formato de Entrega

La entrega final debe ser `Parcial_Cap1a6_<NombreDelGrupo>.zip` conteniendo:
1. `parcial/`
2. `despliegue/`
Sin `.venv`, `__pycache__`, ni `.env`.
