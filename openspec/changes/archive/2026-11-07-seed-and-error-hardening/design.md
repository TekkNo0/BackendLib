# Design

## Context

El sistema tiene implementada la arquitectura en capas y todas las tablas del modelo relacional. Se requiere poblar los datos exigidos por la consigna del Parcial y blindar el sistema contra la exposición de detalles internos de base de datos.
Ver `proposal.md` para la motivación.

## Goals / Non-Goals

**Goals:**
- Script `seed.py` asincrónico e idempotente que inserte el conjunto completo de datos exigido sin fallar si se ejecuta reiteradas veces.
- Manejador global de `IntegrityError` en `parcial/app/core/exceptions.py` registrado en FastAPI para responder HTTP 409 limpio sin fugar trazas SQL ni nombres de tablas/columnas (RN-01, RN-15).
- Manejador global para errores no previstos respondiendo HTTP 500 genérico.

**Non-Goals:**
- Generación de datos sintéticos masivos o benchmarks de carga.

## Decisions

### Decisión 1: Idempotencia en `seed.py`
- **Elección**: Para cada entidad a sembrar (usuarios, editoriales, géneros, autores, libros, clientes), consultar previamente si ya existe por su campo identificador único (email, nombre, ISBN). Si existe, reutilizar el objeto; si no, crearlo. Para la Venta 1, si ya existe una venta para Lucía Fernández con fecha inicial, se omite para evitar duplicar descuentos de stock.
- **Razón**: Permite ejecutar el script en ambientes de desarrollo, testing o despliegue múltiples veces sin violar unicidad ni desfasar la contabilidad de stock.

### Decisión 2: Traducción global de `IntegrityError` (RN-01, RN-15)
- **Elección**: Registrar un exception handler para `sqlalchemy.exc.IntegrityError` que devuelva `JSONResponse(status_code=409, content={"detail": "Conflicto de integridad: la operación viola una restricción única o de clave foránea."})`.
- **Razón**: Cumple estrictamente con RN-01 ("la unicidad no se valida previamente con un SELECT sino que se delega a la base y se traduce a 409") y RN-15 ("ninguna respuesta de error expone trazas de error, nombres de tablas o mensajes nativos de PostgreSQL").

### Decisión 3: Manejador de excepciones 500 controlado
- **Elección**: Interceptar cualquier excepción no manejada (`Exception`) y responder HTTP 500 con un mensaje genérico `"Error interno del servidor"`, registrando el log de error en el servidor sin exponerlo al cliente.

## Risks / Trade-offs

- **[Riesgo de enmascarar errores de programación durante el desarrollo]**: Ocultar el detalle en HTTP 500 podría dificultar el debugging.
  → *Mitigación*: El exception handler registra la traza completa con `logging.error(...)` en los logs del servidor para diagnóstico.
