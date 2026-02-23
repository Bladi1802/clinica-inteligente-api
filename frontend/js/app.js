import { api } from "./api.js";
import { $, log, setAuthBadge } from "./ui.js";
import { getAccessToken, setTokens, clearTokens } from "./api.js";

const app = $("#app");

function setViewMeta(title, subtitle) {
  $("#viewTitle").textContent = title;
  $("#viewSubtitle").textContent = subtitle || "";
}

function escapeHtml(v) {
  return String(v)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function updateUserUI(me) {
  // me puede traer username/email/role según tu backend
  const name = me?.username || me?.email || "Usuario";
  const role = me?.role || "Autenticado";

  const el1 = document.getElementById("userName");
  const el2 = document.getElementById("userNameHeader");
  const el3 = document.getElementById("userRole");

  if (el1) el1.textContent = name;
  if (el2) el2.textContent = name;
  if (el3) el3.textContent = role;
}


function toDateInputValue(iso) {
  if (!iso) return "";
  return iso.slice(0, 10);
}

function toTimeInputValue(iso) {
  if (!iso) return "";
  const t = iso.split("T")[1] || "";
  return t.slice(0, 5);
}

/* -------------------- LOGIN -------------------- */

function renderLogin() {
  setViewMeta("Login", "POST /api/auth/token/");

  app.innerHTML = `
    <div class="row">
      <div>
        <label>Username</label>
        <input id="username" type="text" placeholder="Bladimir" />
      </div>
      <div>
        <label>Password</label>
        <input id="password" type="password" placeholder="********" />
      </div>
    </div>

    <div style="display:flex; gap:10px; margin-top:12px; flex-wrap:wrap;">
      <button id="loginBtn" class="btn">Entrar</button>
      <button id="registerBtn" class="btn btn--ghost">Registrar usuario</button>
      <button id="testMeBtn" class="btn btn--ghost">Probar /me</button>
    </div>

    <p class="muted" style="margin-top:10px;">
      ¿Nuevo? Usa <b>Registrar usuario</b> para crear tu cuenta y después inicia sesión.
    </p>
  `;

  $("#loginBtn").addEventListener("click", async () => {
    try {
      const username = $("#username").value.trim();
      const password = $("#password").value;

      const res = await api.login(username, password);
      log(res);

      const access = res.access || res.access_token;
      const refresh = res.refresh;

      if (!access) throw new Error("Login NO devolvió 'access'.");

      setTokens({ access, refresh });
      setAuthBadge(true);

      // (Opcional) actualizar nombre en UI
      try {
        const me = await api.me();
        updateUserUI(me);
      } catch (_) {}

      renderDashboard();
    } catch (e) {
      log(String(e.message || e));
    }
  });

  $("#registerBtn").addEventListener("click", () => renderRegisterUser());

  $("#testMeBtn").addEventListener("click", async () => {
    try {
      const me = await api.me();
      log(me);
      updateUserUI(me);
    } catch (e) {
      log("Necesitas iniciar sesión primero.\n" + String(e.message || e));
    }
  });
}

function renderRegisterUser() {
  setViewMeta("Registrar usuario", "POST /api/auth/register/");

  app.innerHTML = `
    <div class="row">
      <div>
        <label>Username</label>
        <input id="r_username" type="text" placeholder="nuevo_usuario" />
      </div>
      <div>
        <label>Password</label>
        <input id="r_password" type="password" placeholder="********" />
      </div>
    </div>

    <div class="row" style="margin-top:12px;">
      <div>
        <label>Email (opcional)</label>
        <input id="r_email" type="email" placeholder="correo@dominio.com" />
      </div>
      <div>
        <label>Teléfono (opcional)</label>
        <input id="r_phone" type="text" placeholder="664..." />
      </div>
    </div>

    <div class="row" style="margin-top:12px;">
      <div>
        <label>Rol (si tu backend lo soporta)</label>
        <select id="r_role" style="width:100%; padding:10px 12px; border-radius:12px; border:1px solid rgba(255,255,255,.10); background:rgba(255,255,255,.04); color:#e8eefc;">
          <option value="">PATIENT (por defecto)</option>
          <option value="PATIENT">PATIENT</option>
          <option value="DOCTOR">DOCTOR</option>
          <option value="CLINIC">CLINIC</option>
        </select>
      </div>
      <div>
        <label>Nombre (opcional)</label>
        <input id="r_name" type="text" placeholder="Nombre completo" />
      </div>
    </div>

    <div style="display:flex; gap:10px; margin-top:12px; flex-wrap:wrap;">
      <button id="createUserBtn" class="btn">Crear cuenta</button>
      <button id="backToLoginBtn" class="btn btn--ghost">Volver a login</button>
    </div>

    <p class="muted" style="margin-top:10px;">
      Después de crear la cuenta, vuelve a login e inicia sesión.
    </p>
  `;

  $("#createUserBtn").addEventListener("click", async () => {
    try {
      const payload = {
        username: $("#r_username").value.trim(),
        password: $("#r_password").value,
        email: $("#r_email").value.trim() || undefined,
        phone: $("#r_phone").value.trim() || undefined,
        name: $("#r_name").value.trim() || undefined,
      };

      const role = $("#r_role").value;
      if (role) payload.role = role;

      Object.keys(payload).forEach(k => payload[k] === undefined && delete payload[k]);

      // ✅ Usa tu endpoint real
      const res = await api.registerUser(payload);
      log(res);

      // UX: regresar a login
      renderLogin();
    } catch (e) {
      log(String(e.message || e));
    }
  });

  $("#backToLoginBtn").addEventListener("click", () => renderLogin());
}


/* -------------------- DASHBOARD -------------------- */

function renderDashboard() {
  setViewMeta("Dashboard", "Acciones");

  app.innerHTML = `
    <div style="display:flex; gap:10px; flex-wrap:wrap;">
      <button id="btnMe" class="btn">Ver /me</button>
      <button id="btnCitas" class="btn">Gestionar citas</button>
      <button id="btnCrear" class="btn btn--ghost">Crear cita</button>
    </div>

    <div id="dashContent" style="margin-top:12px;"></div>
  `;

  $("#btnMe").addEventListener("click", async () => {
    try {
      const me = await api.me();
      log(me);
      $("#dashContent").innerHTML = `<pre class="console">${escapeHtml(JSON.stringify(me, null, 2))}</pre>`;
    } catch (e) {
      log(String(e.message || e));
    }
  });

  $("#btnCitas").addEventListener("click", () => renderGestionCitas());
  $("#btnCrear").addEventListener("click", () => renderCrearCita());
}

/* -------------------- CREAR CITA -------------------- */

function renderCrearCita() {
  setViewMeta("Crear cita", "POST /api/appointments/");

  app.innerHTML = `
    <div class="row">
      <div>
        <label>Fecha</label>
        <input id="a_date" type="date" />
      </div>
      <div>
        <label>Hora</label>
        <input id="a_time" type="time" />
      </div>
    </div>

    <div class="row" style="margin-top:12px;">
      <div>
        <label>Paciente (ID o nombre según tu API)</label>
        <input id="a_patient" type="text" placeholder="1 o Juan Pérez" />
      </div>
      <div>
        <label>Motivo</label>
        <input id="a_reason" type="text" placeholder="Rayos X" />
      </div>
    </div>

    <div style="display:flex; gap:10px; margin-top:12px; flex-wrap:wrap;">
      <button id="createBtn" class="btn">Crear</button>
      <button id="backBtn" class="btn btn--ghost">Volver</button>
    </div>

    <p class="muted" style="margin-top:10px;">
      Tu API requiere <code>scheduled_at</code> (fecha+hora).
    </p>
  `;

  $("#createBtn").addEventListener("click", async () => {
    try {
      const date = $("#a_date").value;
      const time = $("#a_time").value;
      if (!date || !time) throw new Error("Selecciona fecha y hora.");

      const scheduled_at = `${date}T${time}:00`;

      const payload = {
        scheduled_at,
        patient: $("#a_patient").value.trim(),
        reason: $("#a_reason").value.trim(),
      };

      const res = await api.crearCita(payload);
      log(res);
      renderGestionCitas();
    } catch (e) {
      log(String(e.message || e));
    }
  });

  $("#backBtn").addEventListener("click", () => renderDashboard());
}

/* -------------------- LISTAR / EDITAR / ELIMINAR -------------------- */

async function renderGestionCitas() {
  setViewMeta("Citas del usuario", "GET /api/appointments/ | PATCH/DELETE /api/appointments/{id}/");

  app.innerHTML = `
    <div style="display:flex; gap:10px; flex-wrap:wrap; margin-bottom:12px;">
      <button id="refreshBtn" class="btn">Actualizar lista</button>
      <button id="newBtn" class="btn btn--ghost">Crear nueva</button>
      <button id="backBtn" class="btn btn--ghost">Volver</button>
    </div>

    <div id="citasWrap" class="muted">Cargando...</div>
  `;

  $("#refreshBtn").addEventListener("click", () => renderGestionCitas());
  $("#newBtn").addEventListener("click", () => renderCrearCita());
  $("#backBtn").addEventListener("click", () => renderDashboard());

  try {
    const data = await api.listarCitas();
    log(data);

    const items = Array.isArray(data) ? data : (data.results || data.items || []);

    if (items.length === 0) {
      $("#citasWrap").innerHTML = `<p class="muted">No hay citas registradas.</p>`;
      return;
    }

    $("#citasWrap").innerHTML = `
      <table class="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>scheduled_at</th>
            <th>Paciente</th>
            <th>Motivo</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          ${items.map(a => `
            <tr>
              <td>${escapeHtml(a.id ?? "-")}</td>
              <td>${escapeHtml(a.scheduled_at ?? "-")}</td>
              <td>${escapeHtml(a.patient ?? a.patient_name ?? a.patient_id ?? "-")}</td>
              <td>${escapeHtml(a.reason ?? a.motivo ?? "-")}</td>
              <td style="display:flex; gap:8px; flex-wrap:wrap;">
                <button class="btn btn--ghost" data-edit="${a.id}">Editar</button>
                <button class="btn btn--ghost" data-del="${a.id}">Eliminar</button>
              </td>
            </tr>
          `).join("")}
        </tbody>
      </table>
    `;

    document.querySelectorAll("[data-edit]").forEach(btn => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-edit");
        const cita = items.find(x => String(x.id) === String(id));
        renderEditarCita(cita);
      });
    });

    document.querySelectorAll("[data-del]").forEach(btn => {
      btn.addEventListener("click", async () => {
        const id = btn.getAttribute("data-del");
        const ok = confirm(`¿Eliminar cita ${id}?`);
        if (!ok) return;

        try {
          await api.eliminarCita(id);
          log(`Cita ${id} eliminada.`);
          renderGestionCitas();
        } catch (e) {
          log(String(e.message || e));
        }
      });
    });

  } catch (e) {
    $("#citasWrap").innerHTML = `<p class="muted">Error: ${escapeHtml(String(e.message || e))}</p>`;
    log(String(e.message || e));
  }
}

