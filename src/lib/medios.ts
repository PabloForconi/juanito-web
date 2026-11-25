import { maybeAsset } from './assets';
import mediosData from '../data/medios.json';
import type { Medio } from '../data/types';

/** Medios de prensa, en orden de peso (el orden de medios.json). */
export const medios = mediosData as Medio[];

/**
 * Logo blanco de un medio, con una altura que compensa la proporción para que
 * todos "pesen" parecido: uno muy ancho queda más bajo, uno cuadrado más alto.
 */
export const logoDe = (nombre: string, escala = 1) => {
  const medio = medios.find((m) => m.nombre === nombre);
  const img = maybeAsset(medio?.logo);
  if (!img) return undefined;
  const h = Math.min(40, Math.max(16, Math.sqrt(3000 / (img.width / img.height)))) * escala * (medio?.escala ?? 1);
  return { img, h: Math.round(h) };
};
