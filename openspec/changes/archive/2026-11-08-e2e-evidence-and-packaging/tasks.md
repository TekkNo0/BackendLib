# Tasks

## 1. Suite de Casos HTTP (C-01 a C-16) y Script de Inmutabilidad

- [x] 1.1 Crear y organizar los 16 archivos `.http` canónicos en `parcial/test/` (`caso_c01_parametro_invalido.http` a `caso_c16_filtros_seguridad_paginacion.http`) con respuestas esperadas comentadas y sintaxis REST Client.
- [x] 1.2 Consolidar `parcial/test/solo_agregado.sql` para la comprobación del trigger de inmutabilidad (Caso C-14).

## 2. Evidencias de Ejecución (C-14 y C-15)

- [x] 2.1 Generar `parcial/evidencia/c14_psql_output.txt` con la sesión psql demostrando la inserción y el rechazo por disparador de UPDATE y DELETE.
- [x] 2.2 Generar `parcial/evidencia/c15_consultas_n1_output.txt` registrando la captura de queries SQL para `GET /ventas/{id}` con 2 y 4 renglones demostrando cantidad fija de consultas (sin N+1).

## 3. Documentación y Verificación de Suite de Tests

- [x] 3.1 Redactar `parcial/README.md` completo con integrantes, arquitectura en capas, guía de despliegue local paso a paso desde cero y catálogo de endpoints.
- [x] 3.2 Ejecutar la suite completa de pruebas unitarias/integración en `parcial/test/` confirmando que todos los tests pasan limpiamente.

## 4. Empaquetado y Auditoría del Entregable ZIP

- [x] 4.1 Construir y ejecutar script de empaquetado que ensamble `Parcial_Cap1a6_Grupo.zip` conteniendo únicamente `parcial/` y `despliegue/`.
- [x] 4.2 Auditar el contenido del ZIP generado asegurando la ausencia total de `.venv`, `.env`, `__pycache__`, `*.pyc` y `.pytest_cache`.
