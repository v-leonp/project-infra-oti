(function () {
  function initPasswordToggle() {
    const passwordInput = document.getElementById("id_password");
    const toggleButton = document.getElementById("toggle-password");
    if (!passwordInput || !toggleButton) {
      return;
    }

    const labels = {
      show: "Mostrar contraseña",
      hide: "Ocultar contraseña",
    };

    toggleButton.addEventListener("click", function () {
      const isHidden = passwordInput.type === "password";
      passwordInput.type = isHidden ? "text" : "password";
      toggleButton.setAttribute("aria-label", isHidden ? labels.hide : labels.show);
      toggleButton.setAttribute("aria-pressed", String(isHidden));
    });
  }

  function focusFirstError() {
    const alert = document.getElementById("login-errors");
    if (alert) {
      alert.focus();
      return;
    }
    const invalid = document.querySelector("[aria-invalid='true']");
    if (invalid) {
      invalid.focus();
    }
  }

  document.addEventListener("DOMContentLoaded", function () {
    initPasswordToggle();
    focusFirstError();
  });
})();
