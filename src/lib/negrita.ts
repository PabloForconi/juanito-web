/**
 * Texto de los JSON con **palabras** en negrita: escapa el HTML y convierte **x** en <strong>x</strong>.
 * Se usa con set:html, p. ej. <p set:html={negrita(h.texto)} />.
 */
export function negrita(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
}

/** El mismo texto sin las marcas, para atributos (alt, meta description). */
export const sinNegrita = (s: string) => s.replace(/\*\*(.+?)\*\*/g, '$1');
