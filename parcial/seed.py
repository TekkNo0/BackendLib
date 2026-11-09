import asyncio
from datetime import datetime, timezone
from decimal import Decimal
import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import Settings
from app.core.database import create_engine_and_session_factory
from app.core.security import hash_password
from app.modules.autores.models import Autor
from app.modules.clientes.models import Cliente, PerfilCliente
from app.modules.editoriales.models import Editorial
from app.modules.generos.models import Genero
from app.modules.libros.models import Libro, LibroAutor
from app.modules.usuarios.models import AsignacionRol, EventoSeguridad, Usuario
from app.modules.ventas.models import MovimientoStock, RenglonVenta, Venta

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed")


async def run_seed(session: AsyncSession) -> None:
    """Ejecuta la población inicial de datos de manera idempotente."""

    logger.info("Iniciando carga de datos iniciales...")

    # 1. Historial de seguridad: comprobación si ya se ejecutó el seeder
    stmt_auditoria = select(EventoSeguridad).where(
        EventoSeguridad.actor == "SISTEMA",
        EventoSeguridad.accion == "Carga de los datos iniciales",
    )
    if (await session.execute(stmt_auditoria)).scalar_one_or_none():
        logger.info("Los datos iniciales ya se encuentran cargados en la base de datos. Omitiendo.")
        return

    # 2. Usuarios
    usuarios_data = [
        ("admin@example.com", "Admin Uno", "Admin123!", "ADMIN", False),
        ("admin2@example.com", "Admin Dos", "Admin123!", "ADMIN", False),
        ("vendedor@example.com", "Vendedor Uno", "Vendedor123!", "VENDEDOR", False),
        ("ana@example.com", "Ana Paz", "Ana12345!", "CLIENTE", False),
        ("nuevo@example.com", "Vendedor Nuevo", "Nuevo123!", "VENDEDOR", True),
    ]

    usuarios_dict: dict[str, Usuario] = {}
    for email, nombre, pwd, rol, debe_cambiar in usuarios_data:
        h = await hash_password(pwd)
        u = Usuario(
            email=email,
            nombre=nombre,
            password_hash=h,
            activo=True,
            debe_cambiar_password=debe_cambiar,
        )
        session.add(u)
        await session.flush()
        usuarios_dict[email] = u

        # Rol vigente sin vencimiento
        asig = AsignacionRol(
            usuario_id=u.id,
            rol=rol,
            otorgada_por=u.id,
            vence_en=None,
            revocada_en=None,
        )
        session.add(asig)

    admin_user = usuarios_dict["admin@example.com"]
    vendedor_user = usuarios_dict["vendedor@example.com"]

    # 3. Editoriales
    editoriales_data = ["Sudamericana", "Minotauro", "Emecé"]
    editoriales_dict: dict[str, Editorial] = {}
    for nom in editoriales_data:
        e = Editorial(nombre=nom)
        session.add(e)
        await session.flush()
        editoriales_dict[nom] = e

    # 4. Géneros
    generos_data = ["Novela", "Cuento", "Fantasía"]
    generos_dict: dict[str, Genero] = {}
    for nom in generos_data:
        g = Genero(nombre=nom)
        session.add(g)
        await session.flush()
        generos_dict[nom] = g

    # 5. Autores
    autores_data = [
        ("Julio Cortázar", "Argentina"),
        ("Jorge Luis Borges", "Argentina"),
        ("Adolfo Bioy Casares", "Argentina"),
        ("Silvina Ocampo", "Argentina"),
        ("Ernesto Sabato", "Argentina"),
        ("Ricardo Piglia", "Argentina"),
    ]
    autores_dict: dict[str, Autor] = {}
    for nom, nac in autores_data:
        a = Autor(nombre=nom, nacionalidad=nac)
        session.add(a)
        await session.flush()
        autores_dict[nom] = a

    # 6. Libros con stock inicial y movimiento
    libros_data = [
        ("978-950-07-0033-0", "Rayuela", Decimal("25000.00"), 11, "Sudamericana", "Novela", [("Julio Cortázar", 1)]),
        (
            "978-950-04-0012-1",
            "Antología de la literatura fantástica",
            Decimal("35000.00"),
            5,
            "Emecé",
            "Fantasía",
            [("Jorge Luis Borges", 1), ("Adolfo Bioy Casares", 2), ("Silvina Ocampo", 3)],
        ),
        ("978-950-04-0010-7", "Ficciones", Decimal("22000.00"), 10, "Emecé", "Cuento", [("Jorge Luis Borges", 1)]),
        ("978-950-07-0044-6", "Respiración artificial", Decimal("21000.00"), 3, "Sudamericana", "Novela", [("Ricardo Piglia", 1)]),
        ("978-950-07-0055-2", "Bestiario", Decimal("19000.00"), 1, "Sudamericana", "Cuento", [("Julio Cortázar", 1)]),
    ]

    libros_dict: dict[str, Libro] = {}
    for isbn, tit, prec, stock_ini, edit_nom, gen_nom, aut_list in libros_data:
        l = Libro(
            isbn=isbn,
            titulo=tit,
            precio=prec,
            stock=stock_ini,
            editorial_id=editoriales_dict[edit_nom].id,
            genero_id=generos_dict[gen_nom].id,
        )
        session.add(l)
        await session.flush()
        libros_dict[tit] = l

        for aut_nom, orden in aut_list:
            la = LibroAutor(
                libro_id=l.id,
                autor_id=autores_dict[aut_nom].id,
                rol="autor",
                orden=orden,
            )
            session.add(la)

        mov = MovimientoStock(
            libro_id=l.id,
            usuario_id=admin_user.id,
            cantidad=stock_ini,
            motivo="Stock inicial",
        )
        session.add(mov)

    # 7. Clientes
    c_lucia = Cliente(nombre="Lucía Fernández", email="lucia.fernandez@example.com", usuario_id=None)
    session.add(c_lucia)
    await session.flush()

    p_lucia = PerfilCliente(
        cliente_id=c_lucia.id,
        telefono="+54 11 4567-8901",
        direccion="Av. Corrientes 1234, CABA",
    )
    session.add(p_lucia)

    c_tomas = Cliente(nombre="Tomás Ríos", email="tomas.rios@example.com", usuario_id=None)
    session.add(c_tomas)

    c_ana = Cliente(nombre="Ana Paz", email="ana@example.com", usuario_id=usuarios_dict["ana@example.com"].id)
    session.add(c_ana)
    await session.flush()

    # 8. Venta 1 histórica (Lucía Fernández con vendedor@example.com)
    # Renglones: 1 Rayuela (25000) + 2 Ficciones (22000) = Total 69000.00
    l_rayuela = libros_dict["Rayuela"]
    l_ficciones = libros_dict["Ficciones"]

    v1 = Venta(
        cliente_id=c_lucia.id,
        fecha=datetime.now(timezone.utc),
        total=Decimal("69000.00"),
    )
    session.add(v1)
    await session.flush()

    r1 = RenglonVenta(venta_id=v1.id, libro_id=l_rayuela.id, cantidad=1, precio_unitario=Decimal("25000.00"))
    r2 = RenglonVenta(venta_id=v1.id, libro_id=l_ficciones.id, cantidad=2, precio_unitario=Decimal("22000.00"))
    session.add(r1)
    session.add(r2)

    # Descuento físico de stock
    l_rayuela.stock -= 1  # 11 -> 10
    l_ficciones.stock -= 2  # 10 -> 8
    await session.flush()

    # Movimientos de stock de salida
    mov_v1_1 = MovimientoStock(
        libro_id=l_rayuela.id,
        venta_id=v1.id,
        usuario_id=vendedor_user.id,
        cantidad=-1,
        motivo="Venta #1",
    )
    mov_v1_2 = MovimientoStock(
        libro_id=l_ficciones.id,
        venta_id=v1.id,
        usuario_id=vendedor_user.id,
        cantidad=-2,
        motivo="Venta #1",
    )
    session.add(mov_v1_1)
    session.add(mov_v1_2)

    # 9. Auditoría inicial en evento_seguridad
    ev_inicial = EventoSeguridad(
        actor="SISTEMA",
        accion="Carga de los datos iniciales",
        origen="seed.py",
        cuando=datetime.now(timezone.utc),
    )
    session.add(ev_inicial)

    await session.commit()
    logger.info("Carga de datos iniciales completada con éxito.")


async def main() -> None:
    settings = Settings()
    engine, session_factory = create_engine_and_session_factory(settings)
    async with session_factory() as session:
        await run_seed(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
