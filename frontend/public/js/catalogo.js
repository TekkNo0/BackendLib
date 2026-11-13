import { api, formatMoney, setFeedback } from "./api.js";

const LIMIT = 20;

export function initCatalogo() {
  const formBuscar = document.getElementById("form-buscar-catalogo");
  const inputTitulo = document.getElementById("filtro-titulo");
  const btnLimpiar = document.getElementById("btn-limpiar-filtro");
  const estadoEl = document.getElementById("estado-catalogo");
  const tbody = document.getElementById("tbody-catalogo");
  const btnPrev = document.getElementById("btn-cat-prev");
  const btnNext = document.getElementById("btn-cat-next");
  const infoPag = document.getElementById("info-cat-paginacion");
  const dialog = document.getElementById("dialog-libro");
  const dialogTitulo = document.getElementById("dialog-libro-titulo");
  const dialogCuerpo = document.getElementById("dialog-libro-cuerpo");

  const state = {
    titulo: "",
    offset: 0,
    total: 0,
  };

  function renderFilas(items) {
    tbody.replaceChildren();
    for (const libro of items) {
      const tr = document.createElement("tr");

      const tdTitulo = document.createElement("td");
      tdTitulo.textContent = libro.titulo;

      const tdIsbn = document.createElement("td");
      tdIsbn.textContent = libro.isbn;

      const tdEditorial = document.createElement("td");
      tdEditorial.textContent = libro.editorial ? libro.editorial.nombre : `ID ${libro.editorial_id}`;

      const tdGenero = document.createElement("td");
      tdGenero.textContent = libro.genero ? libro.genero.nombre : "Sin clasificar";

      const tdPrecio = document.createElement("td");
      tdPrecio.textContent = formatMoney(libro.precio);

      const tdStock = document.createElement("td");
      tdStock.textContent = String(libro.stock);

      const tdAcciones = document.createElement("td");
      const btnDetalle = document.createElement("button");
      btnDetalle.type = "button";
      btnDetalle.className = "btn btn-secondary btn-sm";
      btnDetalle.textContent = "Ver detalle";
      btnDetalle.addEventListener("click", () => abrirDetalleLibro(libro.id));
      tdAcciones.appendChild(btnDetalle);

      tr.append(tdTitulo, tdIsbn, tdEditorial, tdGenero, tdPrecio, tdStock, tdAcciones);
      tbody.appendChild(tr);
    }
  }

  function actualizarPaginacion() {
    const paginaActual = Math.floor(state.offset / LIMIT) + 1;
    const totalPaginas = Math.max(1, Math.ceil(state.total / LIMIT));
    infoPag.textContent = `Página ${paginaActual} de ${totalPaginas} (${state.total} libros)`;
    btnPrev.disabled = state.offset === 0;
    btnNext.disabled = state.offset + LIMIT >= state.total;
  }

  async function cargarCatalogo() {
    setFeedback(estadoEl, "Cargando catálogo...", "info");
    try {
      const data = await api.getLibros({
        titulo: state.titulo,
        limit: LIMIT,
        offset: state.offset,
      });
      state.total = data.total ?? data.items.length;
      renderFilas(data.items);
      actualizarPaginacion();

      if (data.items.length === 0) {
        if (state.titulo.trim()) {
          setFeedback(
            estadoEl,
            `No se encontraron coincidencias para "${state.titulo.trim()}".`,
            "info"
          );
        } else {
          setFeedback(estadoEl, "El catálogo está vacío.", "info");
        }
      } else {
        setFeedback(estadoEl, "", "info");
      }
    } catch (err) {
      tbody.replaceChildren();
      state.total = 0;
      actualizarPaginacion();
      setFeedback(
        estadoEl,
        err.isNetworkError ? err.message : `Error al cargar el catálogo: ${err.message}`,
        "error"
      );
    }
  }

  async function abrirDetalleLibro(id) {
    dialogTitulo.textContent = "Cargando detalle...";
    dialogCuerpo.replaceChildren();
    dialog.showModal();

    try {
      const libro = await api.getLibro(id);
      dialogTitulo.textContent = libro.titulo;

      const dl = document.createElement("dl");
      dl.className = "detail-list";

      const campos = [
        ["ID", String(libro.id)],
        ["ISBN", libro.isbn],
        ["Precio", formatMoney(libro.precio)],
        ["Stock", String(libro.stock)],
        ["Editorial", libro.editorial ? libro.editorial.nombre : `ID ${libro.editorial_id}`],
        ["Género", libro.genero ? libro.genero.nombre : "Sin clasificar"],
      ];

      for (const [label, val] of campos) {
        const row = document.createElement("div");
        row.className = "detail-row";
        const dt = document.createElement("dt");
        dt.textContent = `${label}:`;
        const dd = document.createElement("dd");
        dd.textContent = val;
        row.append(dt, dd);
        dl.appendChild(row);
      }

      const h3 = document.createElement("h3");
      h3.textContent = "Autores";
      const ul = document.createElement("ul");

      if (!libro.autores || libro.autores.length === 0) {
        const li = document.createElement("li");
        li.textContent = "Sin autores registrados.";
        ul.appendChild(li);
      } else {
        for (const autor of libro.autores) {
          const li = document.createElement("li");
          li.textContent = `${autor.nombre} (${autor.rol}, orden ${autor.orden})`;
          ul.appendChild(li);
        }
      }

      dialogCuerpo.replaceChildren(dl, h3, ul);
    } catch (err) {
      dialogTitulo.textContent = "Error";
      const p = document.createElement("p");
      p.textContent = err.message;
      dialogCuerpo.replaceChildren(p);
    }
  }

  formBuscar.addEventListener("submit", (e) => {
    e.preventDefault();
    state.titulo = inputTitulo.value.trim();
    state.offset = 0;
    cargarCatalogo();
  });

  btnLimpiar.addEventListener("click", () => {
    inputTitulo.value = "";
    state.titulo = "";
    state.offset = 0;
    cargarCatalogo();
  });

  btnPrev.addEventListener("click", () => {
    if (state.offset >= LIMIT) {
      state.offset -= LIMIT;
      cargarCatalogo();
    }
  });

  btnNext.addEventListener("click", () => {
    if (state.offset + LIMIT < state.total) {
      state.offset += LIMIT;
      cargarCatalogo();
    }
  });

  return { cargarCatalogo };
}
