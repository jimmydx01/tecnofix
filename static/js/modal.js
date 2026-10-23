// Ventanas emergentes (modales).
//   data-abrir-modal="id"  -> en cualquier elemento: abre la ventana con ese id
//   data-modal             -> marca a la ventana (el fondo oscuro)
// Se cierran haciendo clic fuera de la ventana o con la tecla Esc.

(function () {
  function cerrarTodas() {
    document.querySelectorAll('[data-modal]').forEach(m => m.classList.add('hidden'));
  }

  function abrir(id) {
    const ventana = document.getElementById(id);
    if (!ventana) return;
    cerrarTodas();
    ventana.classList.remove('hidden');
    // Lleva el cursor al primer campo, si la ventana tiene formulario
    const campo = ventana.querySelector('input');
    if (campo) campo.focus();
  }

  document.addEventListener('click', e => {
    const disparador = e.target.closest('[data-abrir-modal]');
    if (disparador) {
      abrir(disparador.dataset.abrirModal);
      return;
    }
    // Clic en el fondo oscuro (no dentro de la ventana)
    if (e.target.hasAttribute('data-modal')) cerrarTodas();
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') cerrarTodas();
    // Las tarjetas con role="button" también se abren con Enter o espacio
    if ((e.key === 'Enter' || e.key === ' ') && e.target.matches('[role="button"][data-abrir-modal]')) {
      e.preventDefault();
      abrir(e.target.dataset.abrirModal);
    }
  });

  // Si la página llegó con una ventana abierta (por ejemplo, con errores), pone el cursor donde corresponde
  const abierta = document.querySelector('[data-modal]:not(.hidden)');
  if (abierta) {
    const campo = abierta.querySelector('[data-error]') || abierta.querySelector('input:not([type=hidden])');
    if (campo) campo.focus();
  }

  // Formularios que todavía no están conectados: avisan en vez de enviarse
  document.querySelectorAll('form[data-pendiente]').forEach(f => {
    f.addEventListener('submit', e => {
      e.preventDefault();
      window.toast('Esta función se activa en el ' + f.dataset.pendiente);
    });
  });
})();
