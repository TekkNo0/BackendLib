import { initAltas } from "./altas.js";
import { initCatalogo } from "./catalogo.js";
import { initVentas } from "./ventas.js";

function setupDialogFallbacks() {
  if ("closedBy" in HTMLDialogElement.prototype) return;

  for (const dialog of document.querySelectorAll("dialog")) {
    dialog.addEventListener("click", (event) => {
      if (event.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      const isInside =
        rect.top <= event.clientY &&
        event.clientY <= rect.top + rect.height &&
        rect.left <= event.clientX &&
        event.clientX <= rect.left + rect.width;
      if (!isInside) {
        dialog.close();
      }
    });
  }
}

function setupNavigation() {
  const navButtons = Array.from(document.querySelectorAll(".nav-btn"));
  const sections = Array.from(document.querySelectorAll(".view-section"));

  function showView(viewName) {
    for (const btn of navButtons) {
      const active = btn.dataset.view === viewName;
      btn.classList.toggle("is-active", active);
      if (active) {
        btn.setAttribute("aria-current", "page");
      } else {
        btn.removeAttribute("aria-current");
      }
    }

    for (const sec of sections) {
      sec.hidden = sec.id !== `vista-${viewName}`;
    }
  }

  for (const btn of navButtons) {
    btn.addEventListener("click", () => showView(btn.dataset.view));
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  setupDialogFallbacks();
  setupNavigation();

  const catalogo = initCatalogo();
  const ventas = initVentas({
    onVentaConfirmada: () => {
      catalogo.cargarCatalogo();
    },
  });
  const altas = initAltas({
    onLibroCreado: () => {
      catalogo.cargarCatalogo();
      ventas.cargarSelectoresVenta();
    },
    onClienteCreado: () => {
      ventas.cargarSelectoresVenta();
    },
  });

  await Promise.all([
    catalogo.cargarCatalogo(),
    altas.cargarOpcionesLibro(),
    altas.cargarListaLibrosRecientes(),
    altas.cargarListaClientes(),
    ventas.cargarSelectoresVenta(),
    ventas.cargarHistorial(),
  ]);
});
