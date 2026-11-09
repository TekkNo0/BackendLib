FROM python:3.12-alpine

# Crear usuario sin privilegios para no correr como root
RUN adduser -D -u 1000 appuser

WORKDIR /app

# Instalar dependencias en capa de caché antes del código
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del TP
COPY . .

# Asignar permisos al usuario de la aplicación
RUN chown -R appuser:appuser /app

# Cambiar a usuario no root
USER appuser

EXPOSE 8000

# HEALTHCHECK sobre 127.0.0.1 para evitar problemas con localhost (IPv6 en Alpine)
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8000/health/ready || exit 1

# Migraciones automáticas al arrancar y posterior inicio del servidor ASGI
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
