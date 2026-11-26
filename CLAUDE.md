# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Contexto

Es un sitio memorabilia del videojuego **Juanito Arcade Mayhem** (Game Ever Studio, Steam 2017 y mobile 2018). La home tiene que ser de alto impacto visual: parallax espacial y alienígena, verde neón, el personaje en grande y animaciones **sin sonido**. El sitio está en español; el inglés se agrega más adelante.

- Plan, fases y decisiones tomadas: `docs/PLAN.md`. Se trabaja por fases y el dueño valida cada una.
- Investigación web: `docs/investigacion/`. Empezar por `00-resumen.md`.
- Inventario del material local: `docs/material/`, con vistas previas en `docs/material/previews/`.

El material original del juego (87 GB) está en `E:\Game Ever\TRABAJOS\Juanito`. Es **solo lectura**: nunca crear, mover ni modificar nada ahí. Los temporales van al scratchpad.

No publicar los documentos de `Diego\Carpeta High Concept`: tienen datos personales (CUIT, domicilios, teléfonos, presupuestos).

## Comandos

```
npm run dev                 # servidor local en http://localhost:4321
npm run build               # build estático a dist/
npm run check               # chequeo de tipos de Astro
npm run assets              # vuelve a exportar todos los assets desde E:
npm run assets -- hero      # solo un grupo (hero, logo)
```

- Para `npm run assets` hace falta el venv de Python en `tools/.venv`, con psd-tools[composite], pillow y pymupdf.
- ffmpeg portable está en `tools/ffmpeg/bin/`.
- La imagen para compartir el sitio (`public/og.jpg`, una sola para todo el sitio) se arma con `tools/.venv/Scripts/python.exe tools/make_og.py`, a partir de la key art y el logo ya exportados.
- `tools/.venv` y `tools/ffmpeg` no se versionan. Si faltan, se recrean con:

```
python -m venv tools/.venv && tools/.venv/Scripts/python.exe -m pip install "psd-tools[composite]" pillow pymupdf
```

## Arquitectura

- **Stack:** Astro 7 (sitio estático) + TypeScript, GSAP/ScrollTrigger para animación (solo en el hero de la home) y fuentes self-hosted con fontsource. Cada familia tiene un token en `src/styles/global.css`:
  - `--font-display`: Rubik Black, para títulos en mayúsculas. Es la variable de Rubik y se usa en peso 900. El dueño no quiere serifas en los títulos.
  - `--font-heading`: Russo One, para subtítulos y destacados. También tiene un solo peso.
  - `--font-ui`: Chakra Petch, para etiquetas, botones y datos.
  - `--font-body`: Nunito, para el texto corrido.

  Estas fuentes las eligió el dueño. El formato moderno se probó con otras y prefirió estas.

  Dirección visual "moderna":
  - Fondo casi negro con auroras y grano.
  - Superficies de vidrio (`.card`) con bordes `--line` y radios `--radius`.
  - Botones en forma de pill.
  - Destacados con el gradiente `--grad-brand` en la clase `.hl`.
  - El verde y el lima van como acento, no como glow en todo.
  - Hay un backup de la versión retro anterior en el scratchpad de la sesión del 20/11/2026.

  Captura de referencia: `docs/diseno/tipografia.png`. No hay framework de UI: los scripts de cliente van en `<script>` dentro de cada componente `.astro`.
- **Assets:** `tools/export_assets.py` es la única puerta de entrada desde el material original.
  - Cada grupo (`GROUPS`) abre los PSD/AI originales, compone capas y escribe PNG/SVG en `src/assets/`.
  - Los ajustes globales de color del PSD (Curvas, Equilibrio de color) se "bakean" con una LUT por canal, calculada contra el merge que guardó Photoshop.
  - Las capas recortadas guardan su posición en el lienzo original en un manifest (`src/assets/hero/layers.json`).
  - Astro convierte esos PNG a WebP responsive en el build. **No editar los assets a mano: re-exportar.**