function renderEditarCita(cita) {
  if (!cita) return renderGestionCitas();

  setViewMeta("Editar cita", `PATCH /api/appointments/${cita.id}/`);

  const dateVal = toDateInputValue(cita.scheduled_at);
  const timeVal = toTimeInputValue(cita.scheduled_at);

  app.innerHTML = `
    <div class="row">
      <div>
        <label>Fecha</label>
        <input id="e_date" type="date" value="${escapeHtml(dateVal)}" />
      </div>
      <div>
        <label>Hora</label>
        <input id="e_time" type="time" value="${escapeHtml(timeVal)}" />
      </div>
    </div>

    <div class="row" style="margin-top:12px;">
      <div>
        <label>Paciente</label>
        <input id="e_patient" type="text" value="${escapeHtml(cita.patient ?? "")}" />
      </div>
      <div>
        <label>Motivo</label>
        <input id="e_reason" type="text" value="${escapeHtml(cita.reason ?? "")}" />
      </div>
    </div>

    <div style="display:flex; gap:10px; margin-top:12px; flex-wrap:wrap;">
      <button id="saveBtn" class="btn">Guardar cambios (PATCH)</button>
      <button id="backBtn" class="btn btn--ghost">Volver</button>
    </div>

    <p class="muted" style="margin-top:10px;">
      Se envía <code>scheduled_at</code> y los campos editados.
    </p>
  `;

  $("#saveBtn").addEventListener("click", async () => {
    try {
      const date = $("#e_date").value;
      const time = $("#e_time").value;
      if (!date || !time) throw new Error("Selecciona fecha y hora.");

      const scheduled_at = `${date}T${time}:00`;

      // PATCH: solo mandamos lo necesario
      const payload = {
        scheduled_at,
        patient: $("#e_patient").value.trim(),
        reason: $("#e_reason").value.trim(),
      };

      const res = await api.editarCitaPATCH(cita.id, payload);
      log(res);
      renderGestionCitas();
    } catch (e) {
      log(String(e.message || e));
    }
  });

  $("#backBtn").addEventListener("click", () => renderGestionCitas());
}

/* -------------------- NAV + BOOT -------------------- */

function initNav() {
  document.querySelectorAll("[data-view]").forEach(btn => {
    btn.addEventListener("click", () => {
      const view = btn.getAttribute("data-view");
      if (view === "login") renderLogin();
      if (view === "dashboard") renderDashboard();
      if (view === "citas") renderGestionCitas();
      if (view === "pacientes") renderDashboard(); // placeholder si luego haces pacientes
    });
  });

  $("#logoutBtn").addEventListener("click", () => {
    clearTokens();
    setAuthBadge(false);
    log("Sesión cerrada. Tokens eliminados.");
    renderLogin();
  });
}

(async function boot() {
  initNav();
  const isAuth = Boolean(getAccessToken());
  setAuthBadge(isAuth);

  if (isAuth) {
    try { updateUserUI(await api.me()); } catch (_) {}
    renderDashboard();
  } else {
    renderLogin();
  }
})();
