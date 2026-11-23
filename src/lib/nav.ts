import { u } from './url';

export interface NavItem {
  href: string;
  label: string;
}

/** Secciones principales (orden del menú). */
export const NAV: NavItem[] = [
  { href: u('/el-juego/'), label: 'El juego' },
  { href: u('/historia/'), label: 'Historia' },
  { href: u('/prensa/'), label: 'Prensa' },
  { href: u('/videos/'), label: 'Videos' },
  { href: u('/galeria/'), label: 'Galería' },
];

/** Secundarias (menú "Más" y footer). */
export const NAV_MORE: NavItem[] = [
  { href: u('/musica/'), label: 'Música' },
  { href: u('/juego-de-mesa/'), label: 'Juego de mesa' },
  { href: u('/pirateria/'), label: 'Salón de la piratería' },
  { href: u('/creditos/'), label: 'Créditos' },
];

export const CTA: NavItem = { href: u('/conseguilo/'), label: 'Conseguilo' };
