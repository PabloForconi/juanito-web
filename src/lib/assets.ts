import type { ImageMetadata } from 'astro';

/** Todas las imágenes de src/assets, indexadas por ruta relativa ("fanart/x.jpg"). */
const files = import.meta.glob<{ default: ImageMetadata }>('../assets/**/*.{png,jpg,jpeg,webp}', { eager: true });

const byPath = new Map<string, ImageMetadata>();
for (const [k, v] of Object.entries(files)) byPath.set(k.replace('../assets/', ''), v.default);

/** Devuelve la imagen o tira un error claro en build si la ruta no existe. */
export function asset(path: string): ImageMetadata {
  const img = byPath.get(path);
  if (!img) throw new Error(`Imagen no encontrada en src/assets: "${path}"`);
  return img;
}

export function maybeAsset(path?: string): ImageMetadata | undefined {
  return path ? byPath.get(path) : undefined;
}
