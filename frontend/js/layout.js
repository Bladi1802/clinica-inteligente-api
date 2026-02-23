// frontend/js/layout.js
document.addEventListener("DOMContentLoaded", () => {
  const sideBar = document.getElementById("sideBar");
  const menuBtn = document.getElementById("menuBtn");
  const closeMenuBtn = document.getElementById("closeMenuBtn");

  function openSidebar() {
    if (!sideBar) return;
    sideBar.classList.add("open");
    document.body.classList.add("sidebar-open");
  }

  function closeSidebar() {
    if (!sideBar) return;
    sideBar.classList.remove("open");
    document.body.classList.remove("sidebar-open");
  }

  // Arranca cerrado en móvil
  closeSidebar();

  if (menuBtn) menuBtn.addEventListener("click", openSidebar);
  if (closeMenuBtn) closeMenuBtn.addEventListener("click", closeSidebar);

  // Cerrar al hacer click en “overlay”
  document.addEventListener("click", (e) => {
    if (!document.body.classList.contains("sidebar-open")) return;

    const clickedInsideSidebar = sideBar && sideBar.contains(e.target);
    const clickedMenuBtn = menuBtn && (menuBtn === e.target || menuBtn.contains(e.target));

    if (!clickedInsideSidebar && !clickedMenuBtn) closeSidebar();
  });

  // Cerrar al navegar (opcional)
  document.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener("click", () => closeSidebar());
  });

  // Cerrar con ESC
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeSidebar();
  });
});