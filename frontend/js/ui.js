export function $(sel) {
  return document.querySelector(sel);
}

export function log(value) {
  const el = document.getElementById("console");
  if (!el) return;
  const msg = typeof value === "string" ? value : JSON.stringify(value, null, 2);
  el.textContent = msg;
}

let flashTimer = null;

export function flash(message, type = "success") {
  const el = document.getElementById("flashMessage");
  if (!el) return;

  if (flashTimer) clearTimeout(flashTimer);

  el.textContent = String(message || "");
  el.className = `flash-message flash-message--${type}`;
  el.hidden = false;

  flashTimer = setTimeout(() => {
    el.hidden = true;
  }, 3600);
}

export function setAuthBadge(isAuth) {
  const badge = document.getElementById("authBadge");
  if (!badge) return;
  badge.textContent = isAuth ? "Autenticado" : "No autenticado";
}
