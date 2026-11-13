import { api, formatMoney, setFeedback } from "./api.js";

const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

export function initAltas({ onLibroCreado, onClienteCreado }) {
  // Elementos de Libros
  const formLibro = document.getElementById("form-alta-libro");
  const selectEditorial = document.getElementById("libro-editorial");
  const selectGenero = document.getElementById("libro-genero");
  const selectAutor = document.getElementById("autor-selector");
  const inputAutorId = document.getElementById("autor-id-verificar");
  const btnVerificarAutor = document.getElementById("btn-verificar-autor");
  const autorVerificadoEl = document.getElementById("autor-verificado-nombre");
  const selectRol = document.getElementById("autor-rol");
  const inputOrden = document.getElementById("autor-orden");
  const btnAgregarAutor = document.getElementById("btn-agregar-autor");
  const listaAutoriasEl = document.getElementById("lista-autorias-borrador");
  const msgLibroEl = document.getElementById("mensaje-alta-libro");
  const btnSubmitLibro = document.getElementById("btn-submit-libro");
  const estadoLibrosLista = document.getElementById("estado-libros-lista");
  const tbodyLibros = document.getElementById("tbody-libros-registrados");

  // Elementos de Clientes
  const formCliente = document.getElementById("form-alta-cliente");
  const msgClienteEl = document.getElementById("mensaje-alta-cliente");
  const btnSubmitCliente = document.getElementById("btn-submit-cliente");
  const formBuscarClienteId = document.getElementById("form-buscar-cliente-id");
  const inputClienteIdBuscar = document.getElementById("cliente-id-buscar");
  const resultadoClienteId = document.getElementById("resultado-cliente-id");
  const estadoClientesLista = document.getElementById("estado-clientes-lista");
  const tbodyClientes = document.getElementById("tbody-clientes");

  let autorVerificado = null;
  let autoriasBorrador = [];

  function renderAutoriasBorrador() {
    listaAutoriasEl.replaceChildren();
    for (const item of autoriasBorrador) {
      const li = document.createElement("li");
      li.className = "chip-item";

      const span = document.createElement("span");
      span.textContent = `${item.nombre} (ID ${item.autor_id}) · ${item.rol} · orden ${item.orden}`;

      const btnQuitar = document.createElement("button");
      btnQuitar.type = "button";
      btnQuitar.className = "btn btn-secondary btn-sm";
      btnQuitar.textContent = "Quitar";
      btnQuitar.addEventListener("click", () => {
        autoriasBorrador = autoriasBorrador.filter((a) => a.autor_id !== item.autor_id);
        renderAutoriasBorrador();
      });

      li.append(span, btnQuitar);
      listaAutoriasEl.appendChild(li);
    }
  }

  async function cargarOpcionesLibro() {
    try {
      const [edData, genData, autData] = await Promise.all([
        api.getEditoriales(100, 0),
        api.getGeneros(100, 0),
        api.getAutores(100, 0),
      ]);

      selectEditorial.replaceChildren();
      const optDefaultEd = document.createElement("option");
      optDefaultEd.value = "";
      optDefaultEd.textContent = "Seleccioná una editorial...";
      selectEditorial.appendChild(optDefaultEd);
      for (const ed of edData.items) {
        const opt = document.createElement("option");
        opt.value = String(ed.id);
        opt.textContent = ed.nombre;
        selectEditorial.appendChild(opt);
      }

      selectGenero.replaceChildren();
      const optSinGenero = document.createElement("option");
      optSinGenero.value = "";
      optSinGenero.textContent = "Sin clasificar";
      selectGenero.appendChild(optSinGenero);
      for (const gen of genData.items) {
        const opt = document.createElement("option");
        opt.value = String(gen.id);
        opt.textContent = gen.nombre;
        selectGenero.appendChild(opt);
      }

      selectAutor.replaceChildren();
      const optDefaultAut = document.createElement("option");
      optDefaultAut.value = "";
      optDefaultAut.textContent = "Seleccioná un autor...";
      selectAutor.appendChild(optDefaultAut);
      for (const aut of autData.items) {
        const opt = document.createElement("option");
        opt.value = String(aut.id);
        opt.textContent = `${aut.nombre} (ID ${aut.id})`;
        selectAutor.appendChild(opt);
      }
    } catch (err) {
      setFeedback(msgLibroEl, `No se pudieron cargar editoriales/géneros/autores: ${err.message}`, "error");
    }
  }

  async function cargarListaLibrosRecientes() {
    setFeedback(estadoLibrosLista, "Cargando libros...", "info");
    try {
      const data = await api.getLibros({ limit: 20, offset: 0 });
      tbodyLibros.replaceChildren();
      for (const libro of data.items) {
        const tr = document.createElement("tr");
        const c1 = document.createElement("td");
        c1.textContent = String(libro.id);
        const c2 = document.createElement("td");
        c2.textContent = libro.titulo;
        const c3 = document.createElement("td");
        c3.textContent = libro.isbn;
        const c4 = document.createElement("td");
        c4.textContent = formatMoney(libro.precio);
        const c5 = document.createElement("td");
        c5.textContent = String(libro.stock);
        tr.append(c1, c2, c3, c4, c5);
        tbodyLibros.appendChild(tr);
      }
      setFeedback(estadoLibrosLista, data.items.length === 0 ? "No hay libros registrados." : "", "info");
    } catch (err) {
      setFeedback(estadoLibrosLista, err.message, "error");
    }
  }

  async function cargarListaClientes() {
    setFeedback(estadoClientesLista, "Cargando clientes...", "info");
    try {
      const data = await api.getClientes(100, 0);
      tbodyClientes.replaceChildren();
      for (const cli of data.items) {
        const tr = document.createElement("tr");
        const c1 = document.createElement("td");
        c1.textContent = String(cli.id);
        const c2 = document.createElement("td");
        c2.textContent = cli.nombre;
        const c3 = document.createElement("td");
        c3.textContent = cli.email;
        tr.append(c1, c2, c3);
        tbodyClientes.appendChild(tr);
      }
      setFeedback(estadoClientesLista, data.items.length === 0 ? "No hay clientes registrados." : "", "info");
    } catch (err) {
      setFeedback(estadoClientesLista, err.message, "error");
    }
  }

  btnVerificarAutor.addEventListener("click", async () => {
    const idVal = Number(inputAutorId.value);
    if (!Number.isInteger(idVal) || idVal <= 0) {
      autorVerificado = null;
      autorVerificadoEl.textContent = "Ingresá un ID de autor entero positivo.";
      return;
    }
    autorVerificadoEl.textContent = "Consultando autor...";
    try {
      const autor = await api.getAutor(idVal);
      autorVerificado = autor;
      selectAutor.value = String(autor.id);
      autorVerificadoEl.textContent = `Encontrado: ${autor.nombre} (${autor.nacionalidad})`;
    } catch (err) {
      autorVerificado = null;
      autorVerificadoEl.textContent = err.message;
    }
  });

  btnAgregarAutor.addEventListener("click", async () => {
    setFeedback(msgLibroEl, "", "info");
    let autorId = Number(selectAutor.value);
    let nombre = "";

    if (autorId > 0) {
      const opt = selectAutor.options[selectAutor.selectedIndex];
      nombre = opt ? opt.textContent.replace(/\s*\(ID \d+\)$/, "") : `Autor #${autorId}`;
    } else if (autorVerificado) {
      autorId = autorVerificado.id;
      nombre = autorVerificado.nombre;
    } else {
      setFeedback(msgLibroEl, "Seleccioná un autor o verificalo por ID antes de agregar.", "error");
      return;
    }

    const rol = selectRol.value;
    const orden = Number(inputOrden.value);
    if (!Number.isInteger(orden) || orden < 1) {
      setFeedback(msgLibroEl, "El orden de autoría debe ser un entero >= 1.", "error");
      return;
    }

    if (autoriasBorrador.some((a) => a.autor_id === autorId)) {
      setFeedback(msgLibroEl, "Ese autor ya fue agregado al libro.", "error");
      return;
    }

    autoriasBorrador.push({ autor_id: autorId, nombre, rol, orden });
    inputOrden.value = String(autoriasBorrador.length + 1);
    renderAutoriasBorrador();
  });

  formLibro.addEventListener("submit", async (e) => {
    e.preventDefault();
    setFeedback(msgLibroEl, "", "info");

    const titulo = document.getElementById("libro-titulo").value.trim();
    const isbn = document.getElementById("libro-isbn").value.trim();
    const precio = Number(document.getElementById("libro-precio").value);
    const stockRaw = document.getElementById("libro-stock").value;
    const stock = Number(stockRaw);
    const editorialId = Number(selectEditorial.value);
    const generoRaw = selectGenero.value;
    const generoId = generoRaw ? Number(generoRaw) : null;

    if (!titulo) {
      setFeedback(msgLibroEl, "El título es obligatorio.", "error");
      return;
    }
    if (!isbn) {
      setFeedback(msgLibroEl, "El ISBN es obligatorio.", "error");
      return;
    }
    if (!Number.isFinite(precio) || precio <= 0) {
      setFeedback(msgLibroEl, "El precio debe ser un número positivo.", "error");
      return;
    }
    if (stockRaw === "" || !Number.isInteger(stock) || stock < 0) {
      setFeedback(msgLibroEl, "El stock inicial debe ser un entero >= 0.", "error");
      return;
    }
    if (!Number.isInteger(editorialId) || editorialId <= 0) {
      setFeedback(msgLibroEl, "Seleccioná una editorial válida.", "error");
      return;
    }
    if (autoriasBorrador.length === 0) {
      setFeedback(msgLibroEl, "Agregá al menos un autor al libro.", "error");
      return;
    }

    btnSubmitLibro.disabled = true;
    try {
      const creado = await api.crearLibro({
        titulo,
        isbn,
        precio,
        stock_inicial: stock,
        editorial_id: editorialId,
        genero_id: generoId,
        autores: autoriasBorrador.map(({ autor_id, rol, orden }) => ({
          autor_id,
          rol,
          orden,
        })),
      });

      formLibro.reset();
      document.getElementById("libro-stock").value = "0";
      inputOrden.value = "1";
      autoriasBorrador = [];
      autorVerificado = null;
      autorVerificadoEl.textContent = "";
      renderAutoriasBorrador();

      setFeedback(msgLibroEl, `Libro "${creado.titulo}" registrado (ID ${creado.id}).`, "success");
      await cargarListaLibrosRecientes();
      if (onLibroCreado) onLibroCreado(creado);
    } catch (err) {
      setFeedback(msgLibroEl, err.message, "error");
    } finally {
      btnSubmitLibro.disabled = false;
    }
  });

  formCliente.addEventListener("submit", async (e) => {
    e.preventDefault();
    setFeedback(msgClienteEl, "", "info");

    const nombre = document.getElementById("cliente-nombre").value.trim();
    const email = document.getElementById("cliente-email").value.trim();

    if (!nombre) {
      setFeedback(msgClienteEl, "El nombre completo es obligatorio.", "error");
      return;
    }
    if (!EMAIL_RE.test(email)) {
      setFeedback(msgClienteEl, "Ingresá un email válido.", "error");
      return;
    }

    btnSubmitCliente.disabled = true;
    try {
      const creado = await api.crearCliente({ nombre, email });
      formCliente.reset();
      setFeedback(
        msgClienteEl,
        `Cliente "${creado.nombre}" registrado (ID ${creado.id}).`,
        "success"
      );
      await cargarListaClientes();
      if (onClienteCreado) onClienteCreado(creado);
    } catch (err) {
      setFeedback(msgClienteEl, err.message, "error");
    } finally {
      btnSubmitCliente.disabled = false;
    }
  });

  formBuscarClienteId.addEventListener("submit", async (e) => {
    e.preventDefault();
    const idVal = Number(inputClienteIdBuscar.value);
    if (!Number.isInteger(idVal) || idVal <= 0) {
      resultadoClienteId.textContent = "Ingresá un ID de cliente entero positivo.";
      return;
    }
    resultadoClienteId.textContent = "Consultando...";
    try {
      const cli = await api.getCliente(idVal);
      resultadoClienteId.textContent = `ID ${cli.id}: ${cli.nombre} (${cli.email})`;
    } catch (err) {
      resultadoClienteId.textContent = err.message;
    }
  });

  return {
    cargarOpcionesLibro,
    cargarListaLibrosRecientes,
    cargarListaClientes,
  };
}
