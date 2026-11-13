# Programación III — Parcial: La librería con acceso, transacciones y despliegue en el VPS
**Universidad Tecnológica Nacional (UTN) — Tecnicatura Universitaria en Programación**  
**Unidad 1 a 6: Del objeto a la transacción**

---

## 1. Integrantes del Grupo

- **Nombre y Apellido**: MAXIMO MONARDEZ, JOAQUIN MENDEZ, FACUNDO CHACON, MATIAS RUIZ, THIAGO OVIEDO, TIAGO GUILLOT (Grupo de Desarrollo)
- **Materia**: Programación III
- **Carrera**: Tecnicatura Universitaria en Programación (TUP)
- **Año lectivo**: 2026

---

## 2. Arquitectura del Proyecto

El backend está construido con **FastAPI**, **SQLModel**, **SQLAlchemy 2.0 (Async)** y **PostgreSQL 16**, siguiendo estrictamente el patrón de **Arquitectura en Capas**:

$$\text{Router} \longrightarrow \text{Service} \longrightarrow \text{Unit of Work} \longrightarrow \text{Repository} \longrightarrow \text{Model}$$

### Principios y Separación de Responsabilidades:
1. **Router (`app/modules/*/router.py`)**: Valida contratos de entrada/salida HTTP con Pydantic, maneja cookies HttpOnly e invoca a la capa de servicios. Nunca interactúa directamente con la base de datos ni con los repositorios.
2. **Service (`app/modules/*/service.py`)**: Orquesta las reglas de negocio, coordina las validaciones entre entidades e interactúa exclusivamente con el Unit of Work.
3. **Unit of Work (`app/core/unit_of_work.py` y `app/modules/*/unit_of_work.py`)**: Delimita la transacción atómica de base de datos. Controla el `commit()` al completar exitosamente todas las operaciones y el `rollback()` automático ante cualquier error o excepción.
4. **Repository (`app/core/repository.py` y `app/modules/*/repository.py`)**: Abstrae las consultas y persistencia. Hereda de `BaseRepository[T]` y `SoftDeleteRepository[T]`. Ejecuta únicamente `flush()` y lecturas con eager loading (`selectinload`), **nunca ejecuta commit**.
5. **Model (`app/modules/*/models.py`)**: Entidades de datos y tablas SQLModel/SQLAlchemy con sus restricciones de integridad (`CHECK`, `UNIQUE` parciales, claves foráneas).

---

## 3. Requisitos del Sistema

- **Python**: 3.12 o superior
- **PostgreSQL**: 16 (con base de datos creada, por ejemplo `libreria`)
- **Git**

---

## 4. Guía de Instalación y Puesta en Marcha desde Cero

Siga estrictamente los siguientes pasos en una terminal:

### Paso 1: Clonar o posicionarse en la carpeta del parcial
```bash
cd parcial
```

### Paso 2: Crear el entorno virtual de Python
En Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

En Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### Paso 3: Instalar las dependencias del proyecto
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Paso 4: Configurar las variables de entorno (`.env`)
Copie la plantilla de ejemplo:
```bash
cp env.example .env
```
*(En Windows PowerShell: `Copy-Item env.example .env`)*

Edite el archivo `.env` configurando la cadena de conexión a su PostgreSQL local y generando una clave secreta segura para JWT:

#### Generación de la clave de firma (`SECRET_KEY`):
Ejecute en la terminal el siguiente comando interactivo para obtener un token criptográficamente seguro:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
Copie el valor devuelto y péguelo en la variable `SECRET_KEY` de su `.env`.

Ejemplo de contenido de `.env`:
```ini
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/libreria
SECRET_KEY=clave_criptografica_generada_con_secrets
ACCESS_TOKEN_EXPIRE_MINUTES=30
COOKIE_SECURE=false
SQL_ECHO=false
```

### Paso 5: Aplicar las migraciones de base de datos con Alembic
Asegúrese de que el servicio de PostgreSQL esté en ejecución y la base de datos `libreria` esté creada (`createdb -U postgres libreria` o vía pgAdmin/psql).
Luego ejecute:
```bash
alembic upgrade head
```
Esto creará el esquema completo:
- `0001_initial_tp`: Estructura base del TP (editoriales, géneros, autores, libros, clientes, ventas, renglones).
- `0002_parcial_modelos`: Extensiones del parcial (usuarios, asignacion_rol con índice único parcial, intento_acceso, evento_seguridad, movimiento_stock, columna cliente.usuario_id y libro.borrado_en con índice único parcial sobre ISBN).
- `0003_trigger_solo_agregado`: Función PL/pgSQL y trigger `tr_movimiento_stock_solo_agregado` que garantiza la inmutabilidad de los movimientos de stock (sólo agregado).

