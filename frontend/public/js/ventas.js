import { api, formatMoney, setFeedback } from "./api.js";

const HISTORIAL_LIMIT = 20;

export function initVentas({ onVentaConfirmada }) {
  // Elementos de Nueva Venta
  const formVenta = document.getElementById("form-venta");
  const selectCliente = document.getElementById("venta-cliente");
  const inputClienteDirecto = document.getElementById("venta-cliente-id-directo");
  const btnBuscarCliente = document.getElementById("btn-venta-buscar-cliente");
  const selectLibro = document.getElementById("venta-libro");
  const inputCantidad = document.getElementById("venta-cantidad");
  const btnAgregarRenglon = document.getElementById("btn-agregar-renglon");
  const tbodyBorrador = document.getElementById("tbody-borrador-venta");
  const totalEstimadoEl = document.getElementById("venta-total-estimado");
  const msgVentaEl = document.getElementById("mensaje-venta");
  const btnConfirmarVenta = document.getElementById("btn-confirmar-venta");
  const resumenConfirmadaEl = document.getElementById("resumen-venta-confirmada");

  // Elementos de Historial
  const btnRefrescarHist = document.getElementById("btn-refrescar-historial");
  const estadoHistEl = document.getElementById("estado-historial");
  const tbodyHistorial = document.getElementById("tbody-historial");
  const btnHistPrev = document.getElementById("btn-hist-prev");
  const btnHistNext = document.getElementById("btn-hist-next");
  const infoHistPag = document.getElementById("info-hist-paginacion");
  const dialogVenta = document.getElementById("dialog-venta");
  const dialogVentaTitulo = document.getElementById("dialog-venta-titulo");
  const dialogVentaCuerpo = document.getElementById("dialog-venta-cuerpo");

  let catalogoCache = new Map();
  let borradorRenglones = [];
  const histState = { offset: 0, total: 0 };

  async function cargarSelectoresVenta() {
    try {
      const [clientesData, librosData] = await Promise.all([
        api.getClientes(100, 0),
        api.getLibros({ limit: 100, offset: 0 }),
      ]);

      const prevCliente = selectCliente.value;
      selectCliente.replaceChildren();
      const optC0 = document.createElement("option");
      optC0.value = "";
      optC0.textContent = "Seleccioná un cliente...";
      selectCliente.appendChild(optC0);
      for (const c of clientesData.items) {
        const opt = document.createElement("option");
        opt.value = String(c.id);
        opt.textContent = `${c.nombre} (${c.email})`;
        selectCliente.appendChild(opt);
      }
      if (prevCliente) selectCliente.value = prevCliente;

      catalogoCache = new Map();
      selectLibro.replaceChildren();
      const optL0 = document.createElement("option");
      optL0.value = "";
      optL0.textContent = "Seleccioná un libro...";
      selectLibro.appendChild(optL0);
      for (const l of librosData.items) {
        catalogoCache.set(l.id, l);
        const opt = document.createElement("option");
        opt.value = String(l.id);
        opt.textContent = `${l.titulo} — ${formatMoney(l.precio)} (stock: ${l.stock})`;
        selectLibro.appendChild(opt);
      }
    } catch (err) {
      setFeedback(msgVentaEl, `Error cargando clientes/libros: ${err.message}`, "error");
    }
  }

  function renderBorrador() {
    tbodyBorrador.replaceChildren();
    let total = 0;

    for (const renglon of borradorRenglones) {
      const subtotal = Number(renglon.precio_unitario) * renglon.cantidad;
      total += subtotal;

      const tr = document.createElement("tr");

      const tdLibro = document.createElement("td");
      tdLibro.textContent = renglon.titulo;

      const tdPrecio = document.createElement("td");
      tdPrecio.textContent = formatMoney(renglon.precio_unitario);

      const tdCant = document.createElement("td");
      const inputCant = document.createElement("input");
      inputCant.type = "number";
      inputCant.min = "1";
      inputCant.step = "1";
      inputCant.className = "qty-input";
      inputCant.value = String(renglon.cantidad);
      inputCant.setAttribute("aria-label", `Cantidad de ${renglon.titulo}`);
      inputCant.addEventListener("change", () => {
        const val = Number(inputCant.value);
        if (!Number.isInteger(val) || val <= 0) {
          inputCant.value = String(renglon.cantidad);
          setFeedback(msgVentaEl, "La cantidad debe ser un entero positivo.", "error");
          return;
        }
        renglon.cantidad = val;
        setFeedback(msgVentaEl, "", "info");
        renderBorrador();
      });
      tdCant.appendChild(inputCant);

      const tdSub = document.createElement("td");
      tdSub.textContent = formatMoney(subtotal);

      const tdQuitar = document.createElement("td");
      const btnQuitar = document.createElement("button");
      btnQuitar.type = "button";
      btnQuitar.className = "btn btn-secondary btn-sm";
      btnQuitar.textContent = "Quitar";
      btnQuitar.addEventListener("click", () => {
        borradorRenglones = borradorRenglones.filter((r) => r.libro_id !== renglon.libro_id);
        renderBorrador();
      });
      tdQuitar.appendChild(btnQuitar);

      tr.append(tdLibro, tdPrecio, tdCant, tdSub, tdQuitar);
      tbodyBorrador.appendChild(tr);
    }

    totalEstimadoEl.textContent = formatMoney(total);
  }

  function renderResumenVenta(venta, container) {
    container.className = "";
    container.replaceChildren();

    const dl = document.createElement("dl");
    dl.className = "detail-list";

    const fechaStr = venta.fecha ? new Date(venta.fecha).toLocaleString("es-AR") : "-";
    const clienteStr = venta.cliente
      ? `${venta.cliente.nombre} (${venta.cliente.email})`
      : `Cliente ID ${venta.cliente_id}`;

    const cabecera = [
      ["Venta #", String(venta.id)],
      ["Fecha", fechaStr],
      ["Cliente", clienteStr],
      ["Total confirmado", formatMoney(venta.total)],
    ];

    for (const [label, val] of cabecera) {
      const row = document.createElement("div");
      row.className = "detail-row";
      const dt = document.createElement("dt");
      dt.textContent = `${label}:`;
      const dd = document.createElement("dd");
      dd.textContent = val;
      row.append(dt, dd);
      dl.appendChild(row);
    }

    const wrap = document.createElement("div");
    wrap.className = "table-wrapper";
    const table = document.createElement("table");
    const thead = document.createElement("thead");
    const headRow = document.createElement("tr");
    for (const col of ["Libro", "P. Unitario", "Cant.", "Subtotal"]) {
      const th = document.createElement("th");
      th.scope = "col";
      th.textContent = col;
      headRow.appendChild(th);
    }
    thead.appendChild(headRow);

    const tbody = document.createElement("tbody");
    for (const r of venta.renglones || []) {
      const tr = document.createElement("tr");
      const subtotal = r.subtotal ?? Number(r.precio_unitario) * r.cantidad;

      const c1 = document.createElement("td");
      c1.textContent = r.libro ? r.libro.titulo : `Libro #${r.libro_id}`;
      const c2 = document.createElement("td");
      c2.textContent = formatMoney(r.precio_unitario);
      const c3 = document.createElement("td");
      c3.textContent = String(r.cantidad);
      const c4 = document.createElement("td");
      c4.textContent = formatMoney(subtotal);

      tr.append(c1, c2, c3, c4);
      tbody.appendChild(tr);
    }

    table.append(thead, tbody);
    wrap.appendChild(table);
    container.append(dl, wrap);
  }

  btnBuscarCliente.addEventListener("click", async () => {
    setFeedback(msgVentaEl, "", "info");
    const idVal = Number(inputClienteDirecto.value);
    if (!Number.isInteger(idVal) || idVal <= 0) {
      setFeedback(msgVentaEl, "Ingresá un ID de cliente entero positivo.", "error");
      return;
    }
    try {
      const cli = await api.getCliente(idVal);
      let opt = Array.from(selectCliente.options).find((o) => Number(o.value) === cli.id);
      if (!opt) {
        opt = document.createElement("option");
        opt.value = String(cli.id);
        opt.textContent = `${cli.nombre} (${cli.email})`;
        selectCliente.appendChild(opt);
      }
      selectCliente.value = String(cli.id);
      setFeedback(msgVentaEl, `Cliente seleccionado: ${cli.nombre}.`, "success");
    } catch (err) {
      setFeedback(msgVentaEl, err.message, "error");
    }
  });

  btnAgregarRenglon.addEventListener("click", () => {
    setFeedback(msgVentaEl, "", "info");
    const libroId = Number(selectLibro.value);
    const cantidad = Number(inputCantidad.value);

    if (!Number.isInteger(libroId) || libroId <= 0) {
      setFeedback(msgVentaEl, "Seleccioná un libro del catálogo.", "error");
      return;
    }
    if (!Number.isInteger(cantidad) || cantidad <= 0) {
      setFeedback(msgVentaEl, "La cantidad debe ser un entero positivo.", "error");
      return;
    }
    if (borradorRenglones.some((r) => r.libro_id === libroId)) {
      setFeedback(
        msgVentaEl,
        "Ese libro ya está en la venta. Editá su cantidad en la tabla.",
        "error"
      );
      return;
    }

    const libro = catalogoCache.get(libroId);
    borradorRenglones.push({
      libro_id: libroId,
      titulo: libro ? libro.titulo : `Libro #${libroId}`,
      precio_unitario: libro ? libro.precio : 0,
      cantidad,
    });
    inputCantidad.value = "1";
    renderBorrador();
  });

  formVenta.addEventListener("submit", async (e) => {
    e.preventDefault();
    setFeedback(msgVentaEl, "", "info");

    const clienteId = Number(selectCliente.value);
    if (!Number.isInteger(clienteId) || clienteId <= 0) {
      setFeedback(msgVentaEl, "Seleccioná un cliente antes de confirmar la venta.", "error");
      return;
    }
    if (borradorRenglones.length === 0) {
      setFeedback(msgVentaEl, "Agregá al menos un renglón a la venta.", "error");
      return;
    }
    for (const r of borradorRenglones) {
      if (!Number.isInteger(r.cantidad) || r.cantidad <= 0) {
        setFeedback(msgVentaEl, "Todas las cantidades deben ser enteros positivos.", "error");
        return;
      }
    }

    btnConfirmarVenta.disabled = true;
    try {
      const ventaConfirmada = await api.crearVenta({
        cliente_id: clienteId,
        renglones: borradorRenglones.map(({ libro_id, cantidad }) => ({
          libro_id,
          cantidad,
        })),
      });

      borradorRenglones = [];
      selectCliente.value = "";
      selectLibro.value = "";
      inputCantidad.value = "1";
      renderBorrador();

      renderResumenVenta(ventaConfirmada, resumenConfirmadaEl);
      setFeedback(
        msgVentaEl,
        `Venta #${ventaConfirmada.id} confirmada por ${formatMoney(ventaConfirmada.total)}.`,
        "success"
      );

      await Promise.all([cargarHistorial(), cargarSelectoresVenta()]);
      if (onVentaConfirmada) onVentaConfirmada(ventaConfirmada);
    } catch (err) {
      // Conserva el borrador cuando se rechaza la operación (409/422/red)
      setFeedback(msgVentaEl, err.message, "error");
    } finally {
      btnConfirmarVenta.disabled = false;
    }
  });

  function actualizarPaginacionHistorial() {
    const paginaActual = Math.floor(histState.offset / HISTORIAL_LIMIT) + 1;
    const totalPaginas = Math.max(1, Math.ceil(histState.total / HISTORIAL_LIMIT));
    infoHistPag.textContent = `Página ${paginaActual} de ${totalPaginas} (${histState.total} ventas)`;
    btnHistPrev.disabled = histState.offset === 0;
    btnHistNext.disabled = histState.offset + HISTORIAL_LIMIT >= histState.total;
  }

  async function cargarHistorial() {
    setFeedback(estadoHistEl, "Cargando historial de ventas...", "info");
    try {
      const data = await api.getVentas(HISTORIAL_LIMIT, histState.offset);
      histState.total = data.total ?? data.items.length;
      tbodyHistorial.replaceChildren();

      for (const v of data.items) {
        const tr = document.createElement("tr");

        const tdId = document.createElement("td");
        tdId.textContent = `#${v.id}`;

        const tdFecha = document.createElement("td");
        tdFecha.textContent = v.fecha ? new Date(v.fecha).toLocaleString("es-AR") : "-";

        const tdCliente = document.createElement("td");
        tdCliente.textContent = v.cliente ? v.cliente.nombre : `Cliente #${v.cliente_id}`;

        const tdTotal = document.createElement("td");
        tdTotal.textContent = formatMoney(v.total);

        const tdAccion = document.createElement("td");
        const btnDet = document.createElement("button");
        btnDet.type = "button";
        btnDet.className = "btn btn-secondary btn-sm";
        btnDet.textContent = "Ver detalle";
        btnDet.addEventListener("click", () => abrirDetalleVenta(v.id));
        tdAccion.appendChild(btnDet);

        tr.append(tdId, tdFecha, tdCliente, tdTotal, tdAccion);
        tbodyHistorial.appendChild(tr);
      }

      actualizarPaginacionHistorial();
      setFeedback(
        estadoHistEl,
        data.items.length === 0 ? "No hay ventas registradas todavía." : "",
        "info"
      );
    } catch (err) {
      tbodyHistorial.replaceChildren();
      setFeedback(estadoHistEl, err.message, "error");
    }
  }

  async function abrirDetalleVenta(id) {
    dialogVentaTitulo.textContent = `Venta #${id}`;
    dialogVentaCuerpo.replaceChildren();
    dialogVenta.showModal();

    try {
      const venta = await api.getVenta(id);
      renderResumenVenta(venta, dialogVentaCuerpo);
    } catch (err) {
      const p = document.createElement("p");
      p.textContent = err.message;
      dialogVentaCuerpo.replaceChildren(p);
    }
  }

  btnRefrescarHist.addEventListener("click", cargarHistorial);
  btnHistPrev.addEventListener("click", () => {
    if (histState.offset >= HISTORIAL_LIMIT) {
      histState.offset -= HISTORIAL_LIMIT;
      cargarHistorial();
    }
  });
  btnHistNext.addEventListener("click", () => {
    if (histState.offset + HISTORIAL_LIMIT < histState.total) {
      histState.offset += HISTORIAL_LIMIT;
      cargarHistorial();
    }
  });

  return {
    cargarSelectoresVenta,
    cargarHistorial,
  };
}
