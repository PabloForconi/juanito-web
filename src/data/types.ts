/**
 * Tipos de los datos del sitio (src/data/*.json).
 * Las rutas de imagen ("img") son relativas a src/assets/ (ej. "fanart/astodh.jpg")
 * y se resuelven con src/lib/assets.ts.
 * Fechas: "YYYY-MM-DD", "YYYY-MM" o "YYYY" según lo que se sepa.
 */

// ------------------------------------------------------------- el juego
export interface Mundo {
  slug: string;
  nombre: string; // nombre provisional (el dueño lo define después)
  parodia: string; // clásico parodiado, ej. "Tetris"
  jefe?: string; // nombre del jefe, si se conoce
  descripcion: string;
  chip?: string; // img: tarjeta del mundo
  fondo?: string; // img: fondo del nivel
  jefeImg?: string; // img
  flip?: boolean; // espejar el cartucho horizontalmente en el selector
  especial?: string; // etiqueta en lugar de "Mundo N" (ej. "Inicio", "Final"); no cuenta en la numeración
}

export interface Personaje {
  slug: string;
  nombre: string;
  rol: string; // "Protagonista", "Compañero alien"...
  descripcion: string;
  img: string;
  extra?: string[]; // otras poses (img)
  oculto?: boolean; // true = no se muestra en el sitio (queda en los datos)
}

export interface Enemigo {
  slug: string;
  nombre: string; // en español
  original?: string; // nombre en inglés del artbook
  descripcion: string;
  img?: string;
}

// ------------------------------------------------------------- archivo
export interface Nota {
  id: string;
  titulo: string;
  medio: string;
  fecha: string;
  pais?: string;
  idioma: 'es' | 'en' | 'pt' | 'fa' | 'other';
  tipo: 'nota' | 'review' | 'entrevista' | 'noticia';
  puntaje?: string; // "7/10", "85%"
  url: string;
  archivo?: string; // copia en web.archive.org si la original cayó
  resumen: string; // resumen propio, máx. ~30 palabras (no copiar texto)
  destacada?: boolean;
  caida?: boolean; // el link original ya no existe: la nota no se muestra
  portada?: string; // imagen propia (ruta en src/assets) para las destacadas
}

/** Medios de prensa: logo en blanco (src/assets/prensa/logos). Sin logo se muestra el nombre. */
export interface Medio {
  nombre: string;
  logo?: string;
  /** Ajuste fino del tamaño del logo (1 = normal), para los que a ojo quedan chicos */
  escala?: number;
}

export interface Video {
  id: string;
  titulo: string;
  canal: string;
  fecha?: string;
  youtubeId?: string; // sin youtubeId = "próximamente"
  categoria: 'oficial' | 'animacion' | 'comunidad' | 'entrevista' | 'making-of' | 'resena' | 'musica';
  vistas?: number;
  nota?: string;
}

export interface Radio {
  id: string;
  programa: string;
  emisora: string;
  fecha: string;
  duracion?: string; // "1:04:59"
  descripcion: string;
  audio?: string; // ruta pública, ej. "/media/radio/overcast-24.opus"
  img?: string; // portada del programa
}

export interface Hito {
  fecha: string;
  titulo: string;
  texto: string;
  categoria: 'origen' | 'desarrollo' | 'evento' | 'lanzamiento' | 'prensa' | 'comunidad' | 'legado';
  img?: string | string[]; // una o varias imágenes (miniaturas que se abren en el visor)
  // imagen tomada de un evento (sus nombres llevan huella y cambian al re-exportar):
  // n = posición en [flyer, ...fotos]; 0 por defecto
  evento?: { slug: string; n?: number };
  link?: string;
}

export interface Evento {
  slug: string;
  nombre: string;
  fecha: string;
  lugar?: string;
  descripcion?: string;
  flyer?: string; // img
  fotos: string[]; // img
  portada?: string; // img: recorte para la tarjeta (el álbum muestra la imagen entera)
  oculto?: boolean; // se exporta pero no se muestra (falta información)
  pedirDatos?: boolean; // muestra «¿Estuviste en este evento? Mandanos info por nuestras redes.»
}

export interface Cita {
  texto: string; // máx. 15 palabras
  autor: string;
  fuente: string; // "Reseña de Steam", "Pocket Gamer"...
  url?: string;
  destacada?: boolean; // también va en tarjeta (Steam: Conseguilo; Taringa: Prensa)
  // datos de la reseña de Steam (se muestran en la tarjeta en lugar de la fuente)
  fecha?: string;
  horas?: number; // horas jugadas al escribirla
  utiles?: number; // personas que la marcaron como útil
  recomienda?: boolean;
}

export interface Credito {
  rol: string;
  nombres: string[];
  /** listas largas (playtesters, agradecimientos): nombres más chicos y corridos, separados por puntos */
  compacto?: boolean;
}

export interface FanArt {
  img: string;
  autor: string; // "Fan desconocido" si no se sabe
  titulo?: string;
  fecha?: string;
  origen?: string; // "Concurso Fan-Art 2017", "DeviantArt"...
  url?: string;
  mini?: boolean; // dibujo de un chico o una chica: va en el bloque "Mini fans"
}

export interface ItemGaleria {
  img: string;
  titulo: string;
  categoria: 'concept' | 'afiche' | 'posters' | 'merch' | 'arcade' | 'artbook' | 'promo' | 'fondos' | 'historia';
  fecha?: string;
  descripcion?: string;
  serie?: string; // las piezas de una misma serie se muestran juntas, en su propio bloque
  oculto?: boolean; // se exporta (lo usa otra página) pero no se muestra en la galería
}

export interface CapturaPirata {
  img: string;
  sitio: string;
  pais?: string;
  fecha?: string;
  chiste: string; // epígrafe con humor
}

export interface SitioPirata {
  nombre: string;
  pais?: string;
  detalle: string; // qué tiene de gracioso (sin link a descargas)
}

export interface PostTaringa {
  titulo: string;
  fecha: string;
  url: string; // archivo en web.archive.org
  resumen: string;
  stats?: string; // "761 puntos · 13.170 visitas · 336 comentarios"
}

/** Banda sonora (página Música). Cada tema es un video de YouTube del canal del estudio. */
export interface Tema {
  n: number;
  titulo: string;
  youtubeId: string;
  duracion: string; // "m:ss"
}
export interface Disco {
  titulo: string;
  autor: string;
  portada: string; // ruta en src/assets
  steam: string;
  precio?: string;
  temas: Tema[];
}

/** Récords del gabinete arcade (Historia). El ranking ordena por tiempo sobrevivido. */
export interface Records {
  nota: string;
  tabla: { ini: string; tiempo: string; puntaje: number; nuevo?: boolean }[];
  // pie: año y lugar de la foto; foco/zoom: recorte de la miniatura (el visor muestra la foto entera)
  fotos: { img: string; titulo: string; fecha: string; pie?: string; foco?: string; zoom?: number }[];
}
