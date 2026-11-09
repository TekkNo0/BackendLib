from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.paginacion import PaginatedResponse, PaginationParams, paginate
from app.core.unit_of_work import UnitOfWork
from app.modules.autores.repository import AutorRepository
from app.modules.editoriales.repository import EditorialRepository
from app.modules.editoriales.schemas import EditorialResponse
from app.modules.generos.repository import GeneroRepository
from app.modules.generos.schemas import GeneroResponse
from app.modules.libros.models import Libro, LibroAutor
from app.modules.libros.repository import LibroRepository
from app.modules.libros.schemas import (
    AutorEnLibroResponse,
    LibroCreateRequest,
    LibroDetalleResponse,
    LibroUpdateRequest,
    MovimientoStockResponse,
    ReponerStockRequest,
)
from app.modules.ventas.models import MovimientoStock
from app.modules.ventas.repository import MovimientoStockRepository


class LibroService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.libro_repo = LibroRepository(session)
        self.movimiento_repo = MovimientoStockRepository(session)
        self.editorial_repo = EditorialRepository(session)
        self.genero_repo = GeneroRepository(session)
        self.autor_repo = AutorRepository(session)
        self.uow = UnitOfWork(session)

    def _map_libro_detalle(self, libro: Libro) -> LibroDetalleResponse:
        autores: list[AutorEnLibroResponse] = []
        if libro.autores_asociados:
            for assoc in sorted(libro.autores_asociados, key=lambda x: x.orden):
                if assoc.autor:
                    autores.append(
                        AutorEnLibroResponse(
                            id=assoc.autor.id,
                            nombre=assoc.autor.nombre,
                            nacionalidad=assoc.autor.nacionalidad,
                            rol=assoc.rol,
                            orden=assoc.orden,
                        )
                    )
        return LibroDetalleResponse(
            id=libro.id,
            isbn=libro.isbn,
            titulo=libro.titulo,
            precio=libro.precio,
            stock=libro.stock,
            editorial_id=libro.editorial_id,
            genero_id=libro.genero_id,
            borrado_en=libro.borrado_en,
            editorial=EditorialResponse.model_validate(libro.editorial) if libro.editorial else None,
            genero=GeneroResponse.model_validate(libro.genero) if libro.genero else None,
            autores=autores,
        )

    async def crear_libro(
        self, data: LibroCreateRequest, usuario_id: int
    ) -> LibroDetalleResponse:
        editorial = await self.editorial_repo.get_by_id(data.editorial_id)
        if not editorial:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Editorial no encontrada")

        genero = await self.genero_repo.get_by_id(data.genero_id)
        if not genero:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Género no encontrado")

        autores = await self.autor_repo.get_by_ids(data.autores_ids)
        if len(autores) != len(set(data.autores_ids)):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uno o más autores no existen")

        existente = await self.libro_repo.get_vigente_by_isbn(data.isbn)
        if existente:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Ya existe un libro vigente con el ISBN {data.isbn} (RN-01)",
            )

        async with self.uow:
            libro = Libro(
                isbn=data.isbn,
                titulo=data.titulo,
                precio=data.precio,
                stock=data.stock_inicial,
                editorial_id=data.editorial_id,
                genero_id=data.genero_id,
            )
            await self.libro_repo.add(libro)

            for idx, autor_id in enumerate(data.autores_ids, start=1):
                assoc = LibroAutor(
                    libro_id=libro.id,
                    autor_id=autor_id,
                    rol="autor",
                    orden=idx,
                )
                self.session.add(assoc)

            if data.stock_inicial > 0:
                movimiento = MovimientoStock(
                    libro_id=libro.id,
                    usuario_id=usuario_id,
                    cantidad=data.stock_inicial,
                    motivo="Stock inicial",
                )
                await self.movimiento_repo.add(movimiento)

        libro_cargado = await self.libro_repo.get_detalle_vigente(libro.id)
        return self._map_libro_detalle(libro_cargado)

    async def actualizar_libro(
        self, libro_id: int, data: LibroUpdateRequest
    ) -> LibroDetalleResponse:
        libro = await self.libro_repo.get_detalle_vigente(libro_id)
        if not libro:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Libro no encontrado")

        async with self.uow:
            if data.titulo is not None:
                libro.titulo = data.titulo
            if data.precio is not None:
                libro.precio = data.precio
            await self.libro_repo.update(libro)

        libro_cargado = await self.libro_repo.get_detalle_vigente(libro_id)
        return self._map_libro_detalle(libro_cargado)

    async def borrar_libro(self, libro_id: int) -> None:
        libro = await self.libro_repo.get_detalle_any(libro_id)
        if not libro or libro.borrado_en is not None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Libro no encontrado o ya descatalogado",
            )

        async with self.uow:
            await self.libro_repo.soft_delete(libro)

    async def reponer_stock(
        self, libro_id: int, data: ReponerStockRequest, usuario_id: int
    ) -> LibroDetalleResponse:
        libro = await self.libro_repo.get_detalle_any(libro_id)
        if not libro:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Libro no encontrado")

        if libro.borrado_en is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No se puede reponer stock de un libro descatalogado (RN-13)",
            )

        async with self.uow:
            libro.stock += data.cantidad
            await self.libro_repo.update(libro)

            movimiento = MovimientoStock(
                libro_id=libro.id,
                usuario_id=usuario_id,
                cantidad=data.cantidad,
                motivo=data.motivo,
            )
            await self.movimiento_repo.add(movimiento)

        libro_cargado = await self.libro_repo.get_detalle_vigente(libro_id)
        return self._map_libro_detalle(libro_cargado)

    async def obtener_libro(self, libro_id: int) -> LibroDetalleResponse:
        libro = await self.libro_repo.get_detalle_vigente(libro_id)
        if not libro:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Libro no encontrado")
        return self._map_libro_detalle(libro)

    async def listar_catalogo(
        self, titulo: str | None, params: PaginationParams
    ) -> PaginatedResponse[LibroDetalleResponse]:
        items, total = await self.libro_repo.listar_catalogo(
            titulo=titulo, offset=params.offset, limit=params.limit
        )
        mapped = [self._map_libro_detalle(item) for item in items]
        return paginate(mapped, total, params)

    async def listar_movimientos(
        self, libro_id: int, params: PaginationParams
    ) -> PaginatedResponse[MovimientoStockResponse]:
        libro = await self.libro_repo.get_detalle_any(libro_id)
        if not libro:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Libro no encontrado")

        items, total = await self.movimiento_repo.listar_por_libro(
            libro_id=libro_id, offset=params.offset, limit=params.limit
        )
        mapped = [MovimientoStockResponse.model_validate(item) for item in items]
        return paginate(mapped, total, params)

    async def listar_por_editorial(
        self, editorial_id: int, params: PaginationParams
    ) -> PaginatedResponse[LibroDetalleResponse]:
        editorial = await self.editorial_repo.get_by_id(editorial_id)
        if not editorial:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Editorial no encontrada")

        items, total = await self.libro_repo.listar_por_editorial(
            editorial_id=editorial_id, offset=params.offset, limit=params.limit
        )
        mapped = [self._map_libro_detalle(item) for item in items]
        return paginate(mapped, total, params)

    async def listar_por_genero(
        self, genero_id: int, params: PaginationParams
    ) -> PaginatedResponse[LibroDetalleResponse]:
        genero = await self.genero_repo.get_by_id(genero_id)
        if not genero:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Género no encontrado")

        items, total = await self.libro_repo.listar_por_genero(
            genero_id=genero_id, offset=params.offset, limit=params.limit
        )
        mapped = [self._map_libro_detalle(item) for item in items]
        return paginate(mapped, total, params)

    async def listar_por_autor(
        self, autor_id: int, params: PaginationParams
    ) -> PaginatedResponse[LibroDetalleResponse]:
        autor = await self.autor_repo.get_by_id(autor_id)
        if not autor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Autor no encontrado")

        items, total = await self.libro_repo.listar_por_autor(
            autor_id=autor_id, offset=params.offset, limit=params.limit
        )
        mapped = [self._map_libro_detalle(item) for item in items]
        return paginate(mapped, total, params)
