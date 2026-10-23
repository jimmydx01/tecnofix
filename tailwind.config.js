// Tailwind revisa estos archivos para saber qué clases usa el diseño
// y genera solo el CSS necesario (static/css/tailwind.css).
module.exports = {
  content: [
    './templates/**/*.html',
    './*/templates/**/*.html',
    './static/js/**/*.js',
  ],
  theme: { extend: {} },
  plugins: [],
};
