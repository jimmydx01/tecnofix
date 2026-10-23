// Mensaje breve en pantalla: toast('Texto').
// También muestra los mensajes que manda Django (messages) al cargar la página.

(function () {
  let reloj = null;

  window.toast = function (texto) {
    const caja = document.getElementById('toast');
    if (!caja) return;
    caja.textContent = texto;
    caja.classList.remove('hidden');
    clearTimeout(reloj);
    reloj = setTimeout(() => caja.classList.add('hidden'), 2600);
  };

  // Mensajes de Django: se muestran en orden, uno tras otro
  const mensajes = [...document.querySelectorAll('[data-mensaje]')];
  mensajes.forEach((m, i) => setTimeout(() => window.toast(m.textContent.trim()), i * 2800));
})();
