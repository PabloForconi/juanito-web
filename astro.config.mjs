// @ts-check
import { defineConfig } from 'astro/config';

// En GitHub Pages el sitio vive en https://pabloforconi.github.io/juanito-web/.
// El workflow de deploy define SITE_URL y BASE_PATH; en local queda en la raíz
// (http://localhost:4321/). Cuando haya dominio propio, BASE_PATH pasa a "/".
export default defineConfig({
  site: process.env.SITE_URL ?? 'http://localhost:4321',
  base: process.env.BASE_PATH ?? '/',
  trailingSlash: 'always',
  i18n: {
    defaultLocale: 'es',
    locales: ['es'], // a futuro: ['es', 'en']
  },
});
