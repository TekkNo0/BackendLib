"""Script de empaquetado automatizado y validación de entrega.
UTN - Programación III - Parcial: La librería con acceso, transacciones y despliegue en el VPS.
Genera Parcial_Cap1a6_Grupo.zip conteniendo estrictamente parcial/ y despliegue/ sin archivos temporales ni secretos.
"""
from pathlib import Path
import sys
import zipfile

PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_ZIP = PROJECT_ROOT / "Parcial_Cap1a6_Grupo.zip"

FOLDERS_TO_INCLUDE = ["parcial", "despliegue"]

EXCLUDED_DIR_NAMES = {
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".idea",
    ".vscode",
    ".mypy_cache",
}

EXCLUDED_FILE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
}

EXCLUDED_FILE_NAMES = {
    ".env",
    ".env.local",
    ".DS_Store",
    "Thumbs.db",
}


def should_exclude(rel_path: Path) -> bool:
    """Evalúa si un archivo o directorio debe ser excluido del empaquetado final."""
    parts = rel_path.parts

    # Excluir directorios prohibidos en cualquier nivel de la ruta
    for part in parts[:-1]:
        if part in EXCLUDED_DIR_NAMES:
            return True

    # Excluir el archivo o directorio final
    name = rel_path.name
    if name in EXCLUDED_DIR_NAMES:
        return True
    if name in EXCLUDED_FILE_NAMES:
        return True
    if rel_path.suffix in EXCLUDED_FILE_EXTENSIONS:
        return True

    # Asegurar que archivos .env.* no se incluyan, salvo env.example
    if name.startswith(".env") and name != "env.example":
        return True

    return False


def build_package() -> None:
    print(f"Iniciando empaquetado en: {OUTPUT_ZIP}")
    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()

    included_count = 0
    total_uncompressed_bytes = 0

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for folder_name in FOLDERS_TO_INCLUDE:
            folder_path = PROJECT_ROOT / folder_name
            if not folder_path.exists():
                raise FileNotFoundError(f"El directorio requerido '{folder_name}' no existe en {PROJECT_ROOT}")

            for file_path in folder_path.rglob("*"):
                if file_path.is_file():
                    rel_to_root = file_path.relative_to(PROJECT_ROOT)
                    if should_exclude(rel_to_root):
                        continue

                    # Escribir en el zip con separador estándar POSIX /
                    archive_name = rel_to_root.as_posix()
                    zipf.write(file_path, arcname=archive_name)
                    included_count += 1
                    total_uncompressed_bytes += file_path.stat().st_size

    zip_size_bytes = OUTPUT_ZIP.stat().st_size
    print(f"Empaquetado finalizado:")
    print(f"  - Archivos incluidos: {included_count}")
    print(f"  - Tamaño descomprimido: {total_uncompressed_bytes / 1024:.2f} KB")
    print(f"  - Tamaño ZIP comprimido: {zip_size_bytes / 1024:.2f} KB")

    validate_package()


def validate_package() -> None:
    print("\nAuditoría estricta del contenido del archivo ZIP...")
    with zipfile.ZipFile(OUTPUT_ZIP, "r") as zipf:
        names = zipf.namelist()

        has_parcial = False
        has_despliegue = False
        violations = []

        for name in names:
            # 1. Comprobar pertenencia a parcial/ o despliegue/
            if name.startswith("parcial/"):
                has_parcial = True
            elif name.startswith("despliegue/"):
                has_despliegue = True
            else:
                violations.append(f"Archivo fuera de las carpetas permitidas: {name}")

            # 2. Comprobar ausencia de .venv o __pycache__
            if ".venv" in name.split("/"):
                violations.append(f"Directorio virtualenv detectado: {name}")
            if "__pycache__" in name.split("/"):
                violations.append(f"Caché bytecode detectada: {name}")
            if ".pytest_cache" in name.split("/"):
                violations.append(f"Caché pytest detectada: {name}")

            # 3. Comprobar ausencia de .env
            filename = name.split("/")[-1]
            if filename == ".env" or (filename.startswith(".env.") and filename != "env.example"):
                violations.append(f"Archivo de variables de entorno secreto detectado: {name}")

            # 4. Comprobar extensiones binarias de python
            if filename.endswith((".pyc", ".pyo", ".pyd")):
                violations.append(f"Binario compilado de Python detectado: {name}")

        assert has_parcial, "El archivo ZIP no contiene la carpeta 'parcial/'"
        assert has_despliegue, "El archivo ZIP no contiene la carpeta 'despliegue/'"

        # Comprobar presencia de artefactos clave
        assert "parcial/README.md" in names, "Falta parcial/README.md en el ZIP"
        assert "parcial/env.example" in names, "Falta parcial/env.example en el ZIP"
        assert "despliegue/DEPLOY.md" in names, "Falta despliegue/DEPLOY.md en el ZIP"
        assert "despliegue/Dockerfile" in names, "Falta despliegue/Dockerfile en el ZIP"
        assert "parcial/evidencia/c14_psql_output.txt" in names, "Falta parcial/evidencia/c14_psql_output.txt"
        assert "parcial/evidencia/c15_consultas_n1_output.txt" in names, "Falta parcial/evidencia/c15_consultas_n1_output.txt"
        assert "despliegue/evidencia/d01_docker_images.txt" in names, "Falta despliegue/evidencia/d01_docker_images.txt"

        if violations:
            print("ERROR: Se encontraron violaciones en la auditoría:")
            for v in violations:
                print(f"  [VIOLACION] {v}")
            OUTPUT_ZIP.unlink(missing_ok=True)
            sys.exit(1)

        print("AUDITORÍA EXITOSA: El archivo ZIP cumple al 100% con todos los requisitos de entrega.")


if __name__ == "__main__":
    build_package()
