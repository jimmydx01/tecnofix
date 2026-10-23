// Modo día / noche. La elección se guarda en el navegador (clave "tf-th").

(function () {
  const raiz = document.documentElement;
  const botones = document.querySelectorAll('[data-tema-toggle]');
  const svg = trazo => '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" class="w-5 h-5" aria-hidden="true">' + trazo + '</svg>';
  const SOL = svg('<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>');
  const LUNA = svg('<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>');

  // El botón muestra la luna cuando es de día y el sol cuando es de noche
  function pintarBotones() {
    const dia = raiz.dataset.theme === 'light';
    botones.forEach(b => (b.innerHTML = dia ? LUNA : SOL));
  }

  function cambiarTema() {
    const nuevo = raiz.dataset.theme === 'light' ? 'dark' : 'light';
    raiz.dataset.theme = nuevo;
    try {
      localStorage.setItem('tf-th', nuevo);
    } catch (e) {}
    pintarBotones();
  }

  botones.forEach(b => b.addEventListener('click', cambiarTema));
  pintarBotones();
})();