- **Hero** (`src/components/Hero.astro`):
  - Arma la key art `BG_Main_v6.psd` (2880×1620) con capas posicionadas en % según `layers.json`, dentro de un lienzo 16:9 que hace "cover" del viewport. En pantallas verticales la escena va abajo y el logo arriba.
  - Cada capa tiene tres niveles de transform, para que las animaciones no se pisen: `.layer` (entrada y scroll) > `.layer__mouse` (parallax del mouse) > `img` (loops idle).
  - `data-depth` define cuánto se mueve cada capa.
- **Logo:** hay dos versiones.
  - El **pintado** (`src/assets/logo/logo-pintado.png`, sale de `Logo/Logo_Juanito_Pintura_v1.png`) es el oficial y va en tamaños grandes, como el hero. El footer usa su versión en blanco (`logo-pintado-blanco.png`), que también genera `export_assets.py`.
  - El **vectorial** (`logo.svg`) va solo en tamaños chicos, como el menú.
- **Contenido como datos:** todo el contenido del archivo vive en `src/data/*.json`, tipado en `src/data/types.ts`.
  - Las imágenes se referencian por ruta relativa a `src/assets/` y se resuelven con `asset()` / `maybeAsset()` de `src/lib/assets.ts`. `asset()` falla el build si la ruta no existe.
  - Para agregar una nota, un video o un evento, se edita el JSON. Las páginas no se tocan.
- **Páginas:** `index` (home), `el-juego`, `historia`, `prensa`, `videos`, `galeria`, `juego-de-mesa`, `pirateria`, `creditos` y `conseguilo`.
  - El menú sale de `src/lib/nav.ts`.
  - Todas usan `Base.astro`, que incluye Nav, Footer y Starfield. Base también revela los elementos marcados con `data-reveal`, con IntersectionObserver y una transición CSS (clase `.is-in`). Usa scroll nativo: el smooth scroll se sacó a pedido del dueño.
  - Las páginas internas abren con `PageHeader.astro`.
- **Componentes reutilizables:**
  - `Gallery.astro`: grilla con lightbox. Necesita un `<Lightbox />` por página.
  - `YouTube.astro`: embed liviano con youtube-nocookie. Sin id, muestra "Próximamente".
  - `Marquee.astro`: citas.
- **Exportadores:**
  - `tools/export_assets.py` exporta el arte del juego a `src/assets/juego/`, el hero y los personajes.
  - `tools/export_archivo.py` exporta fan art, eventos, galería y piratería a `src/assets/archivo/`, y los audios de radio a `public/media/radio/`.
- **Fondo:** `src/components/Starfield.astro` combina auroras CSS quietas con un canvas de estrellas que se redibuja solo al scrollear. Se montó en `Base.astro`.
- **Rendimiento (pedido del dueño):** no usar `backdrop-filter` en tarjetas ni en elementos repetidos (solo en la barra del menú) y no agregar animaciones continuas de fondo. El hero de la home es la única zona con animación constante.
- **Movimiento reducido:** todo el movimiento se apaga con `prefers-reduced-motion`.

## Repo

- GitHub (**público**): `git@github.com:PabloForconi/juanito-web.git`, rama `main`. El repo local usa `core.sshCommand` con la clave `~/.ssh/DesktopPablo`.
- Publicado en GitHub Pages: https://pabloforconi.github.io/juanito-web/
  - Cada push a `main` dispara `.github/workflows/deploy.yml`, que compila con `SITE_URL` y `BASE_PATH=/juanito-web`.
  - Los links internos siempre van con `u('/ruta/')` de `src/lib/url.ts`, para que respeten el base path. En local el base es `/`.
  - Para probar el build con el base path en Git Bash: `MSYS_NO_PATHCONV=1 SITE_URL=https://pabloforconi.github.io BASE_PATH=/juanito-web npm run build`.
- `docs/` **no se versiona**: está en `.gitignore` y queda solo en la PC, porque es documentación interna y el repo es público.

## Pendiente

- Hosting y dominio.
