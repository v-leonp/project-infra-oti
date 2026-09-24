(function () {
  function initSidebar() {
    const toggle = document.getElementById("sidebar-toggle");
    const sidebar = document.getElementById("app-sidebar");
    const backdrop = document.getElementById("sidebar-backdrop");
    if (!toggle || !sidebar || !backdrop) return;

    function setOpen(open) {
      sidebar.classList.toggle("-translate-x-full", !open);
      backdrop.classList.toggle("hidden", !open);
      toggle.setAttribute("aria-expanded", String(open));
      toggle.setAttribute("aria-label", open ? "Cerrar menú" : "Abrir menú");
    }

    toggle.addEventListener("click", function () {
      const isOpen = sidebar.classList.contains("-translate-x-full");
      setOpen(isOpen);
    });
    backdrop.addEventListener("click", function () {
      setOpen(false);
    });
  }

  function initCatalogsMenu() {
    const toggle = document.getElementById("catalogs-menu-toggle");
    const submenu = document.getElementById("catalogs-submenu");
    if (!toggle || !submenu) return;
    toggle.addEventListener("click", function () {
      const isHidden = submenu.classList.contains("hidden");
      submenu.classList.toggle("hidden", !isHidden);
      toggle.setAttribute("aria-expanded", String(isHidden));
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    initSidebar();
    initCatalogsMenu();
  });
})();
