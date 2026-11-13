export const API_BASE = "/api";

export class ApiError extends Error {
  constructor(message, status = 0, isNetworkError = false) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.isNetworkError = isNetworkError;
  }
}

function extractErrorMessage(payload, status) {
  if (!payload) {
    return `Error HTTP ${status}`;
  }
  if (typeof payload.detail === "string") {
    return payload.detail;
  }
  if (Array.isArray(payload.detail)) {
    return payload.detail
      .map((item) => {
        const loc = Array.isArray(item.loc) ? item.loc.slice(1).join(".") : "";
        return loc ? `${loc}: ${item.msg}` : item.msg;
      })
      .join(" | ");
  }
  return `Error HTTP ${status}`;
}

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const headers = { ...(options.headers || {}) };
  if (options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  let response;
  try {
    response = await fetch(url, { ...options, headers });
  } catch (_err) {
    throw new ApiError(
      "No se pudo conectar con el servidor. Verificá tu conexión o el estado de la API.",
      0,
      true
    );
  }

  let payload = null;
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    try {
      payload = await response.json();
    } catch (_err) {
      payload = null;
    }
  }

  if (!response.ok) {
    throw new ApiError(extractErrorMessage(payload, response.status), response.status, false);
  }

  return payload;
}

export const api = {
  getLibros({ titulo = "", limit = 20, offset = 0 } = {}) {
    const params = new URLSearchParams();
    params.set("limit", String(limit));
    params.set("offset", String(offset));
    if (titulo.trim()) {
      params.set("titulo", titulo.trim());
    }
    return request(`/libros/?${params.toString()}`);
  },

  getLibro(id) {
    return request(`/libros/${id}`);
  },

  crearLibro(data) {
    return request("/libros/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  getEditoriales(limit = 100, offset = 0) {
    return request(`/editoriales/?limit=${limit}&offset=${offset}`);
  },

  getGeneros(limit = 100, offset = 0) {
    return request(`/generos/?limit=${limit}&offset=${offset}`);
  },

  getAutores(limit = 100, offset = 0) {
    return request(`/autores/?limit=${limit}&offset=${offset}`);
  },

  getAutor(id) {
    return request(`/autores/${id}`);
  },

  getClientes(limit = 100, offset = 0) {
    return request(`/clientes/?limit=${limit}&offset=${offset}`);
  },

  getCliente(id) {
    return request(`/clientes/${id}`);
  },

  crearCliente(data) {
    return request("/clientes/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  getVentas(limit = 20, offset = 0) {
    return request(`/ventas/?limit=${limit}&offset=${offset}`);
  },

  getVenta(id) {
    return request(`/ventas/${id}`);
  },

  crearVenta(data) {
    return request("/ventas/", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },
};

export function formatMoney(value) {
  const num = Number(value);
  if (Number.isNaN(num)) return "$0.00";
  return `$${num.toFixed(2)}`;
}

export function setFeedback(el, message, type = "info") {
  el.className = el.classList.contains("form-feedback") ? "form-feedback" : "status-banner";
  if (!message) {
    el.textContent = "";
    return;
  }
  el.classList.add(`is-${type}`);
  el.textContent = message;
}