### Paso 6: Cargar los datos iniciales requeridos (Seed)
Ejecute el script de inicialización idempotente:
```bash
python seed.py
```
Este script inicializa:
- 5 usuarios (`admin@example.com`, `admin2@example.com`, `vendedor@example.com`, `ana@example.com`, `nuevo@example.com`).
- Catálogo de libros con autores, géneros, editoriales y sus movimientos de stock inicial.
- Clientes (Lucía Fernández, Tomás Ríos, Ana Paz vinculada a usuario).
- Venta histórica #1 y auditoría de seguridad del sistema.

### Paso 7: Iniciar el servidor web
```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
La API quedará escuchando en `http://127.0.0.1:8000`.  
Documentación interactiva Swagger: `http://127.0.0.1:8000/docs`  
Documentación ReDoc: `http://127.0.0.1:8000/redoc`

---

## 5. Cuentas de Usuario de Prueba (Seed)

| Email | Contraseña | Rol asignado | Características |
|---|---|---|---|
| `admin@example.com` | `Admin123!` | `ADMIN` | Administrador principal con autoprotección |
| `admin2@example.com` | `Admin123!` | `ADMIN` | Segundo administrador del sistema |
| `vendedor@example.com` | `Vendedor123!` | `VENDEDOR` | Personal de ventas y atención |
| `ana@example.com` | `Ana12345!` | `CLIENTE` | Cliente con cuenta web vinculada a ficha cliente #3 |
| `nuevo@example.com` | `Nuevo123!` | `VENDEDOR` | Empleado nuevo con `debe_cambiar_password = true` |

---

## 6. Suite de Pruebas y Evidencias

### Ejecución de Pruebas Automatizadas (Pytest)
Para correr la suite de pruebas unitarias y de integración:
```bash
pytest test/ -v
```

### Casos de Prueba HTTP (REST Client) en `test/`
El directorio `test/` incluye los 16 archivos `.http` preparados para la extensión REST Client de VS Code:
- `caso_c01_parametro_invalido.http`: Parámetro no entero en ruta -> 422 sin ejecutar handler.
- `caso_c02_registro_conflictos.http`: Auto-registro, colisión de usuario y cliente -> 201 y 409 sin filas huérfanas.
- `caso_c03_cookie_login.http`: Cookie HttpOnly, cuerpo sin token, rechazo de Bearer -> 401.
- `caso_c04_timing_login.http`: Contraseña mala vs email inexistente -> 401 tiempo idéntico (dummy hash).
- `caso_c05_rate_limit.http`: 5 fallos consecutivos, el 6to responde 429 con `Retry-After: 60`.
- `caso_c06_permisos_y_lo_propio.http`: 401 vs 403, vendedor no crea libros, cliente sólo ve sus compras.
- `caso_c07_revocar_rol_en_vivo.http`: Revocación en tiempo real (invalida sin nuevo login) y fechas inválidas -> 422.
- `caso_c08_autoproteccion_admin.http`: Admin no puede auto-revocarse rol ADMIN -> 409.
- `caso_c09_cambio_obligatorio.http`: Intercepción 403 fuera de `/auth`, desbloqueo tras cambio con misma cookie.
- `caso_c10_venta_valida.http`: Venta atómica con 2 libros, descuento de inventario y despacho asincrónico.
- `caso_c11_venta_insuficiente.http`: Rollback total ante stock insuficiente, consistencia en 5 libros -> 409.
- `caso_c12_venta_inexistente.http`: Rechazo de ventas con cliente inexistente, libro inexistente o libro dado de baja -> 409.
- `caso_c13_reponer_baja_reuso_isbn.http`: Reposición (200), baja lógica (204), alta con mismo ISBN (201), colisión de vigentes (409) e historial preservado.
- `caso_c14_solo_agregado.sql`: Script SQL ejecutado en psql para probar rechazo de UPDATE y DELETE en `movimiento_stock`.
- `caso_c15_eager_loading_n1.http`: Detalle de venta con 2 y 4 renglones demostrando cantidad fija de consultas SQL.
- `caso_c16_filtros_seguridad_paginacion.http`: Inyección SQL neutra, paginación, exceso de páginas -> 422, y rechazo de stock en PATCH.

### Carpeta de Evidencias (`evidencia/`)
- `evidencia/c14_psql_output.txt`: Captura de ejecución de `solo_agregado.sql` en PostgreSQL demostrando el rechazo por disparador de UPDATE y DELETE.
- `evidencia/c15_consultas_n1_output.txt`: Captura de consultas SQL en consola (`SQL_ECHO=True`) para `GET /ventas/{id}` demostrando ausencia de N+1 con eager loading (`selectinload`).
