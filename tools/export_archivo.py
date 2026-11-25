"""Exporta el material de ARCHIVO (fanart, eventos, galería, piratería, radio)
desde el material original (solo lectura) a src/assets/archivo/ y public/media/radio/.

Uso:  tools\\.venv\\Scripts\\python.exe -I tools\\export_archivo.py            (todo)
      tools\\.venv\\Scripts\\python.exe -I tools\\export_archivo.py radio      (un grupo)
Grupos: fanart, eventos, galeria, pirateria, radio

El material original vive en JUANITO_SRC (por defecto E:\\Game Ever\\TRABAJOS\\Juanito)
y NUNCA se modifica: solo se abren los archivos para leer. Las salidas no llevan
metadatos (EXIF/GPS): se reescriben los píxeles en un archivo nuevo.

Los JSON de datos (src/data/*.json) los escribe este script a partir de las listas
curadas de abajo (selección manual de las mejores fotos/piezas).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

from PIL import Image, ImageOps

Image.MAX_IMAGE_PIXELS = None

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(os.environ.get("JUANITO_SRC", r"E:\Game Ever\TRABAJOS\Juanito"))
ASSETS = ROOT / "src" / "assets"
OUT = ASSETS / "archivo"
DATA = ROOT / "src" / "data"
RADIO_OUT = ROOT / "public" / "media" / "radio"
FFMPEG = ROOT / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe"
FFPROBE = ROOT / "tools" / "ffmpeg" / "bin" / "ffprobe.exe"


# ---------------------------------------------------------------- utilidades

def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.replace("\u200e", ""))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def src(rel: str) -> Path:
    p = SRC / rel
    if not p.exists():
        raise FileNotFoundError(p)
    return p


def open_image(path: Path) -> Image.Image:
    """Abre una imagen (jpg/png/psd) respetando la orientación EXIF."""
    if path.suffix.lower() == ".psd":
        from psd_tools import PSDImage
        img = PSDImage.open(path).topil()
    else:
        img = Image.open(path)
        img.load()
        img = ImageOps.exif_transpose(img)
    return img


def has_alpha(img: Image.Image) -> bool:
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        a = img.convert("RGBA").getchannel("A")
        return a.getextrema()[0] < 250
    return False


def fit(img: Image.Image, max_side: int) -> Image.Image:
    w, h = img.size
    if max(w, h) <= max_side:
        return img
    s = max_side / max(w, h)
    return img.resize((round(w * s), round(h * s)), Image.LANCZOS)


def export_image(srcrel: str | Path, outrel: str, max_side: int = 1600, crop=None,
                 fmt: str | None = None, quality: int = 85, huella: bool = False) -> str:
    """Exporta srcrel (relativo a SRC) a src/assets/<outrel sin extensión>.<jpg|png>.
    fmt=None: PNG si tiene transparencia real, JPG si no. Devuelve la ruta relativa
    a src/assets/ (con extensión) para los JSON.
    huella=True agrega al nombre 8 caracteres del hash del contenido (04-3fa9c1d2.jpg):
    si la imagen cambia, cambia la URL y ningún navegador muestra la versión vieja
    (el servidor de desarrollo de Astro cachea /_image por un año)."""
    path = srcrel if isinstance(srcrel, Path) else src(srcrel)
    img = open_image(path)
    if crop:
        if callable(crop):
            img = crop(img)
        else:
            img = img.crop(crop)
    alpha = has_alpha(img)
    if fmt is None:
        fmt = "png" if alpha else "jpg"
    img = fit(img, max_side)
    out = (ASSETS / outrel).with_suffix("." + fmt)
    out.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "jpg":
        if img.mode != "RGB":
            if alpha:
                bg = Image.new("RGB", img.size, (0, 0, 0))
                bg.paste(img.convert("RGBA"), mask=img.convert("RGBA").getchannel("A"))
                img = bg
            else:
                img = img.convert("RGB")
        # imagen nueva: sin exif, icc ni comentarios
        clean = Image.new("RGB", img.size)
        clean.paste(img)
        clean.save(out, "JPEG", quality=quality, optimize=True, progressive=True)
    else:
        img = img.convert("RGBA") if alpha else img.convert("RGB")
        clean = Image.new(img.mode, img.size)
        clean.paste(img)
        clean.save(out, "PNG", optimize=True)
    if huella:
        h = hashlib.sha1(out.read_bytes()).hexdigest()[:8]
        final = out.with_name(f"{out.stem}-{h}{out.suffix}")
        out.replace(final)
        out = final
    rel = out.relative_to(ASSETS).as_posix()
    print(f"  -> {rel}  {img.size}")
    return rel


def write_json(name: str, data) -> None:
    out = DATA / name
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"  => src/data/{name}  ({len(data)} items)")


def clean_dir(d: Path, exts=(".jpg", ".png", ".opus")) -> None:
    """Borra salidas viejas de este script (solo dentro del proyecto)."""
    if d.exists():
        for f in d.rglob("*"):
            if f.is_file() and f.suffix.lower() in exts:
                f.unlink()


# ------------------------------------------------------------------- radio

RADIO_DIR = "Prensa/Radios"

RADIOS = [
    {
        "id": "crack-60",
        "programa": "Crack #60",
        "emisora": "Radiolexia",
        "fecha": "2016-11-10",
        "audio": "Crack 10-10-2016/Crack 60 - Juanito Arcade - Videogame nacional.m4a",
        "img": "Crack 10-10-2016/crack_portada.png",
        "descripcion": "Entrevista a Game Ever sobre Juanito Arcade Mayhem en Crack, programa de "
                       "cultura alternativa conducido por Alejandro Caminos y Natalia Valchi, con la "
                       "columna gamer de Carlos Andrés Maidana.",
    },
    {
        "id": "fakin-vicio-005",
        "programa": "Fakin Vicio · Misión 005",
        "emisora": "Radio Monk",
        "fecha": "2017-03-11",
        "audio": "Fakin Vicio 11-03-2017/Fakin Vicio - Misión 005.m4a",
        "img": "Fakin Vicio 11-03-2017/fakin_portada.png",
        "descripcion": "Programa completo de Fakin Vicio, con Mauro Del Castillo, Iván «Taka» Salazar "
                       "y Martín Charruff Fadiga, que incluye el segmento en el que el equipo de Game Ever cuenta sobre Juanito Arcade Mayhem.",
    },
    {
        "id": "crack-84",
        "programa": "Crack #84",
        "emisora": "Radiolexia",
        "fecha": "2017-07-11",
        "audio": "Crack  11-07-2017/CRACK #84 Juanito Arcade 11-07-2017.m4a",
        "img": "Crack 10-10-2016/17155837_1271376789611839_1644823007496039515_n.jpg",
        "descripcion": "Segunda visita de Game Ever a Crack, el programa de cultura alternativa de "
                       "Radiolexia, a pocas semanas del lanzamiento de Juanito Arcade Mayhem en Steam.",
    },
    {
        "id": "overcast-24",
        "programa": "OverCast · Episodio 24",
        "emisora": "Radio LED",
        "fecha": "2017-07-15",
        "audio": "OverCluster 15-07-2017/OverCast - Episodio 24 - Entrevista Juanito Arcade y Review Black The Fall - OverCluster.mp3",
        "descripcion": "El podcast de OverCluster, con Damián Silberstein, Julián Chereque y Eduardo "
                       "Campastro, entrevista a Pablo Forconi de Game Ever sobre el inminente lanzamiento "
                       "de Juanito Arcade Mayhem (además, reseña de Black The Fall).",
    },
    {
        "id": "me-paso-en-sistemas-1",
        "programa": "Me Pasó En Sistemas (parte 1)",
        "emisora": "Facebook Live",
        "fecha": "2017-07-20",
        "audio": "Me Pasó En Sistemas - 20-07-2017/Me Pasó En Sistemas was live. - Me Pasó En Sistemas_1150354235108763.mp4",
        "descripcion": "Primera parte del vivo de Me Pasó En Sistemas en Facebook, con Juanito Arcade "
                       "Mayhem como tema, dos semanas antes de su salida en Steam.",
    },
    {
        "id": "me-paso-en-sistemas-2",
        "programa": "Me Pasó En Sistemas (parte 2)",
        "emisora": "Facebook Live",
        "fecha": "2017-07-20",
        "audio": "Me Pasó En Sistemas - 20-07-2017/Me Pasó En Sistemas was live. - Me Pasó En Sistemas_1150402591770594.mp4",
        "descripcion": "Segunda parte del vivo de Me Pasó En Sistemas en Facebook dedicado a Juanito "
                       "Arcade Mayhem.",
    },
    {
        "id": "radioactivo-delta",
        "programa": "Radioactivo",
        "emisora": "Delta 90.3 FM",
        "fecha": "2017-08-11",
        "audio": "Radioactivo - 11-08-2017/JAM_Delta_2017-08-15.wav",
        "img": "Radioactivo - 11-08-2017/Radio_Activo_984X275web-20f09e59ad.jpg",
        "descripcion": "En «un programa casi real», Angel Brozman, consultor de e-sports y startups del "
                       "programa, presenta Juanito Arcade Mayhem y a sus desarrolladores, días después "
                       "del lanzamiento en Steam.",
    },
]


def probe_duration(path: Path) -> float:
    out = subprocess.run([str(FFPROBE), "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", str(path)],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def fmt_dur(sec: float) -> str:
    s = round(sec)
    h, m, s = s // 3600, (s % 3600) // 60, s % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def transcode(inp: Path, out: Path, kbps: int) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(FFMPEG), "-hide_banner", "-loglevel", "error", "-y", "-i", str(inp),
                    "-vn", "-map_metadata", "-1", "-ac", "1", "-c:a", "libopus",
                    "-b:a", f"{kbps}k", "-application", "voip", str(out)], check=True)


def export_radio() -> None:
    print("radio")
    LIMIT = 25 * 1024 * 1024
    data = []
    for r in RADIOS:
        inp = src(f"{RADIO_DIR}/{r['audio']}")
        out = RADIO_OUT / f"{r['id']}.opus"
        if not (out.exists() and out.stat().st_size > 0 and os.environ.get("RADIO_SKIP_EXISTING")):
            for kbps in (24, 20, 16):
                transcode(inp, out, kbps)
                if out.stat().st_size < LIMIT:
                    break
                print(f"  ! {out.name} >= 25 MB a {kbps}k, bajando bitrate")
        dur = probe_duration(out)
        print(f"  -> public/media/radio/{out.name}  {out.stat().st_size / 1e6:.1f} MB  {fmt_dur(dur)}")
        item = {
            "id": r["id"],
            "programa": r["programa"],
            "emisora": r["emisora"],
            "fecha": r["fecha"],
            "duracion": fmt_dur(dur),
            "descripcion": r["descripcion"],
            "audio": f"/media/radio/{out.name}",
        }
        if r.get("img"):
            item["img"] = export_image(f"{RADIO_DIR}/{r['img']}", f"archivo/radio/{r['id']}", 1600)
        data.append(item)
    write_json("radio.json", data)


# ------------------------------------------------------------------ fanart

CONCURSO = "Concurso Fan-Art 2017"

# (archivo relativo a FanArt/, autor, título, fecha, origen)
FANART = [
    ("Ferando Almada/Juanito poster version B.png", "Fernando Almada", "Póster synthwave", "2017-06", CONCURSO),
    ("Aldana Ortiz.jpg", "Aldana Ortiz", "Juanito en la grilla neón", "2017-07", CONCURSO),
    ("Lucas Suarez.jpg", "Lucas Suárez", "Disparo eléctrico", "2017-07", CONCURSO),
    ("Federico Rivarola‎.jpg","Federico Rivarola", "Caricatura", "2017-07", CONCURSO),
    ("Tinot Pasticcino.jpg", "Tinot Pasticcino", "Juanito con lentes", "2017-07", CONCURSO),
    ("Belén Andrade.jpg", "Belén Andrade", "Juanito volando", "2017-07", CONCURSO),
    ("Sergio Gómez.jpg", "Sergio Gómez", "Acción en el arcade", "2017-07", CONCURSO),
    ("Emiliano Trevisano.jpg", "Emiliano Trevisano", "Fiebre de sábado en el laberinto", "2017-07", CONCURSO),
    ("Roque Macea.jpg", "Roque Macea", "El monstruo de un ojo", "2017-07", CONCURSO),
    ("Santiago R. Villa.jpg", "Santiago R. Villa", "Carta coleccionable", "2017-07", CONCURSO),
    ("Facu Arlequín.jpg", "Facu Arlequín", "Juanito y la clonocélula", "2017-07", CONCURSO),
    ("Carolina Bu.jpg", "Carolina Bu", "Juanito en Pac-Man", "2017-07", CONCURSO),
    ("Chona Falanje Urquiza.jpg", "Chona Falanje Urquiza", "¡Piuu piuu!", "2017-07", CONCURSO),
    ("Pablo Yungblut.jpg", "Pablo Yungblut", "Siesta gamer", "2017-07", CONCURSO),
    ("Martín Sebastián Wain.jpg", "Martín Sebastián Wain", "Clonocélula gigante", "2017-07", CONCURSO),
    ("Martin Dasnoy.jpg", "Martín Dasnoy", "Juanito y Gluk en acuarela", "2017-07", CONCURSO),
    ("Mer Grazzini.jpg", "Mer Grazzini", "Juanito en acuarela", "2017-07", CONCURSO),
    ("Megawacky Max.jpg", "Megawacky Max", "Huyendo de una larva", "2017-07", CONCURSO),
    ("Gaston Boquel.jpg", "Gastón Boquel", "Juanito y Gluk a la carrera", "2017-07", CONCURSO),
    ("Juan Camilo Salamanca 1.jpg", "Juan Camilo Salamanca", "Juanito 3D sobre el arcade", "2017-07", CONCURSO),
    # "Juan Camilo Salamanca 2.jpg" ("Juanito 3D en el espacio") se sacó a pedido del dueño
    ("Kurara Himura.jpg", "Kurara Himura", "Juanita", "2017-07", CONCURSO),
    ("Luisito Rodriguez.jpg", "Luisito Rodríguez", "Juanito barbudo", "2017-07", CONCURSO),
    ("Mariano Lo Prete.jpg", "Mariano Lo Prete", "El trono de Pac-Man", "2017-07", CONCURSO),
    ("Martin Asteasuain.jpg", "Martín Asteasuain", "Juanito en pixel art", "2017-07", CONCURSO),
    ("David Brun.jpg", "David Brun", "Pop art", "2017-07", CONCURSO),
    ("Federico Abrigo.jpg", "Federico Abrigo", "Juanito pelirrojo", "2017-07", CONCURSO),
    ("Ikki Ari.jpg", "Ikki Ari", "Lápiz y marcador", "2017-07", CONCURSO),
    ("Bianca Papalardo.jpg", "Bianca Papalardo", "Disparo verde", "2017-07", CONCURSO),
    ("Richar Meza.jpg", "Richar Meza", "Cara a cara con el monstruo", "2017-07", CONCURSO),
    ("Pablo Sanchez.jpg", "Pablo Sánchez", "Mini pixel art", "2017-07", CONCURSO),
    ("Aleksander Youkovibch 1.jpg", "Aleksander «Alek» Youkovibch", "Juanito contra el Clonojefe", "2018-04", None),
    ("Aleksander Youkovibch 2.jpg", "Aleksander «Alek» Youkovibch", "Juanito y Gluk en modo cooperativo", "2018-04", None),
]

PIXEL_ART = {"Pablo Sanchez.jpg"}  # se agranda x4 sin suavizar


# Dibujos de chicos: van en su propio bloque ("Mini fans") en la galería
MINI_FANS = {"Aleksander Youkovibch 1.jpg", "Aleksander Youkovibch 2.jpg"}


def export_fanart() -> None:
    print("fanart")
    clean_dir(OUT / "fanart")
    data, used = [], {}
    for rel, autor, titulo, fecha, origen in FANART:
        base = slugify(autor.split("(")[0])
        used[base] = used.get(base, 0) + 1
        n = sum(1 for r in FANART if slugify(r[1].split("(")[0]) == base)
        slug = f"{base}-{used[base]}" if n > 1 else base
        path = src(f"FanArt/{rel}")
        if rel in PIXEL_ART:
            img = open_image(path).convert("RGB")
            img = img.resize((img.width * 4, img.height * 4), Image.NEAREST)
            out = OUT / "fanart" / f"{slug}.png"
            out.parent.mkdir(parents=True, exist_ok=True)
            img.save(out, "PNG", optimize=True)
            img_rel = out.relative_to(ASSETS).as_posix()
            print(f"  -> {img_rel}  {img.size}")
        else:
            img_rel = export_image(path, f"archivo/fanart/{slug}", 1600, fmt="jpg")
        item = {"img": img_rel, "autor": autor, "titulo": titulo, "fecha": fecha}
        if origen:
            item["origen"] = origen
        if rel in MINI_FANS:
            item["mini"] = True
        data.append(item)
    write_json("fanart.json", data)


# ----------------------------------------------------------------- eventos
# Fechas corregidas según el inventario (docs/material/02-difusion-prensa-fotos.md):
# los nombres de carpeta DD-MM a veces están mal; mandan el flyer o el EXIF.

EV = "Difusion/Eventos"
# Piezas que el dueño rehízo o adaptó y pasó aparte (no están en E:)
ORIG = ROOT / "tools" / "originales"


def _f(folder: str, *names: str) -> list[str]:
    return [f"Fotos/{folder}/{n}" for n in names]


IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def _natural(s: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", s)]


def _sueltas(folder: str, excluir: tuple[str, ...] = ()) -> list[str]:
    """Selección del dueño: las fotos sueltas de Fotos/<folder>. Las subcarpetas
    (por ejemplo "No/") no se publican. Un archivo llamado "cover.*" va primero:
    es la portada de la tarjeta cuando el evento no tiene flyer (si tiene, queda
    como primera foto del álbum). `excluir`: sueltas que el dueño pidió sacar
    (E: es solo lectura para el exportador, así que no se pueden mover a No/)."""
    d = SRC / "Fotos" / folder
    files = [p.name for p in d.iterdir()
             if p.is_file() and p.suffix.lower() in IMG_EXT and p.name not in excluir]
    files.sort(key=lambda n: (not n.lower().startswith("cover."), _natural(n)))
    return _f(folder, *files)


EVENTOS = [
    dict(slug="meet-the-game-2014", nombre="Meet The Game", fecha="2014-05-10",
         lugar="Fusion Bar, Florida 328, CABA",
         descripcion="Primera edición de la expo de videojuegos argentinos de Gamedia. Juanito se pudo jugar en tablets y en una notebook con joystick.",
         flyer=ORIG / "eventos" / "meet-the-game-2014-flyer.jpg",  # versión cuadrada del dueño (antes: MTG_v1.jpg)
         fotos=_sueltas("2014/12-05 - Meet The Game 1")),
    dict(slug="toronjapalooza-2014", nombre="Toronjapalooza", fecha="2014-07-26",
         lugar="Espacio Cultural Chacra de los Remedios, Parque Avellaneda, CABA",
         descripcion="«Evento cultural nerd» con demo de Juanito en tablet.",
         flyer=ORIG / "eventos" / "toronjapalooza-2014-flyer.jpg",  # versión cuadrada del dueño (antes: Afiche_Toronjapalooza.png)
         fotos=_sueltas("2014/06-08 - Toronjapalooza")),
    dict(slug="eva-2014", nombre="EVA 2014", fecha="2014-11-07",  # 7 y 8 de noviembre (Neoteo)
         lugar="Espacio Gaumont, CABA",
         descripcion="Exposición de Videojuegos Argentina: stand de Game Ever en el Espacio Indie.",
         fotos=_sueltas("2014/08-11 - EVA"),
         # tarjeta: recorte cuadrado de cover.png (la tablet), según la referencia del dueño
         portada_crop=(472, 184, 1222, 934)),
    dict(slug="meet-the-game-2", nombre="Meet The Game 2", fecha="2014-11-16",
         lugar="Centro Cultural San Martín, Sarmiento 1551, CABA",
         descripcion="Segunda edición de la expo de Gamedia. Juanito se jugó en PC, con premio para el mejor puntaje: un trofeo con forma de cartucho de Famicom. Ahí Pablo Forconi le habló a Nivel Xtremo, cuando el juego todavía se llamaba «Juanito Game».",
         flyer=f"{EV}/Meet The Game 2 2015/MTG_2_v1.png",
         fotos=_sueltas("2014/08-08 - Meet The Game 2")),
    dict(slug="feria-del-libro-2015", nombre="Feria Internacional del Libro de Buenos Aires", fecha="2015-04-23",
         lugar="La Rural, Pabellón Azul, stand 225",
         descripcion="Del 23 de abril al 11 de mayo, el gabinete arcade de Juanito se pudo jugar en plena feria, entre libros, cómics y peluches.",
         flyer=f"{EV}/Feria Libro 2015/Feria_Juanito.png",
         fotos=_f("2015/24-04 - Feria del Libro",
                  "11041732_716213611823091_1367413272972892951_n.jpg",
                  "11160575_716213735156412_3430791138622533342_n.jpg",
                  "11164148_10205201903179798_909209003_n.jpg",
                  "11185728_10205201907179898_2103408271_n.jpg",
                  "Juanito.jpg")),
    dict(slug="tecnopolis-2015", nombre="Tecnópolis 2015: Ar.Cade", fecha="2015-07-20",  # fotos del 20/07; la muestra siguió hasta nov.
         lugar="Tecnópolis, Villa Martelli",
         descripcion="Juanito formó parte de Ar.Cade, el catálogo jugable de videojuegos argentinos de la sala azul. Chicos haciendo fila para salvar los clásicos.",
         fotos=[ORIG / "eventos" / "tecnopolis-2015-equipo.jpg"] + _f("2015/20-07 - Tecnopolis", "01.jpg", "03.jpg", "05.jpg", "06.jpg", "08.jpg", "09.jpg", "10.jpg", "13.jpg"),
         # tarjeta: cover cuadrado del dueño (recorte de 01.jpg); el álbum muestra la captura entera
         portada_img=ORIG / "eventos" / "tecnopolis-2015-cover.jpg"),
    dict(slug="meet-the-devs-2015", nombre="Meet The Devs: Extended Edition", fecha="2015-08-15",
         lugar="Centro Cultural San Martín, Sarmiento 1551, CABA",
         descripcion="Evento de Gamedia con el gabinete arcade de Juanito.",
         flyer=f"{EV}/Meet The Devs Extended 2015/Meet_Devs_Ext_v1.jpg",
         fotos=_sueltas("2015/16-08 - Meet The Devs Extended Edition")),
    dict(slug="mica-2015", nombre="MICA 2015", fecha="2015-09-06",
         lugar="CABA",
         descripcion="Mercado de Industrias Culturales Argentinas: Juanito en el espacio «Videojuegos Argentinos».",
         fotos=_sueltas("2015/02-09 - MICA"),
         # tarjeta: cuadrado de cover.JPG con la pantalla del juego y la chica que juega
         portada_crop=(1525, 413, 3988, 2876)),
    dict(slug="bit-bang-fest-2", nombre="Bit Bang Fest 2", fecha="2015-09-12",  # segunda edición (Culturageek, 02/09/2015)
         lugar="Escuela Da Vinci, Av. Corrientes 2049, CABA",
         descripcion="El festival de la Escuela Da Vinci: juegos indie argentinos para probar y votar, charlas, juegos de mesa y rol. Y una multitud alrededor del arcade de Juanito.",
         fotos=_sueltas("2015/15-09 - Bit Bang Fest Edicion 2"),
         # tarjeta: cuadrado de cover.jpg (vertical): marquesina, pantalla y la mano en los controles
         portada_crop=(0, 55, 640, 695)),
    dict(slug="animacity-2015", nombre="Animacity 2015", fecha="2015-10-04",
         lugar="Colegio San José, Bartolomé Mitre 2455, CABA",
         descripcion="Entre cosplayers y fans del animé, el gabinete de Juanito no se quedó solo ni un minuto.",
         fotos=_sueltas("2015/04-10 - Animacity"),
         # tarjeta: recorte cuadrado de cover.png (versión verde), con foco en el gabinete y el que juega
         portada_crop=(342, 205, 1122, 985)),
    dict(slug="eva-2015", nombre="EVA 2015", fecha="2015-11-06",  # 6 y 7 de noviembre (Culturageek)
         lugar="Espacio Gaumont, CABA",
         descripcion="Flyer «Mini Arcade» preparado para la Exposición de Videojuegos Argentina 2015.",
         flyer=ORIG / "eventos" / "eva-2015-flyer.jpg", fotos=[]),  # versión cuadrada del dueño (antes: Mini_Arcade_v1.png)
    dict(slug="muere-monstruo-muere-2015", nombre="Muere Monstruo Muere", fecha="2015-10-30",
         lugar="Teatro El Mandril, Humberto 1° 2758, San Cristóbal",
         descripcion="Fiesta con bandas (Nave, Jupitron, Shitty) y arcades, con Juanito en pantalla.",
         flyer=f"{EV}/Muere Monstruo Muere 2015/Muere_Monstruo_Muere_v1.png",
         fotos=_sueltas("2015/30-10 - Muere Monstruo Muere")),
    dict(slug="meet-the-game-3", nombre="Meet The Game 3: Rise of the Devs", fecha="2015-11-14",
         lugar="Centro Cultural San Martín, Sarmiento 1551, CABA",
         descripcion="Tercera edición de la expo de Gamedia, con el arcade de Juanito junto a otros juegos argentinos.",
         flyer=f"{EV}/Meet The Game 2015/Meet_Devs_Game_2015.png",
         fotos=_sueltas("2015/20-11 - Meet The Game 3")),
    dict(slug="muere-monstruo-muere-1-ano", nombre="Muere Monstruo Muere: cumple 1 año", fecha="2015-11-27",
         lugar="Teatro El Mandril, San Cristóbal",
         descripcion="«Película + arcades + banda + mucho más». En la puerta se vendían los pósters de Juanito a $25.",
         flyer=f"{EV}/Muere Monstruo Muere 2015 1 Año/Muere_Monstruo_Muere_v1.png",
         fotos=_sueltas("2015/27-11 - Muere Monstruo Muere")),
    dict(slug="checkpoint-2015", nombre="Checkpoint: fiesta de fin de año", fecha="2015-12-12",
         lugar="TecnoBar, Fitz Roy 2021, Palermo",
         descripcion="Fiesta de fin de año «junto a Juanito», con flyer protagonizado por él.",
         flyer=f"{EV}/Checkpoint 2015/Checkpoint_2015_v1.png", fotos=[]),
    dict(slug="geek-out-fest-2", nombre="Geek Out! Fest 2.0", fecha="2016-04-30",
         lugar="Centro Cultural San Martín, Sarmiento 1551, CABA",
         descripcion="«Vení a jugar»: el arcade de Juanito en el festival de juegos de mesa y cultura geek. Dato de color: entre los sponsors figuraba El Dragón Azul, la editorial que seis años después haría el juego de mesa.",
         flyer=ORIG / "eventos" / "geek-out-fest-2-flyer.jpg",  # versión cuadrada del dueño (antes: Geek Out 2016/Mini_Arcade_v1.png)
         fotos=_f("2016/30-04 - Geek Out Fest",
                  "13090416_10206618021554524_1099661509_n.jpg",
                  "13091603_10206618029434721_274299374_o.jpg",
                  "13105942_10206618026754654_668237804_o.jpg",
                  "13128720_10206618030714753_465319581_o.jpg",
                  "13147898_10206618027114663_620699228_o.jpg",
                  "20160430_153637.jpg", "IMG_20160430_180614280.jpg", "IMG_20160430_180652309.jpg")),
    dict(slug="meet-the-devs-2016", nombre="Meet The Devs Extended 2016", fecha="2016-05-21",
         lugar="CABA",
         descripcion="Charlas de videojuegos, realidad virtual, juegos indie y arcades.",
         fotos=_sueltas("2016/21-05 - Meet The Devs"),
         # tarjeta: cuadrado de cover.png con la pantalla, la mano en el botón y la cara de la que juega
         portada_crop=(420, 0, 1410, 990)),
    dict(slug="nave-100", nombre="NAVE Arcade Tour #100", fecha="2016-06-11",  # festival Let It VJ (posts de Argentron)
         lugar="Club Cultural Matienzo, Pringles 1249, CABA",
         descripcion="Cien fechas del arcade itinerante NAVE, de Videogamo, se festejaron en el Matienzo durante el festival Let It VJ. Y Juanito no se lo quiso perder.",
         fotos=_sueltas("2016/15-06 - Nave 100"),
         # tarjeta: cuadrado de cover.jpg (foto nocturna con luz violeta): marquesina, pantalla y el que juega
         portada_crop=(270, 0, 953, 683)),
    dict(slug="fichinait-2016", nombre="Fichinait", fecha="2016-08-13",
         lugar="La Comunidad del Sótano, Nicasio Oroño 2480, CABA",
         descripcion="Fiesta gamer de La Comunidad del Sótano con Tumba, Argentron Arcade, The Black Heart, Metadron, Nave y Juanito, entre otros.",
         flyer=f"{EV}/Fichinait 2016/13886244_1448803045136629_7787626712625036484_n.jpg",
         fotos=_f("2016/16-08 - Fichinait", "20160814_015230.jpg", "20160814_025030.jpg")),
    dict(slug="fiesta-pow-1", nombre="Fiesta Pow 1", fecha="2016-11-04",
         descripcion="El arcade de Juanito en una fiesta, con grupos jugando hasta tarde.",
         fotos=_sueltas("2016/04-11 - Fiesta Pow 1"),
         # tarjeta: cuadrado de cover.jpg con el que juega, la marquesina y la pantalla encendida
         portada_crop=(323, 0, 1403, 1080)),
    dict(slug="eva-2016", nombre="EVA 2016", fecha="2016-11-04",  # 4 y 5 de noviembre (Culturageek)
         lugar="C3, Centro Cultural de la Ciencia, Godoy Cruz 2270, CABA",
         descripcion="El gabinete de Juanito volvió a la Exposición de Videojuegos Argentina, con mucho público y la tabla de récords en pantalla.",
         fotos=_sueltas("2016/08-11 - EVA"),
         # tarjeta: cuadrado de cover.png con la pantalla del ranking y la cara del jugador reflejada
         portada_crop=(106, 279, 913, 1086)),
    dict(slug="test-fest-2016", nombre="Juanito Test Fest", fecha="2016-11-15",  # fotos de cámara del 15/11; tarjetas impresas el 14/11
         oculto=True,  # oculto hasta tener más información (pedido del dueño)
         descripcion="Sesión de testeo abierta del juego. Cada tester se llevaba una tarjeta: «¡Gracias por ser parte del Testing de Juanito!».",
         flyer="Difusion/Facebook/Eventos/Test Fest/juanito_test_fest_banner_v2.jpg",
         fotos=["Difusion/Facebook/Eventos/Test Fest/juanito_test_fest_banner_v1.jpg",
                "Difusion/Facebook/Eventos/Test Fest/JuanitoA4.png"]),
    dict(slug="muere-monstruo-muere-2016", nombre="Muere Monstruo Muere: 2 años de amor", fecha="2016-11-11",
         lugar="Teatro El Mandril, San Cristóbal",
         descripcion="Segundo aniversario de la fiesta, con flyer protagonizado por Juanito: «Película + arcades + feria».",
         flyer=f"{EV}/11-16 - Muere Monstrue Muere/11-16_Muere_Monstruo_Muere_v1.jpg",
         fotos=_sueltas("2016/11-11 - Muere Monstruo Muere")),
    dict(slug="geek-out-fest-3", nombre="Geek Out! Fest 3.0", fecha="2017-05-06",
         lugar="Centro Cultural San Martín, Sarmiento 1551, CABA",
         descripcion="El arcade de Juanito, muy jugado por chicos, y una mesa de juegos argentinos junto a JuegosArgentinos.org.",
         fotos=_sueltas("2017/06-MAY - Geek Out Fest 3.0"),
         # tarjeta: cuadrado de cover.jpg centrado en el juego (marquesina y pantalla) y la chica que juega
         portada_crop=(884, 624, 2600, 2340)),
    dict(slug="fichinait-2", nombre="Fichinait Vol. 2", fecha="2017-05-06",
         lugar="La Comunidad del Sótano, Nicasio Oroño 2480, CABA",
         descripcion="Segunda fiesta Fichinait: arcades hasta la madrugada y un récord de 50:18 minutos en Juanito.",
         fotos=_sueltas("2017/06-MAY - Fichinait Vol.2",
                        excluir=("20170507_012318.jpg",)),  # casi igual a 20170507_012323.jpg
         # tarjeta: cuadrado de cover.jpeg con la pantalla (puntaje y combo) y las manos en los controles
         portada_crop=(890, 0, 2730, 1840)),
    dict(slug="triple-fest-2017", nombre="Triple Fest", fecha="2017-08",
         oculto=True,  # oculto hasta tener más información (pedido del dueño)
         descripcion="Banner compartido de Juanito con Fidel (Dungeon Rescue) y Bildo, otros juegos argentinos.",
         flyer="Difusion/Facebook/Eventos/Triple Fest/juanito_test_fest_banner_v1.jpg", fotos=[]),
    dict(slug="random-tandil-2017", nombre="Random: Convención de Freaks, Volumen II", fecha="2017-08-19",
         oculto=True,  # oculto hasta tener más información (pedido del dueño)
         lugar="Altos de Unión, Quintana 450, Tandil",
         descripcion="Convención auspiciada por el Municipio de Tandil, con el salón lleno.",
         flyer="Fotos/2017/19-AGO - Random (Tandil)/20451593_1862004497450620_404895491845680858_o.jpg",
         fotos=_f("2017/19-AGO - Random (Tandil)", "20989196_1872293159755087_6741567074557061669_o.jpg")),
    dict(slug="geek-out-fest-4", nombre="Geek Out! Fest 4.0", fecha="2018-04-28",
         lugar="Centro Cultural San Martín, Sarmiento 1551, CABA",
         descripcion="Sede argentina del International Tabletop Day, junto a JuegosArgentinos.org.",
         flyer=ORIG / "eventos" / "geek-out-fest-4-flyer.jpg",  # versión cuadrada del dueño del flyer oficial (GeekOutFest4.jpg)
         # Geek-Out-Fest-4.jpg ("Sábado 30 de abril") no es de esta edición: el 30/04/2018 fue lunes
         fotos=[]),
    dict(slug="arcade-evento-2018", nombre="ARCADE Evento", fecha="2018", orden="2018-07",
         pedir_datos=True,  # no se sabe qué evento fue ni dónde: se piden datos (texto en la tarjeta)
         fotos=_sueltas("2018/ARCADE Evento"),
         # tarjeta: cuadrado de cover.jpg con el gabinete, el jugador y el mural de fondo
         portada_crop=(60, 190, 660, 790)),
    dict(slug="primer-aniversario-2018", nombre="Juanito cumple su primer añito", fecha="2018-08-10",
         oculto=True,  # oculto por ahora (pedido del dueño)
         lugar="Zapiola 2450, Belgrano, CABA",
         descripcion="Fiesta por el primer aniversario del lanzamiento en Steam.",
         flyer="Difusion/Facebook/Varios/primer_anio_v1.jpg", fotos=[]),
    # Sin fotos todavía. Fuente: indiehoy.com/agenda/fichinait-vol-3-fiesta-videojuegos-la-comunidad-del-sotano
    # (anuncia "Juanito Arcade" entre las máquinas)
    dict(slug="fichinait-3", nombre="Fichinait Vol. 3", fecha="2017-10-07",
         lugar="La Comunidad del Sótano, Nicasio Oroño 2480, CABA",
         descripcion="Tercera fiesta Fichinait: Juanito volvió al Sótano, esta vez junto a NAVE y Super Proyecto Isaac.",
         flyer=ORIG / "eventos" / "fichinait-3-flyer.jpg",  # flyer oficial, tomado de la nota de IndieHoy (380 px)
         fotos=[]),
    # Sin fotos todavía. Fuente: davinci.edu.ar/eventos/detalle/bit-bang-fest-videojuegos-2018
    # (Juanito figura en la sección "Arcades")
    dict(slug="bit-bang-fest-2018", nombre="Bit Bang Fest 2018", fecha="2018-08-25",
         lugar="Escuela Da Vinci, Av. Corrientes 2037, CABA",
         descripcion="Juanito volvió al festival de la Escuela Da Vinci como uno de sus arcades, con un año en Steam y recién salido en celulares.",
         # key art de la edición (nota de Culturageek, 08/2018), versión cuadrada del dueño
         flyer=ORIG / "eventos" / "bit-bang-fest-2018-flyer.jpg",
         fotos=[]),
]

# recortes especiales: la hoja A4 de Test Fest tiene 4 tarjetas iguales; queda una.
EV_CROP = {
    "Difusion/Facebook/Eventos/Test Fest/JuanitoA4.png": lambda im: im.crop((0, 0, im.width // 2, im.height // 2)),
}


def export_eventos() -> None:
    print("eventos")
    clean_dir(OUT / "eventos")
    data = []
    for e in sorted(EVENTOS, key=lambda e: e.get("orden", e["fecha"])):
        print(f" {e['slug']}")
        item = {"slug": e["slug"], "nombre": e["nombre"], "fecha": e["fecha"]}
        if e.get("lugar"):
            item["lugar"] = e["lugar"]
        if e.get("descripcion"):
            item["descripcion"] = e["descripcion"]
        if e.get("oculto"):
            item["oculto"] = True
        if e.get("pedir_datos"):
            item["pedirDatos"] = True
        if e.get("flyer"):
            item["flyer"] = export_image(e["flyer"], f"archivo/eventos/{e['slug']}/flyer", 1600, fmt="jpg",
                                         crop=EV_CROP.get(e["flyer"]), huella=True)
        fotos = []
        for i, f in enumerate(e["fotos"], 1):
            fotos.append(export_image(f, f"archivo/eventos/{e['slug']}/{i:02d}", 1600, fmt="jpg",
                                      crop=EV_CROP.get(f), huella=True))
        item["fotos"] = fotos
        # recorte para la tarjeta, sacado de la primera imagen (flyer o cover); el álbum
        # sigue mostrando la imagen entera, así la foto no se repite
        if e.get("portada_crop"):
            primera = e.get("flyer") or e["fotos"][0]
            item["portada"] = export_image(primera, f"archivo/eventos/{e['slug']}/portada", 1200, fmt="jpg",
                                           crop=e["portada_crop"], quality=88, huella=True)
        # o una portada armada aparte por el dueño (solo para la tarjeta, no entra al álbum)
        elif e.get("portada_img"):
            item["portada"] = export_image(e["portada_img"], f"archivo/eventos/{e['slug']}/portada", 1200,
                                           fmt="jpg", quality=88, huella=True)
        data.append(item)
    write_json("eventos.json", data)


# ----------------------------------------------------------------- galería
# (fuente, slug, título, categoría, fecha | None, descripción | None, opciones)
# opciones: max (lado mayor), crop (caja o función), fmt

GL_CROP = (340, 92, 1320, 1008)  # capturas de Greenlight: solo el contenido de la página


def _website_2014() -> Image.Image:
    """Reconstruye la landing 'Coming soon' de 2014 uniendo los cortes de la tabla HTML."""
    d = "Difusion/Website/img"
    rows = [["01"], ["02"], ["03"], ["04"], ["05", "06"], ["07", "08"], ["09"], ["10"]]
    tiles = [[open_image(src(f"{d}/coming_{n}.jpg")).convert("RGB") for n in r] for r in rows]
    h = sum(r[0].height for r in tiles)
    canvas = Image.new("RGB", (960, h), (0, 0, 0))
    y = 0
    for r in tiles:
        x = 0
        for t in r:
            canvas.paste(t, (x, y))
            x += t.width
        y += r[0].height
    return canvas


TN_TECNO = "Prensa/Video/TN Tecno/TN Tecno Fragmento.mp4"


def _cuadro(video: str, seg: float):
    """Devuelve una función que saca un cuadro del video (relativo a SRC) en el segundo seg."""
    def sacar() -> Image.Image:
        r = subprocess.run([str(FFMPEG), "-hide_banner", "-loglevel", "error", "-ss", str(seg), "-i", str(src(video)),
                            "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "-"],
                           check=True, capture_output=True)
        from io import BytesIO
        return Image.open(BytesIO(r.stdout)).convert("RGB")
    return sacar


GALERIA = [
    # --- afiches históricos (2012-2014) y pósters
    ("Difusion/Posters/Retro/juanito_poster_vintage_01.jpg", "retro-dubi-juanito-gluk",
     "Dubi · Juanito · Gluk", "afiche", "2012",
     "Póster retro estilo cine clase B, de cuando el proyecto todavía se llamaba «Juanito vs. las Clonocélulas Mutantes del Espacio Exterior».",
     {"oculto": True}),  # fuera de la galería (pedido del dueño)
    ("Difusion/Posters/Retro/Poster_v2.jpg", "retro-poster-v2",
     "Póster retro", "afiche", None, "Variante vintage del afiche, con Juanito, Gluk y el gorila.", {"oculto": True}),
    ("Difusion/Posters/Logo/logo_cielo_v1.jpg", "logo-en-el-cielo",
     "Logo en el cielo", "afiche", "2012-05-28",
     "El logo original: «Juanito vs. las Clonocélulas Mutantes del Espacio Exterior».", {}),
    ("Difusion/Posters/Clasico/poster_2.jpg", "poster-clasico",
     "Póster clásico", "afiche", "2012-12-04", "Juanito, Gluk y Dubi en la versión clásica del afiche.", {}),
    ("Difusion/Posters/Ascii/sujeto_localizado_v1b.png", "ascii-codename-juanito",  # versión del dueño (antes: sujeto_localizado_v1.jpg)
     "Subject Localized · Codename: Juanito", "afiche", "2012-12-10",
     "Póster ASCII: el informe alienígena que localiza al «sujeto» Juanito.", {}),
    ("Difusion/Posters/Incaa/Poster_Incaa_v1.jpg", "incaa-clonocelulas",
     "Juanito vs. las Clonocélulas Mutantes del Espacio Exterior", "afiche", "2014",
     "Póster preparado para la presentación del proyecto al INCAA.", {"oculto": True}),
    ("Difusion/Posters/Screens/Screens-Landscape-01.jpg", "screens-01",
     "Screens 1", "afiche", None, None, {"serie": "screens"}),
    ("Difusion/Posters/Screens/Screens-Landscape-02.jpg", "screens-02",
     "Screens 2", "afiche", None, None, {"serie": "screens"}),
    ("Difusion/Posters/Screens/Screens-Landscape-04.jpg", "screens-04",
     "Screens 3", "afiche", None, None, {"serie": "screens"}),
    ("Difusion/Posters/Screens/Screens-Landscape-05jpg.jpg", "screens-05",
     "Screens 4", "afiche", None, None, {"serie": "screens"}),
    ("Difusion/Posters/Varios/Poster_Landscape_v1.jpg", "poster-landscape",
     "Póster apaisado", "afiche", None, None, {"serie": "screens"}),
    ("Difusion/Posters/Varios/Poster_v3.2.png", "poster-v3",
     "Póster con cita de prensa", "afiche", None, None, {"max": 2000}),
    ("Difusion/Posters/Varios/juanito_poster_limpio_01.jpg", "poster-limpio",
     "Juanito vs. las Clonocélulas (arte limpio)", "afiche", None, None, {}),

    # --- pósters Super A3 (sección propia) y merch (solo remeras; el panfleto y el sticker quedan ocultos)
    ("Difusion/Merch/Super A3/Poster_Generico_SA.png", "poster-super-a3-generico",
     "El clásico de clásicos", "posters", None, None, {"max": 2000}),
    ("Difusion/Merch/Super A3/Poster_Donkey_SA.png", "poster-super-a3-el-mono",
     "El gorila Trevor", "posters", None, None, {"max": 2000}),
    ("Difusion/Merch/Super A3/Poster_ET_SA.png", "poster-super-a3-et-dedo",
     "El dedito extraterrestre", "posters", None, None, {"max": 2000}),
    ("Difusion/Merch/Posters_Panfleto_v3.png", "panfleto-posters",
     "¡Adquiera ya! su póster de Juanito", "merch", "2015-11",
     "Panfleto de venta: tres modelos de póster a $25 cada uno, edición limitada, «buscanos en la puerta (o por ahí)».", {"max": 2000, "oculto": True}),
    ("Difusion/Merch/Super A3/Poster_Donkey_Sticker.png", "sticker-donkey",
     "Sticker de Donkey", "merch", "2015", None, {"oculto": True}),
    ("Difusion/Merch/Remeras/Remera_Opcion_A.jpg", "remera-a",
     "Remera (opción A)", "merch", None, "Diseño de remera negra con Juanito al frente.", {}),
    ("Difusion/Merch/Remeras/Remera_Opcion_B.jpg", "remera-b",
     "Remera (opción B)", "merch", None, "Diseño de remera negra con el logo.", {}),

    # --- piezas promocionales
    (ORIG / "difusion/dia-del-nino.webp", "dia-del-nino-2014",  # versión del dueño
     "Día del Niño", "promo", "2014-08", "«Nunca te olvides de tu Juanito interior».", {}),
    (ORIG / "difusion/puro-games.webp", "puro-games",  # versión del dueño
     "Crossover con Puro Games", "promo", "2014-08", "Juanito con caricaturas de los conductores del programa Puro Games.", {}),
    (ORIG / "difusion/the-hum.webp", "the-hum",  # versión del dueño
     "Crossover con The Hum", "promo", "2014-08", None, {}),
    (ORIG / "difusion/halloween-2014.webp", "halloween-2014",  # versión del dueño
     "Halloween 2014", "promo", "2014-10", None, {}),
    (ORIG / "difusion/navidad-2014.webp", "navidad-2014",  # versión del dueño
     "Navidad 2014", "promo", "2014-12", None, {}),
    ("Difusion/Promocional/Martes 13/halo.png", "halloween-2015",
     "Halloween 2015", "promo", "2015-10", None, {"oculto": True}),  # fuera de la galería (pedido del dueño)
    ("Difusion/Promocional/Navidad 2015/Navidad 2015.png", "navidad-2015",
     "Navidad 2015", "promo", "2015-12", "¡Felices fiestas!", {}),
    (ORIG / "difusion/afiche-twitter.webp", "afiche-twitter",  # versión del dueño
     "¿Vos ya lo seguís en Twitter?", "promo", None, None, {}),
    (ORIG / "difusion/celestineia.webp", "celestineia",  # versión del dueño
     "Juanito y Celestineia", "promo", None, None, {}),
    ("Difusion/Facebook/Varios/juanito_release_dat.png", "fecha-de-salida",
     "Fecha de salida: 3 de agosto", "promo", "2017-05-18", "El anuncio de la fecha de lanzamiento en Steam.", {"fmt": "jpg"}),
    ("Difusion/Facebook/Varios/MPVJP_2017.png", "gracias-adva",
     "¡Muchas gracias, ADVA!", "promo", "2017-06-13",
     "El agradecimiento por la selección en «Mi Primer Videojuego Publicado II»: Juanito jugando al Pong en la tele.", {"fmt": "jpg"}),
    ("Difusion/Facebook/Varios/juanito_radio_v1b.png", "juanito-radio",  # versión del dueño
     "¡Hoy Juanito va a la radio!", "promo", "2017-06", None, {"fmt": "jpg"}),
    ("Difusion/Facebook/Varios/concurso_dibujo_02b.png", "concurso-fan-art",  # versión del dueño (antes: concurso_dibujo_02.png)
     "Concurso Fan-Art", "promo", "2017-06-19", "«Queremos ver a Juanito en tu estilo».", {"fmt": "jpg"}),
    ("Difusion/Steam/now_available_01b.png", "now-available-steam",  # versión del dueño (antes: now_available_01.png)
     "Now available on Steam", "promo", "2017-08-03", "Pieza del lanzamiento en Steam.", {}),
    ("Difusion/Facebook/Varios/sonico_cosplay_v1b.png", "sonic-mania",  # versión del dueño
     "Felicitaciones a Sonic Mania", "promo", "2017-08", "Juanito vestido de Sonic y Gluk de Tails, para saludar al equipo de Sonic Mania.", {"fmt": "jpg"}),
    ("Difusion/Facebook/Varios/mercadolibre_v1b.png", "mercado-libre",  # versión del dueño
     "Conseguilo por Mercado Libre", "promo", "2017-08", "«¡En pesos argentinos!».", {"fmt": "jpg"}),
    ("Difusion/Facebook/Varios/concurso_pijama_v1.jpg", "concurso-pijama",
     "Mandanos tu foto en pijama", "promo", "2017-08-29", "Concurso en Facebook: una foto en pijama a cambio de códigos del juego.", {}),
    ("Difusion/Promocional/Halloween 2017/fb_halloween_update_v1.jpg", "halloween-2017",
     "Halloween update", "promo", "2017-10-25", None, {}),
    ("Difusion/Facebook/Varios/navidad_2018.jpg", "navidad-2017",
     "Navidad 2017", "promo", "2017-12-21", "Juanito de Papá Noel y el juego con 30 % OFF.", {}),
    ("Difusion/Facebook/Varios/mcdonalds_v1b.png", "mas-barato-que-un-combo",  # versión del dueño
     "Más barato que un combo", "promo", "2017-11", None, {"fmt": "jpg"}),
    (ORIG / "difusion/pagalo-como-quieras.webp", "pagalo-como-quieras",  # versión del dueño
     "Pagalo como quieras", "promo", "2017-11-28", "Juanito anuncia todos los medios de pago posibles.", {}),
    ("Difusion/Facebook/Varios/goku_v1b.png", "chaala-e-chalaaa",  # versión del dueño
     "¡Chaala e chalaaa!", "promo", "2018-02", None, {"fmt": "jpg"}),
    (ORIG / "difusion/san-patricio.webp", "san-patricio-2018",  # versión del dueño
     "San Patricio", "promo", "2018-03", None, {"fmt": "jpg"}),
    (ORIG / "difusion/san-patricio-olla.webp", "san-patricio-olla",
     "San Patricio: la olla de oro", "promo", None, None, {"fmt": "jpg"}),
    ("Difusion/Promocional/1000_descargas_android.png", "100-mil-descargas",
     "¡Llegamos a las 100 MIL descargas!", "promo", "2018-03-16",
     "Festejo de las cien mil descargas en Google Play.", {}),
    ("Difusion/Promocional/Martes 13/Juanito en el bosque neón.png", "martes-13-2018",  # versión del dueño (antes: fb_martes13_v1.jpg)
     "Martes 13", "promo", "2018", None, {}),
    ("Difusion/Awesome Game Awards/JUANITO_3500x3500.png", "awesome-game-awards",
     "Awesome Game Awards", "promo", "2018-08",
     "Key art preparado para los Awesome Game Awards 2018, donde, según recuerda el estudio, Juanito resultó premiado.", {"max": 2000, "oculto": True}),  # fuera de la galería (pedido del dueño)

    # --- tiendas (cápsulas)
    ("Stores/Steam/News/Grafico_Hereo_3840x1240_v1.jpg", "steam-hero",
     "Gráfico hero de Steam", "promo", None, "Key art panorámico sin logo (3840 × 1240 en el original).", {"max": 2000, "oculto": True}),  # fuera de la galería (pedido del dueño)
    ("Stores/Steam/capsule_main.png", "steam-capsula",
     "Cápsula principal de Steam", "promo", "2017", None, {"oculto": True}),  # va en la tarjeta de Steam de /conseguilo/
    ("Stores/Steam/News/Capsula_Biblioteca_600x900_v1.jpg", "steam-biblioteca",
     "Cápsula de biblioteca de Steam", "promo", None, None, {"oculto": True}),  # fuera de la galería (pedido del dueño)
    # cápsulas de los DLC y el bundle: van en las tarjetas de /conseguilo/
    ("Stores/Animation/capsule_main.png", "dlc-the-animation",
     "DLC: The Animation", "promo", None, None, {"oculto": True}),
    ("Stores/Artbook/capsule_main.png", "dlc-the-art-book",
     "DLC: The Art Book", "promo", None, None, {"oculto": True}),
    ("Stores/Soundtrack/capsule_main.png", "dlc-original-soundtrack",
     "DLC: Original Soundtrack", "promo", None, None, {"oculto": True}),
    ("Stores/Bundle/capsule_main.png", "dlc-the-art-edition",
     "Bundle: The Art Edition", "promo", None, None, {"oculto": True}),
    ("Stores/Soundtrack/Original Art/OST_Cover.png", "ost-portada",
     "Portada del Original Soundtrack", "promo", None, "Gluk y Juanito con guitarra, en estética synthwave.",
     {"oculto": True}),  # ya está en /musica/

    # --- fondos de pantalla (homenajes): primero videojuegos, después películas (pedido del dueño)
    ("Difusion/Wallpapers/Videogames/Donkey Kong/Donkey_Kong_Juanito_v1.jpg", "wallpaper-donkey-kong",
     "Homenaje a Donkey Kong", "fondos", None, None, {"serie": "fondos-videojuegos", "oculto": True}),  # oculto: pedido del dueño
    ("Difusion/Wallpapers/Videogames/Wonder Boy/Wonder_Boy_Juanito_HD.png", "wallpaper-wonder-boy",
     "Homenaje a Wonder Boy", "fondos", None, None, {"serie": "fondos-videojuegos"}),
    ("Difusion/Wallpapers/Videogames/Snow Bros/Snow_Bros_Juanito_v2.jpg", "wallpaper-snow-bros",
     "Homenaje a Snow Bros", "fondos", None, None, {"serie": "fondos-videojuegos"}),
    ("Difusion/Wallpapers/Videogames/Zombies Ate My Neighbors/Zombies_Ate_v1.png", "wallpaper-zombies",
     "Zombies Walked with Juanito", "fondos", None, "Homenaje a Zombies Ate My Neighbors.",
     {"fmt": "jpg", "serie": "fondos-videojuegos"}),
    ("Difusion/Wallpapers/Videogames/Kung Fu Master/Kung_Fu_Master_Juanito_v2.jpg", "wallpaper-kung-fu-master",
     "Homenaje a Kung Fu Master", "fondos", None, None, {"serie": "fondos-videojuegos"}),
    # Babality no es un homenaje a un juego: va al final del bloque de videojuegos
    ("Difusion/Wallpapers/Juanito_Babality_v3.png", "wallpaper-babality",
     "Babality", "fondos", None, None, {"serie": "fondos-videojuegos", "oculto": True}),  # oculto: pedido del dueño
    ("Difusion/Wallpapers/Movies/Juanito_Back_To_The_Future_v1.png", "wallpaper-volver-al-futuro",
     "Homenaje a Volver al Futuro", "fondos", None, None, {"serie": "fondos-peliculas"}),
    ("Difusion/Wallpapers/Movies/Juanito_Jaws_v1.jpg", "wallpaper-tiburon",
     "Homenaje a Tiburón", "fondos", None, None, {"serie": "fondos-peliculas"}),
    ("Difusion/Wallpapers/Movies/ET Scene/Juanito_ET_v1.jpg", "wallpaper-et",
     "Homenaje a E.T.", "fondos", None, None, {"serie": "fondos-peliculas", "oculto": True}),  # oculto: pedido del dueño
    ("Difusion/Wallpapers/Movies/Ghost/Juanito_Ghost_v2.png", "wallpaper-ghost",
     "Homenaje a Ghost", "fondos", None, "Juanito y Gluk en la escena del torno.", {"serie": "fondos-peliculas"}),

    # --- historia
    (_website_2014, "web-coming-soon-2014",
     "La web «Coming soon» de 2014", "historia", "2014-03",
     "Así era juanitogame.com: un gabinete arcade en niebla verde y «Coming soon / Próximamente / Em breve».", {}),
    ("Difusion/Steam Greenlight/17148808_10154550285933990_1022999282_o.png", "greenlight-dia-1",
     "Greenlight: día 1", "historia", "2017-03-07",
     "Estadísticas de Steam Greenlight al primer día: 1.122 visitantes y 601 votos «Sí».", {"crop": GL_CROP}),
    ("Difusion/Steam Greenlight/17237092_10154561518563990_206544066_o.png", "greenlight-dia-4",
     "Greenlight: día 4", "historia", "2017-03-10",
     "A los cuatro días: 1.886 visitantes, 1.000 votos «Sí» (66 %) y 61 % del camino al Top 100.", {"crop": GL_CROP}),
    ("Prensa/Radios/Crack 10-10-2016/14991385_1160426870706832_447388316816859153_o.jpg", "visita-crack-radiolexia",
     "De visita en Crack", "historia", "2016-11",
     "El equipo en el estudio de Radiolexia, durante la entrevista en Crack.", {}),
    ("Difusion/Facebook/Varios/switch_rumor.png", "switch-rumor",
     "El rumor del port a Switch", "historia", "2017-08-17",
     "Titulares en inglés, español, alemán y francés sobre un posible port a Nintendo Switch.", {"fmt": "jpg"}),
    # cuadros del fragmento de TN Tecno 377: solo para la línea de tiempo, no van a la galería
    (_cuadro(TN_TECNO, 20), "tn-tecno-apertura",
     "TN Tecno", "historia", "2017-08-26", "La apertura de TN Tecno 377.", {"oculto": True}),
    (_cuadro(TN_TECNO, 48), "tn-tecno-bloque",
     "TN Tecno: videojuego argento", "historia", "2017-08-26",
     "El bloque sobre Juanito: «Videojuego argento y a puro clásico».", {"oculto": True}),

    # --- arcade
    ("Fotos/CAM00293.jpg", "arcade-primera-foto",
     "Primera foto del gabinete", "arcade", "2015-04-22",
     "La primera foto fechada del arcade de Juanito: «Sobreviviste 13:32».", {}),
    ("Arcade Machine/Bartop/Juanito_HD/Marquee_Juanito_v1.png", "arcade-marquesina",
     "Diseño de la marquesina", "arcade", None, None, {"fmt": "jpg"}),
    ("Arcade Machine/Bartop/Juanito_HD/Izquierda_Juanito_v1.png", "arcade-lateral-izquierdo",
     "Diseño del lateral izquierdo", "arcade", None, None, {"fmt": "jpg"}),
    ("Arcade Machine/Bartop/Juanito_HD/Derecha_Juanito_v1.png", "arcade-lateral-derecho",
     "Diseño del lateral derecho", "arcade", None, None, {"fmt": "jpg"}),
    ("Arcade Machine/Bartop/Juanito_HD/Bezel_LCD_Juanito_v3.png", "arcade-bezel",
     "Diseño del marco de pantalla", "arcade", None, None, {"fmt": "jpg"}),
    ("Arcade Machine/Bartop/Juanito_HD/CPO_Juanito_v1.png", "arcade-panel-de-control",
     "Diseño del panel de control", "arcade", None, None, {"fmt": "jpg"}),
    ("3D/Arcade Texturas/Muestra_II.jpg", "arcade-modelo-3d",
     "Modelo 3D del gabinete", "arcade", None, "Render de prueba del modelo 3D del arcade.", {}),
    ("3D/Arcade Texturas/UV_Lateral_A.png", "arcade-lateral-3d",
     "Arte lateral para el gabinete 3D", "arcade", None, None, {"fmt": "jpg"}),
    ("Fotos/2017/30-MAR - Ranking Arcade/IMG_20170330_175228122.jpg", "arcade-ranking-2017",
     "Ranking del arcade", "arcade", "2017-03-30", "La tabla de récords con las iniciales de los jugadores.", {}),
    ("Fotos/2017/23-JUN - Top Ranking/d3c6e7a4-c0fe-4a82-a17e-034006bd77ed.jpg", "arcade-top-ranking",
     "Récord: 70:49 minutos", "arcade", "2017-06",
     "«Lograste 70:49 min», con 53.210.840 puntos.", {}),
]


def export_galeria() -> None:
    print("galeria")
    clean_dir(OUT / "galeria")
    data = []
    for source, slug, titulo, cat, fecha, desc, opt in GALERIA:
        outrel = f"archivo/galeria/{cat}/{slug}"
        if callable(source):
            img = source()
            out = (ASSETS / outrel).with_suffix(".jpg")
            out.parent.mkdir(parents=True, exist_ok=True)
            fit(img, opt.get("max", 1600)).save(out, "JPEG", quality=88, optimize=True, progressive=True)
            rel = out.relative_to(ASSETS).as_posix()
            print(f"  -> {rel}  {img.size}")
        else:
            rel = export_image(source, outrel, opt.get("max", 1600), crop=opt.get("crop"), fmt=opt.get("fmt"))
        item = {"img": rel, "titulo": titulo, "categoria": cat}
        if fecha:
            item["fecha"] = fecha
        if desc:
            item["descripcion"] = desc
        if opt.get("serie"):
            item["serie"] = opt["serie"]
        if opt.get("oculto"):
            item["oculto"] = True
        data.append(item)
    write_json("galeria.json", data)


# --------------------------------------------------------------- piratería
# 9 capturas de celular (30/01/2020). Se recorta la barra de estado del teléfono.
# Sin links: solo el nombre del sitio.

STATUS_BAR = 40  # px sobre 720×1280

PIRATERIA = [
    ("3c03473e-bd97-4110-8ce0-b54b727d7e96.jpg", "skidrowcodex", "skidrowcodex.co", None,
     "La sinopsis pirata descubrió lo que nunca contamos: que Gluk es «un manipulador alienígena bipolar». "
     "Gluk pidió derecho a réplica, pero se enojó antes de terminar la frase."),
    ("c4c5a8f8-0b04-43c5-a65b-ed317647e1c9.jpg", "skidrowcodex-net", "skidrowcodex.net", None,
     "Crack firmado por DARKSiDERS el 30 de enero de 2020. Para los piratas, Juanito ya era un clásico de culto; "
     "para nosotros, el primer DRM vencido por un nene en pijama."),
    ("6b6b2009-810c-4ed9-8c18-8d7cef60a407.jpg", "skidrowgamereloaded", "skidrowgamereloaded.co", None,
     "«ARCADE MAYHEM JUANITO»: en el mundo pirata el apellido va primero, como en la lista del colegio."),
    ("02969cd4-db80-4d43-9ead-016b493441d9.jpg", "thepiratedownload", "thepiratedownload.net", None,
     "Versión en portugués: «80+ níveis únicos». Cuentas claras: hasta los piratas reconocen que hay mucho para jugar."),
    ("f284af79-c160-4740-8446-2d52f3ee99f4.jpg", "makinongames", "makinongames.com", None,
     "«Más armas y power-ups de los que podés contar con una mano». Es la reseña más honesta que tuvimos, y vino de un pirata."),
    ("73d8d6cd-f9ab-4a11-a73e-3f9358f0aac0.jpg", "warezturkey", "warezturkey.org", "Turquía",
     "Juanito conquista Turquía con «Tek Link indir». No sabemos qué significa, pero suena a power-up."),
    ("7a627bfd-39ef-454e-94a6-1e7e0dccb59f.jpg", "gg-play", "gg-play.ru", "Rusia",
     "Ficha rusa: 1,36 GB y 4 visitas. Cuatro valientes, probablemente la misma persona apretando F5."),
    ("bbb1ceac-4a24-4a5a-81f3-34ea85d28c39.jpg", "jiligame", "jiligame.com", "China",
     "En China lo rebautizaron «La gran aventura arcade de Juanito». Suena a secuela, y nos gusta más que el original."),
    ("bb61d585-adb2-4a69-9af7-c5815251097a.jpg", "igg-games", "igg-games.com", None,
     "«Cracked, Free Download, Torrent»: tres palabras que Juanito no entiende. Él solo quería salvar los arcades."),
]


def export_pirateria() -> None:
    print("pirateria")
    clean_dir(OUT / "pirateria")
    data = []
    for fname, slug, sitio, pais, chiste in PIRATERIA:
        rel = export_image(f"Difusion/Torrents/{fname}", f"archivo/pirateria/{slug}", 1280, fmt="jpg",
                           crop=lambda im: im.crop((0, STATUS_BAR, im.width, im.height)))
        item = {"img": rel, "sitio": sitio}
        if pais:
            item["pais"] = pais
        item["fecha"] = "2020-01-30"
        item["chiste"] = chiste
        data.append(item)
    write_json("pirateria-capturas.json", data)


# ---------------------------------------------------------- home (tarjetas)

def _capa_psd(psd: str, nombre: str):
    """Devuelve una función que compone solo la capa `nombre` (primer nivel) del PSD."""
    def sacar() -> Image.Image:
        from psd_tools import PSDImage
        doc = PSDImage.open(src(psd))
        capa = next(l for l in doc if l.name == nombre)
        return capa.composite().convert("RGB")
    return sacar


def _archivo(rel: str):
    """Una imagen tal cual del material original."""
    return lambda: ImageOps.exif_transpose(Image.open(SRC / rel)).convert("RGB")


def export_home() -> None:
    """Imágenes de las tarjetas «Todo lo que pasó» de la home que no salen de otras secciones,
    y la portada de /el-juego/."""
    print("home")
    clean_dir(OUT / "home")
    piezas = [
        # El juego: key art cuadrado del dueño, sin logo (no está en E:)
        (_archivo(ORIG / "home" / "juego.webp"), "juego"),
        # Historia: gabinete arcade vertical del dueño (no está en E:)
        (_archivo(ORIG / "home" / "historia.webp"), "historia"),
        # Prensa: diario, micrófono y credencial del dueño (no está en E:)
        (_archivo(ORIG / "home" / "prensa.webp"), "prensa"),
        # Videos: claqueta, cámara y auriculares del dueño (no está en E:)
        (_archivo(ORIG / "home" / "videos.webp"), "videos"),
        # Eventos: jugador frente al gabinete en una expo (del dueño, no está en E:)
        (_archivo(ORIG / "home" / "eventos.webp"), "eventos"),
        # Juego de mesa: la caja de Blockits sobre la mesa (del dueño, no está en E:)
        (_archivo(ORIG / "home" / "mesa.webp"), "mesa"),
        # portada de /el-juego/: Juanito y Gluk en el circuito (versión del dueño)
        (_archivo("Difusion/Press Over/Niño y robot en aventura galáctica.png"), "portada-el-juego"),
        # Piratería: calavera pirata del dueño (no está en E:)
        (_archivo(ORIG / "home" / "pirateria.webp"), "pirateria"),
    ]
    for sacar, nombre in piezas:
        img = fit(sacar(), 1600)
        out = OUT / "home" / f"{nombre}.jpg"
        out.parent.mkdir(parents=True, exist_ok=True)
        img.save(out, "JPEG", quality=86, optimize=True, progressive=True)
        print(f"  -> {out.relative_to(ASSETS).as_posix()}  {img.size}")


# -------------------------------------------------------------------- main

GROUPS = {
    "fanart": export_fanart,
    "eventos": export_eventos,
    "galeria": export_galeria,
    "pirateria": export_pirateria,
    "radio": export_radio,
    "home": export_home,
}

if __name__ == "__main__":
    names = sys.argv[1:] or list(GROUPS)
    for n in names:
        if n not in GROUPS:
            sys.exit(f"Grupo desconocido: {n}. Opciones: {', '.join(GROUPS)}")
        GROUPS[n]()
