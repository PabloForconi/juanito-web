/**
 * Rutas internas con el "base" del sitio (en GitHub Pages el sitio vive en
 * /juanito-web/). Usar siempre u('/ruta/') para links y archivos de public/.
 */
const BASE = import.meta.env.BASE_URL.endsWith('/') ? import.meta.env.BASE_URL : `${import.meta.env.BASE_URL}/`;

export const u = (path: string): string => (path.startsWith('/') && !path.startsWith('//') ? BASE + path.slice(1) : path);
