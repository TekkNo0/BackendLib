# Design

## Context

El parcial de Programación III exige que el proyecto esté completamente verificado y empaquetado en `Parcial_Cap1a6_Grupo.zip` conteniendo `parcial/` y `despliegue/`. Los 16 casos de prueba del parcial (C-01 a C-16) deben estar representados en archivos `.http` comentados en `parcial/test/`, junto al script de verificación del trigger inmutable `solo_agregado.sql`. Asimismo, se deben generar las evidencias `c14_psql_output.txt` y `c15_consultas_n1_output.txt` en `parcial/evidencia/`, redactar `parcial/README.md` y compilar el ZIP excluyendo `.env`, `.venv` y cachés.

## Goals / Non-Goals

**Goals:**
- Generar y normalizar los 16 archivos `.http` (`caso_c01_*.http` a `caso_c16_*.http`) en `parcial/test/` con comentarios detallados de respuesta esperada y headers de sesión (`# @name`, `# @no-cookie-jar`, `Cookie: ...`).
- Generar `parcial/evidencia/c14_psql_output.txt` ejecutando o simulando con exactitud la sesión psql contra el trigger `tr_movimiento_stock_solo_agregado`.
- Generar `parcial/evidencia/c15_consultas_n1_output.txt` capturando el log de consultas SQL emitido con `SQL_ECHO=True` para `GET /ventas/{id}` (con 2 renglones vs 4 renglones), verificando que la carga de renglones y libros se resuelve con `selectinload` en un número constante de consultas.
- Redactar `parcial/README.md` exhaustivo y claro con todos los pasos para levantar el entorno desde cero.
- Construir un script Python/PowerShell determinístico para generar `Parcial_Cap1a6_Grupo.zip` en la raíz de `ParcialProg`, validando que contenga sólo `parcial/` y `despliegue/` y cero archivos `.env`, `.venv`, `__pycache__` o `.pytest_cache`.

**Non-Goals:**
- No alterar las firmas de API existentes ni los modelos ya aprobados en fases C-01 a C-09.
- No incluir bases de datos embebidas (SQLite) ni credenciales de producción en los scripts o archivos de evidencia.

## Decisions

### 1. Formato y Organización de la Suite de Pruebas `.http`
- **Decisión**: Proveer los 16 archivos canónicos denominados `caso_c01_parametro_invalido.http` hasta `caso_c16_filtros_seguridad_paginacion.http` en `parcial/test/`, manteniendo también los archivos agrupados por módulo (`auth.http`, `libros.http`, `usuarios.http`, `ventas.http`, `health.http`) para conveniencia del desarrollador.
- **Alternativa considerada**: Solo mantener los archivos por módulo. Rechazada porque la consigna y la KB exigen explícitamente los casos `caso_c01` a `caso_c16`.

### 2. Generación de Evidencia C-15 (N+1)
- **Decisión**: Ejecutar una prueba automatizada en pytest o script con motor `echo=True` que realiza `GET /ventas/{id}` sobre una venta de 2 renglones y una venta de 4 renglones, capturando las consultas emitidas por SQLAlchemy para verificar que el número de SELECT emitidos es idéntico (SELECT venta, SELECT renglones, SELECT libros). Guardar la traza formateada en `parcial/evidencia/c15_consultas_n1_output.txt`.
- **Alternativa considerada**: Redactar manualmente la traza. Generarla vía ejecución directa garantiza fidelidad técnica absoluta.

### 3. Generación de Evidencia C-14 (Trigger Inmutable en PostgreSQL)
- **Decisión**: Ejecutar el script `solo_agregado.sql` contra PostgreSQL o capturar la salida estándar de `psql` mostrando el `INSERT` exitoso y los subsiguientes `ERROR: La tabla movimiento_stock es de solo agregado` ante `UPDATE` y `DELETE`. Guardar el resultado en `parcial/evidencia/c14_psql_output.txt`.

### 4. Empaquetador Limpio
- **Decisión**: Usar un script en Python con `zipfile.ZipFile` con compresión `ZIP_DEFLATED` que recorra recursivamente `parcial/` y `despliegue/` aplicando un filtro de exclusión estricto (`.venv`, `__pycache__`, `*.pyc`, `.env`, `.pytest_cache`, `.DS_Store`). Luego, inspeccionar la lista de entradas del ZIP generado para certificar la exclusión.

## Risks / Trade-offs

- **[Risk]** Inclusión accidental de un archivo `.env` o `.venv` en el archivo comprimido.
  - **Mitigation**: Script de verificación post-empaquetado que busca tokens prohibidos en los nombres de archivo del ZIP y arroja error fatal si encuentra alguno.
- **[Risk]** Divergencia en los IDs o datos de seed entre los casos `.http`.
  - **Mitigation**: Los archivos `.http` asumen la ejecución previa de `python seed.py`, referenciando los IDs y usuarios creados por el seed (admin, vendedor, ana, libros 1..5, etc.).
