// Comportamientos de formularios que se usan en varias pantallas.
//   <button data-confirmar="¿Seguro?"> -> pide confirmación antes de enviar el formulario
//   <input data-buscar>                -> envía la búsqueda mientras se escribe
//   <input data-autoenviar>            -> envía su formulario al terminar de editar (al cambiar el valor)

(function () {
  document.addEventListener('submit', e => {
    const aviso = e.submitter && e.submitter.dataset.confirmar;
    if (aviso && !window.confirm(aviso)) e.preventDefault();
  });

  document.addEventListener('change', e => {
    if (e.target.matches('[data-autoenviar]') && e.target.form) e.target.form.requestSubmit();
  });

  document.querySelectorAll('[data-buscar]').forEach(campo => {
    let reloj;
    campo.addEventListener('input', () => {
      clearTimeout(reloj);
      reloj = setTimeout(() => campo.form.submit(), 400);
    });
    // Tras buscar, el cursor vuelve al final del texto para seguir escribiendo
    if (campo.value) {
      campo.focus();
      campo.setSelectionRange(campo.value.length, campo.value.length);
    }
  });
})();
