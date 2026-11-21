const MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic'];

/** "2017-08-03" → "3 ago 2017" · "2017-08" → "ago 2017" · "2017" → "2017" */
export function fecha(f?: string): string {
  if (!f) return '';
  const [y, m, d] = f.split('-');
  if (d) return `${Number(d)} ${MESES[Number(m) - 1]} ${y}`;
  if (m) return `${MESES[Number(m) - 1]} ${y}`;
  return y;
}

export const anio = (f?: string) => (f ? f.slice(0, 4) : '');

/** Orden cronológico por fecha parcial. */
export const byFecha = <T extends { fecha?: string }>(a: T, b: T) => (a.fecha || '9999').localeCompare(b.fecha || '9999'); // sin fecha, al final

export function miles(n?: number): string {
  return n == null ? '' : n.toLocaleString('es-AR');
}
