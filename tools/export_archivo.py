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
                 fmt: str | None = None, quality: int = 85) -> str:
    """Exporta srcrel (relativo a SRC) a src/assets/<outrel sin extensión>.<jpg|png>.
    fmt=None: PNG si tiene transparencia real, JPG si no. Devuelve la ruta relativa
    a src/assets/ (con extensión) para los JSON."""
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
    ("Megawacky Max.jpg", "Megawacky Max", "Huyendo de un Metroid", "2017-07", CONCURSO),
    ("Gaston Boquel.jpg", "Gastón Boquel", "Juanito y Gluk a la carrera", "2017-07", CONCURSO),
    ("Juan Camilo Salamanca 1.jpg", "Juan Camilo Salamanca", "Juanito 3D sobre el arcade", "2017-07", CONCURSO),
    ("Juan Camilo Salamanca 2.jpg", "Juan Camilo Salamanca", "Juanito 3D en el espacio", "2017-07", CONCURSO),
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
    ("Aleksander Youkovibch 1.jpg", "Aleksander «Alek» Youkovibch (6 años)", "Dibujo de Alek 1", "2018-04", None),
    ("Aleksander Youkovibch 2.jpg", "Aleksander «Alek» Youkovibch (6 años)", "Dibujo de Alek 2", "2018-04", None),
]

PIXEL_ART = {"Pablo Sanchez.jpg"}  # se agranda x4 sin suavizar


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
        data.append(item)
    write_json("fanart.json", data)


# ----------------------------------------------------------------- eventos
# Fechas corregidas según el inventario (docs/material/02-difusion-prensa-fotos.md):
# los nombres de carpeta DD-MM a veces están mal; mandan el flyer o el EXIF.

EV = "Difusion/Eventos"


def _f(folder: str, *names: str) -> list[str]:
    return [f"Fotos/{folder}/{n}" for n in names]


EVENTOS = [
    dict(slug="meet-the-game-2014", nombre="Meet The Game", fecha="2014-05-10",
         lugar="Fusion Bar, Florida 328, CABA",
         descripcion="Primera edición de la expo de videojuegos argentinos de Gamedia. Juanito se pudo jugar en tablets y en una notebook con joystick.",
         flyer=f"{EV}/Meet The Game 2014/MTG_v1.jpg",
         fotos=_f("2014/12-05 - Meet The Game 1",
                  "10012429_306532722834621_456629290714981961_n.jpg",
                  "10150652_594892517276814_2602317165178704200_n.jpg",
                  "10255300_628818837205060_8954522881990099111_n.jpg",
                  "10268631_628818677205076_8688942921046479836_n.jpg",
                  "10295668_628818817205062_7844479874289573237_n.jpg",
                  "10313945_732867516764796_514037534471582437_n.jpg",
                  "10363705_306531822834711_8905054621357419814_n.jpg",
                  "HD-bm_1_2014-04-20_2159_C0006.mov_snapshot_00.01_2014.05.11_16.53.34.png")),
    dict(slug="toronjapalooza-2014", nombre="Toronjapalooza", fecha="2014-07-26",
         lugar="Espacio Cultural Chacra de los Remedios, Parque Avellaneda, CABA",
         descripcion="«Evento cultural nerd» con demo de Juanito en tablet y la foto grupal del equipo.",
         flyer=f"{EV}/Toronjapalooza 2014/Afiche_Toronjapalooza.png",
         fotos=_f("2014/06-08 - Toronjapalooza",
                  "10380554_637349923031073_2031308100007212385_o.jpg",
                  "10560454_776754645709416_5152388013681577822_o.jpg",
                  "10570433_733336666711942_1433516386313728670_n.jpg",
                  "10575385_1908042972668014_936659063942071000_o.jpg")),
    dict(slug="eva-2014", nombre="EVA 2014", fecha="2014-11",
         lugar="CABA",
         descripcion="Exposición de Videojuegos Argentina: stand de Game Ever en el Espacio Indie, con tablets, notebook y joystick, tarjetas y banner.",
         fotos=_f("2014/08-11 - EVA",
                  "10252004_10204881543139465_5563615516421514918_n.jpg",
                  "10406670_10204881544899509_2652617373329300688_n.jpg",
                  "10629477_728846130525652_4439548329714532151_o.jpg",
                  "10659084_728845923859006_1641256708013490881_o.jpg",
                  "Yiyo/ge eva 2.jpg", "Yiyo/ge eva 4.jpg", "Yiyo/ge eva 6.jpg", "Yiyo/ge eva 8.jpg")),
    dict(slug="meet-the-game-2", nombre="Meet The Game 2", fecha="2014-11-16",
         lugar="Centro Cultural San Martín, Sarmiento 1551, CABA",
         descripcion="Segunda edición de la expo de Gamedia. Juanito jugable en monitor y un trofeo con forma de cartucho de Famicom.",
         flyer=f"{EV}/Meet The Game 2 2015/MTG_2_v1.png",
         fotos=_f("2014/08-08 - Meet The Game 2",
                  "juanito mtg 2.jpg", "juanito mtg 3.jpg", "juanito mtg 4.jpg", "juanito mtg 6.jpg",
                  "juanito mtg 7.jpg", "juanito mtg 8.jpg", "juanito mtg 9.jpg")),
    dict(slug="feria-del-libro-2015", nombre="Feria Internacional del Libro de Buenos Aires", fecha="2015-04-23",
         lugar="La Rural, Pabellón Azul, stand 225 (Genesis Comic Store)",
         descripcion="Del 23 de abril al 11 de mayo, el gabinete arcade de Juanito estuvo en el stand de la comiquería, rodeado de peluches: «Vení a jugar».",
         flyer=f"{EV}/Feria Libro 2015/Feria_Juanito.png",
         fotos=_f("2015/24-04 - Feria del Libro",
                  "11041732_716213611823091_1367413272972892951_n.jpg",
                  "11160575_716213735156412_3430791138622533342_n.jpg",
                  "11164148_10205201903179798_909209003_n.jpg",
                  "11185728_10205201907179898_2103408271_n.jpg",
                  "Juanito.jpg")),
    dict(slug="tecnopolis-2015", nombre="Tecnópolis 2015: Ar.Cade", fecha="2015-07",
         lugar="Tecnópolis, Villa Martelli",
         descripcion="Juanito formó parte de Ar.Cade, el catálogo jugable de videojuegos argentinos de la sala azul.",
         fotos=_f("2015/20-07 - Tecnopolis", "01.jpg", "03.jpg", "05.jpg", "06.jpg", "08.jpg", "09.jpg", "10.jpg", "13.jpg")),
    dict(slug="meet-the-devs-2015", nombre="Meet The Devs: Extended Edition", fecha="2015-08-15",
         lugar="Centro Cultural General San Martín, CABA",
         descripcion="Evento de Gamedia con el gabinete arcade de Juanito y su standee junto a Donkey.",
         flyer=f"{EV}/Meet The Devs Extended 2015/Meet_Devs_Ext_v1.jpg",
         fotos=_f("2015/16-08 - Meet The Devs Extended Edition",
                  "20150815_161451.jpg", "20150815_161540.jpg", "20150815_162324.jpg", "20150815_162428.jpg",
                  "20150815_175020.jpg", "Gamedia_01.jpg", "Gamedia_02.jpg", "IMG_20150815_183200.jpg")),
    dict(slug="mica-2015", nombre="MICA 2015", fecha="2015-09-06",
         lugar="CABA",
         descripcion="Mercado de Industrias Culturales Argentinas: Juanito en el espacio «Videojuegos Argentinos».",
         fotos=_f("2015/02-09 - MICA",
                  "10446216_2088153121323664_6026390329369197108_o.jpg",
                  "11992220_10207178683412642_1932823513_n.jpg",
                  "DSCN0453.JPG", "DSCN0454.JPG", "DSCN0456.JPG", "DSCN0457.JPG")),
    dict(slug="bit-bang-fest-2", nombre="Bit Bang Fest, edición 2", fecha="2015-09-12",
         descripcion="Festival de videojuegos con conferencias, testeo, juegos de mesa y competencias. Hubo multitud alrededor del arcade de Juanito.",
         fotos=_f("2015/15-09 - Bit Bang Fest Edicion 2",
                  "Yiyo_Flauros_01.jpg",
                  "11222975_827080464058017_181041837833398322_o.jpg",
                  "12009771_827081867391210_2378451958775084744_n.jpg",
                  "12036853_827077554058308_4263086535140773479_n.jpg",
                  "DaVinci_01.jpg", "Jupitron_03.jpg", "Marisol_Estevez_02.jpg", "Marisol_Estevez_05.jpg")),
    dict(slug="animacity-2015", nombre="Animacity 2015", fecha="2015-10-04",
         descripcion="El gabinete estrenó vinilo nuevo, con Juanito, Donkey y la grilla neón.",
         fotos=_f("2015/04-10 - Animacity",
                  "03.jpg", "IMG_20151004_152020.jpg", "IMG_20151004_160807.jpg", "Jupitron_01.jpg",
                  "Marcelo_03.jpg", "Marcelo_06.jpg", "Marcelo_07.jpg", "PlayNoMore_06.jpg")),
    dict(slug="eva-2015", nombre="EVA 2015", fecha="2015", orden="2015-10-31",
         descripcion="Flyer «Mini Arcade» preparado para la Exposición de Videojuegos Argentina 2015.",
         flyer=f"{EV}/Eva 2015/Mini_Arcade_v1.png", fotos=[]),
    dict(slug="muere-monstruo-muere-2015", nombre="Muere Monstruo Muere: Arcade Demons Night", fecha="2015-10-30",
         lugar="Teatro El Mandril, Humberto 1° 2758, San Cristóbal",
         descripcion="Fiesta con bandas (Nave, Jupitron, Shitty) y arcades, con Juanito en pantalla.",
         flyer=f"{EV}/Muere Monstruo Muere 2015/Muere_Monstruo_Muere_v1.png",
         fotos=_f("2015/30-10 - Muere Monstruo Muere",
                  "02.jpg", "05.jpg", "06.jpg", "08.jpg", "10.jpg", "11.jpg",
                  "11012028_846566438776086_4635195684037619547_n.jpg",
                  "12191527_846566355442761_6538782601808470472_n.jpg")),
    dict(slug="meet-the-game-3", nombre="Meet The Game 3: Rise of the Devs", fecha="2015-11-14",
         lugar="Centro Cultural General San Martín, CABA",
         descripcion="Tercera edición de la expo de Gamedia, con el arcade de Juanito junto a otros juegos argentinos.",
         flyer=f"{EV}/Meet The Game 2015/Meet_Devs_Game_2015.png",
         fotos=_f("2015/20-11 - Meet The Game 3",
                  "20151114_162225.jpg", "20151114_162323.jpg", "DSC_1722.JPG", "DSC_1725.JPG",
                  "DSC_1732.JPG", "DSC_1733.JPG", "DSC_1737.JPG", "Gamedia_01.jpg")),
    dict(slug="muere-monstruo-muere-1-ano", nombre="Muere Monstruo Muere: cumple del primer año", fecha="2015-11-27",
         lugar="Teatro El Mandril, San Cristóbal",
         descripcion="«Película + arcades + banda + mucho más». En la puerta se vendían los pósters de Juanito a $25.",
         flyer=f"{EV}/Muere Monstruo Muere 2015 1 Año/Muere_Monstruo_Muere_v1.png",
         fotos=_f("2015/27-11 - Muere Monstruo Muere",
                  "20151128_000410.jpg", "20151128_000449.jpg", "20151128_012907.jpg", "20151128_012926.jpg",
                  "20151128_035053.jpg", "20151128_040709.jpg", "20151128_044309.jpg", "20151128_045928.jpg")),
    dict(slug="checkpoint-2015", nombre="Checkpoint: fiesta de fin de año", fecha="2015-12-12",
         lugar="TecnoBar, Fitz Roy 2021, Palermo",
         descripcion="Fiesta de fin de año «junto a Juanito», con flyer protagonizado por él.",
         flyer=f"{EV}/Checkpoint 2015/Checkpoint_2015_v1.png", fotos=[]),
    dict(slug="geek-out-fest-2", nombre="Geek Out! Fest 2.0", fecha="2016-04-30",
         lugar="Centro Cultural San Martín, CABA",
         descripcion="«Vení a jugar»: el arcade de Juanito en el festival de juegos de mesa y cultura geek.",
         flyer=f"{EV}/Geek Out 2016/Mini_Arcade_v1.png",
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
         fotos=_f("2016/21-05 - Meet The Devs",
                  "604bd320-5100-459a-b989-19dc0dd36dbb.jpg", "20160521_165158.jpg", "20160521_180409.jpg",
                  "20160521_181627.jpg", "75977855-63c6-4b6d-a478-ef140cbfe2c5.jpg")),
    dict(slug="nave-100", nombre="Nave 100", fecha="2016-06-11",
         descripcion="El arcade de Juanito en una noche con bandas en vivo y murales.",
         fotos=_f("2016/15-06 - Nave 100",
                  "20160611_184858.jpg", "20160611_184910.jpg", "20160611_184922.jpg",
                  "20160611_184935.jpg", "20160611_185551.jpg", "20160611_205653.jpg")),
    dict(slug="fichinait-2016", nombre="Fichinait", fecha="2016-08-13",
         lugar="Nicasio Oroño 2480, CABA",
         descripcion="Fiesta gamer de La Comunidad del Sótano con Tumba, Argentron Arcade, The Black Heart, Metadron, Nave y Juanito, entre otros.",
         flyer=f"{EV}/Fichinait 2016/13886244_1448803045136629_7787626712625036484_n.jpg",
         fotos=_f("2016/16-08 - Fichinait", "20160814_015230.jpg", "20160814_025030.jpg")),
    dict(slug="fiesta-pow-1", nombre="Fiesta Pow 1", fecha="2016-11-04",
         descripcion="El arcade de Juanito en una fiesta, con grupos jugando hasta tarde.",
         fotos=_f("2016/04-11 - Fiesta Pow 1",
                  "14753303_1077649192334475_6258867156937548262_o.jpg",
                  "14753319_1077648865667841_4366280068369394587_o.jpg",
                  "14855971_1077645945668133_5972951922032092582_o.jpg",
                  "14876624_1077651729000888_5582720293090154791_o.jpg",
                  "14884688_1077648582334536_6233378757329794728_o.jpg",
                  "14940163_1077653135667414_2408876551470612729_o.jpg",
                  "14940248_1077652825667445_5728427128907845786_o.jpg",
                  "14956460_1077648885667839_605138013893109158_n.jpg")),
    dict(slug="eva-2016", nombre="EVA 2016", fecha="2016-11-05",
         lugar="CABA",
         descripcion="El arcade con la nueva grilla de neón y mucho público en la Exposición de Videojuegos Argentina.",
         fotos=_f("2016/08-11 - EVA",
                  "Juaquin/IMG_20161105_174617588.jpg", "Juaquin/IMG_20161105_175103464_HDR.jpg",
                  "Juaquin/IMG_20161105_175122035.jpg", "Juaquin/IMG_20161105_181523661.jpg",
                  "Marisol/14939522_1233302590064483_7811079525936636613_o.jpg",
                  "Marisol/14963183_1233305360064206_5789180045100913921_n.jpg",
                  "Marisol/14991459_1233301746731234_3550766460333122881_o.jpg",
                  "Marisol/14991479_1233302523397823_6933091448920139606_o.jpg")),
    dict(slug="test-fest-2016", nombre="Juanito Test Fest", fecha="2016-11",
         descripcion="Sesión de testeo abierta del juego. Cada tester se llevaba una tarjeta: «¡Gracias por ser parte del Testing de Juanito!».",
         flyer="Difusion/Facebook/Eventos/Test Fest/juanito_test_fest_banner_v2.jpg",
         fotos=["Difusion/Facebook/Eventos/Test Fest/juanito_test_fest_banner_v1.jpg",
                "Difusion/Facebook/Eventos/Test Fest/JuanitoA4.png"]),
    dict(slug="muere-monstruo-muere-2016", nombre="Muere Monstruo Muere: 2 años de amor", fecha="2016-11-11",
         lugar="Teatro El Mandril, San Cristóbal",
         descripcion="Segundo aniversario de la fiesta, con flyer protagonizado por Juanito: «Película + arcades + feria».",
         flyer=f"{EV}/11-16 - Muere Monstrue Muere/11-16_Muere_Monstruo_Muere_v1.jpg",
         fotos=_f("2016/11-11 - Muere Monstruo Muere",
                  "14976532_10211371156856908_5446097163606181619_o.jpg",
                  "14991224_10211370745886634_9022220797331376223_o.jpg",
                  "15016423_10211371029253718_4932361613404971816_o.jpg",
                  "15025336_10211371028813707_2720834721500661503_o.jpg",
                  "15025629_10211370831208767_7353108571100849392_o.jpg",
                  "15036428_10211370655764381_4354700074293562145_n.jpg",
                  "15037134_10211371027613677_2361396998039120398_n.jpg",
                  "15068417_10211371915115864_2493635484865268387_o.jpg")),
    dict(slug="geek-out-fest-3", nombre="Geek Out! Fest 3.0", fecha="2017-05-06",
         lugar="Centro Cultural San Martín, CABA",
         descripcion="El arcade de Juanito, muy jugado por chicos, y una mesa de juegos argentinos junto a JuegosArgentinos.org.",
         fotos=_f("2017/06-MAY - Geek Out Fest 3.0",
                  "01-16.jpg", "01-17.jpg", "01-6.jpg", "IMG_20170506_170556950.jpg",
                  "IMG_20170506_182206279.jpg", "IMG_20170506_182352374.jpg",
                  "Juegos Argentinos/18319393_1356727984415420_3327864515240167482_o.jpg",
                  "Juegos Argentinos/18358960_1356727387748813_8459114177774647996_o.jpg")),
    dict(slug="fichinait-2", nombre="Fichinait Vol. 2", fecha="2017-05-06",
         descripcion="Segunda fiesta Fichinait: arcades hasta la madrugada y un récord de 50:18 minutos en Juanito.",
         fotos=_f("2017/06-MAY - Fichinait Vol.2",
                  "18339475_1347792951941630_952365903_o.jpg", "18360710_1347792945274964_1973210895_n.jpg",
                  "20170507_003923.jpg", "20170507_012323.jpg", "IMG-20170507-WA0005.jpeg",
                  "IMG-20170507-WA0007.jpeg", "IMG-20170507-WA0012.jpeg", "IMG_20170507_020949074.jpg")),
    dict(slug="triple-fest-2017", nombre="Triple Fest", fecha="2017-08",
         descripcion="Banner compartido de Juanito con Fidel (Dungeon Rescue) y Bildo, otros juegos argentinos.",
         flyer="Difusion/Facebook/Eventos/Triple Fest/juanito_test_fest_banner_v1.jpg", fotos=[]),
    dict(slug="random-tandil-2017", nombre="Random: Convención de Freaks, Volumen II", fecha="2017-08-19",
         lugar="Altos de Unión, Quintana 450, Tandil",
         descripcion="Convención auspiciada por el Municipio de Tandil, con el salón lleno.",
         flyer="Fotos/2017/19-AGO - Random (Tandil)/20451593_1862004497450620_404895491845680858_o.jpg",
         fotos=_f("2017/19-AGO - Random (Tandil)", "20989196_1872293159755087_6741567074557061669_o.jpg")),
    dict(slug="geek-out-fest-4", nombre="Geek Out! Fest 4.0", fecha="2018-04-28",
         lugar="Centro Cultural San Martín, Sarmiento 1551, CABA",
         descripcion="Sede argentina del International Tabletop Day, junto a JuegosArgentinos.org. Juanito invitaba: «¡Vení a jugar!».",
         flyer=f"{EV}/Geek Out! Fest 4.0/GeekOutFest4.jpg",
         fotos=[f"{EV}/Geek Out! Fest 4.0/Geek-Out-Fest-4.jpg"]),
    dict(slug="arcade-evento-2018", nombre="ARCADE Evento", fecha="2018", orden="2018-07",
         fotos=_f("2018/ARCADE Evento",
                  "37400879_10214224947231673_2045354041575211008_n.jpg",
                  "37404763_10214224947391677_9024487606208954368_n.jpg",
                  "37417899_10214224946951666_8625516884218871808_n.jpg",
                  "37550509_10214224960752011_5782732345152897024_n.jpg",
                  "37564181_10214224947151671_1378555975119667200_n.jpg",
                  "37567629_10214224960672009_1728724869215944704_n.jpg")),
    dict(slug="primer-aniversario-2018", nombre="Juanito cumple su primer añito", fecha="2018-08-10",
         lugar="Zapiola 2450, Belgrano, CABA",
         descripcion="Fiesta por el primer aniversario del lanzamiento en Steam.",
         flyer="Difusion/Facebook/Varios/primer_anio_v1.jpg", fotos=[]),
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
        if e.get("flyer"):
            item["flyer"] = export_image(e["flyer"], f"archivo/eventos/{e['slug']}/flyer", 1600, fmt="jpg",
                                         crop=EV_CROP.get(e["flyer"]))
        fotos = []
        for i, f in enumerate(e["fotos"], 1):
            fotos.append(export_image(f, f"archivo/eventos/{e['slug']}/{i:02d}", 1600, fmt="jpg",
                                      crop=EV_CROP.get(f)))
        item["fotos"] = fotos
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


GALERIA = [
    # --- afiches históricos (2012-2014) y pósters
    ("Difusion/Posters/Retro/juanito_poster_vintage_01.jpg", "retro-dubi-juanito-gluk",
     "Dubi · Juanito · Gluk", "afiche", "2012",
     "Póster retro estilo cine clase B, de cuando el proyecto todavía se llamaba «Juanito vs. las Clonocélulas Mutantes del Espacio Exterior».", {}),
    ("Difusion/Posters/Retro/Poster_v2.jpg", "retro-poster-v2",
     "Póster retro", "afiche", None, "Variante vintage del afiche, con Juanito, Gluk y el gorila.", {}),
    ("Difusion/Posters/Logo/logo_cielo_v1.jpg", "logo-en-el-cielo",
     "Logo en el cielo", "afiche", "2012-05-28",
     "El logo original: «Juanito vs. las Clonocélulas Mutantes del Espacio Exterior».", {}),
    ("Difusion/Posters/Clasico/poster_2.jpg", "poster-clasico",
     "Póster clásico", "afiche", "2012-12-04", "Juanito, Gluk y Dubi en la versión clásica del afiche.", {}),
    ("Difusion/Posters/Ascii/sujeto_localizado_v1.jpg", "ascii-codename-juanito",
     "Subject Localized · Codename: Juanito", "afiche", "2012-12-10",
     "Póster ASCII: el informe alienígena que localiza al «sujeto» Juanito.", {}),
    ("Difusion/Posters/Incaa/Poster_Incaa_v1.jpg", "incaa-clonocelulas",
     "Juanito vs. las Clonocélulas Mutantes del Espacio Exterior", "afiche", "2014",
     "Póster preparado para la presentación del proyecto al INCAA.", {}),
    ("Difusion/Posters/Screens/Screens-Landscape-01.jpg", "screens-01",
     "Screens 1", "afiche", None, "Serie «Screens»: capturas del juego con textos de cartel de cine.", {}),
    ("Difusion/Posters/Screens/Screens-Landscape-02.jpg", "screens-02",
     "Screens 2", "afiche", None, None, {}),
    ("Difusion/Posters/Screens/Screens-Landscape-04.jpg", "screens-04",
     "Screens 3", "afiche", None, None, {}),
    ("Difusion/Posters/Screens/Screens-Landscape-05jpg.jpg", "screens-05",
     "Screens 4", "afiche", None, None, {}),
    ("Difusion/Posters/Varios/Poster_v3.2.png", "poster-v3",
     "Póster con cita de prensa", "afiche", None, None, {"max": 2000}),
    ("Difusion/Posters/Varios/juanito_poster_limpio_01.jpg", "poster-limpio",
     "Juanito vs. las Clonocélulas (arte limpio)", "afiche", None, None, {}),
    ("Difusion/Posters/Varios/Poster_Landscape_v1.jpg", "poster-landscape",
     "Póster apaisado", "afiche", None, None, {}),

    # --- merch
    ("Difusion/Merch/Super A3/Poster_Generico_SA.png", "poster-super-a3-generico",
     "Póster Super A3: Clásico", "merch", None, None, {"max": 2000}),
    ("Difusion/Merch/Super A3/Poster_Donkey_SA.png", "poster-super-a3-el-mono",
     "Póster Super A3: El Mono", "merch", None, None, {"max": 2000}),
    ("Difusion/Merch/Super A3/Poster_ET_SA.png", "poster-super-a3-et-dedo",
     "Póster Super A3: E.T. Dedo", "merch", None, None, {"max": 2000}),
    ("Difusion/Merch/Posters_Panfleto_v3.png", "panfleto-posters",
     "¡Adquiera ya! su póster de Juanito", "merch", "2015-11",
     "Panfleto de venta: tres modelos de póster a $25 cada uno, edición limitada, «buscanos en la puerta (o por ahí)».", {"max": 2000}),
    ("Difusion/Merch/Super A3/Poster_Donkey_Sticker.png", "sticker-donkey",
     "Sticker de Donkey", "merch", "2015", None, {}),
    ("Difusion/Merch/Remeras/Remera_Opcion_A.jpg", "remera-a",
     "Remera (opción A)", "merch", None, "Diseño de remera negra con Juanito al frente.", {}),
    ("Difusion/Merch/Remeras/Remera_Opcion_B.jpg", "remera-b",
     "Remera (opción B)", "merch", None, "Diseño de remera negra con el logo.", {}),

    # --- piezas promocionales
    ("Difusion/Promocional/Dia Niño 2014/Dia_Niño_2014_v1.png", "dia-del-nino-2014",
     "Día del Niño", "promo", "2014-08", "«Nunca te olvides de tu Juanito interior».", {}),
    ("Difusion/Promocional/Puro Games/Pure_Games_v1.png", "puro-games",
     "Crossover con Puro Games", "promo", "2014-08", "Juanito con caricaturas de los conductores del programa Puro Games.", {}),
    ("Difusion/Promocional/The Hum/The_Hum_SD.png", "the-hum",
     "Crossover con The Hum", "promo", "2014-08", None, {}),
    ("Difusion/Promocional/Halloween 2014/Halloween_2014_HD.png", "halloween-2014",
     "Halloween 2014", "promo", "2014-10", None, {}),
    ("Difusion/Promocional/Navidad 2014/Navidad_2014_HD.png", "navidad-2014",
     "Navidad 2014", "promo", "2014-12", None, {}),
    ("Difusion/Promocional/Halloween 2015/halo.png", "halloween-2015",
     "Halloween 2015", "promo", "2015-10", None, {}),
    ("Difusion/Promocional/Navidad 2015/Navidad 2015.png", "navidad-2015",
     "Navidad 2015", "promo", "2015-12", "¡Felices fiestas!", {}),
    ("Difusion/Promocional/Twitter/Afiche_Twitter_v1.png", "afiche-twitter",
     "¿Vos ya lo seguís en Twitter?", "promo", None, None, {}),
    ("Difusion/Promocional/Celestineia/Juanito_Celeste.png", "celestineia",
     "Juanito y Celestineia", "promo", None, None, {}),
    ("Difusion/Steam/now_available_01.png", "now-available-steam",
     "Now available on Steam", "promo", "2017-08-03", "Pieza del lanzamiento en Steam.", {}),
    ("Difusion/Promocional/Halloween 2017/fb_halloween_update_v1.jpg", "halloween-2017",
     "Halloween update", "promo", "2017-10-25", None, {}),
    ("Difusion/Steam/juanito_descuento.jpg", "pagalo-como-quieras",
     "Pagalo como quieras", "promo", "2017-11-28", "Juanito anuncia todos los medios de pago posibles.", {}),
    ("Difusion/Promocional/San Patricio/san_patricio_v1.png", "san-patricio-2018",
     "San Patricio", "promo", "2018-03", None, {}),
    ("Difusion/Promocional/1000_descargas_android.png", "100-mil-descargas",
     "¡Llegamos a las 100 MIL descargas!", "promo", "2018-03-16",
     "Festejo de las cien mil descargas en Google Play.", {}),
    ("Difusion/Promocional/Martes 13/fb_martes13_v1.jpg", "martes-13-2018",
     "Martes 13", "promo", "2018", None, {}),
    ("Difusion/Awesome Game Awards/JUANITO_3500x3500.png", "awesome-game-awards",
     "Awesome Game Awards", "promo", "2018-08",
     "Key art preparado para los Awesome Game Awards 2018, donde, según recuerda el estudio, Juanito resultó premiado.", {"max": 2000}),

    # --- tiendas (cápsulas)
    ("Stores/Steam/News/Grafico_Hereo_3840x1240_v1.jpg", "steam-hero",
     "Gráfico hero de Steam", "promo", None, "Key art panorámico sin logo (3840 × 1240 en el original).", {"max": 2000}),
    ("Stores/Steam/capsule_main.png", "steam-capsula",
     "Cápsula principal de Steam", "promo", "2017", None, {}),
    ("Stores/Steam/News/Capsula_Biblioteca_600x900_v1.jpg", "steam-biblioteca",
     "Cápsula de biblioteca de Steam", "promo", None, None, {}),
    ("Stores/Animation/capsule_main.png", "dlc-the-animation",
     "DLC: The Animation", "promo", None, None, {}),
    ("Stores/Artbook/capsule_main.png", "dlc-the-art-book",
     "DLC: The Art Book", "promo", None, None, {}),
    ("Stores/Soundtrack/capsule_main.png", "dlc-original-soundtrack",
     "DLC: Original Soundtrack", "promo", None, None, {}),
    ("Stores/Bundle/capsule_main.png", "dlc-the-art-edition",
     "Bundle: The Art Edition", "promo", None, None, {}),
    ("Stores/Soundtrack/Original Art/OST_Cover.png", "ost-portada",
     "Portada del Original Soundtrack", "promo", None, "Gluk y Juanito con guitarra, en estética synthwave.", {}),

    # --- fondos de pantalla (homenajes)
    ("Difusion/Wallpapers/Movies/Juanito_Back_To_The_Future_v1.png", "wallpaper-volver-al-futuro",
     "Homenaje a Volver al Futuro", "fondos", None, None, {}),
    ("Difusion/Wallpapers/Movies/Juanito_Jaws_v1.jpg", "wallpaper-tiburon",
     "Homenaje a Tiburón", "fondos", None, None, {}),
    ("Difusion/Wallpapers/Movies/ET Scene/Juanito_ET_v1.jpg", "wallpaper-et",
     "Homenaje a E.T.", "fondos", None, None, {}),
    ("Difusion/Wallpapers/Movies/Ghost/Juanito_Ghost_v2.png", "wallpaper-ghost",
     "Homenaje a Ghost", "fondos", None, "Juanito y Gluk en la escena del torno.", {}),
    ("Difusion/Wallpapers/Juanito_Babality_v3.png", "wallpaper-babality",
     "Babality", "fondos", None, None, {}),
    ("Difusion/Wallpapers/Videogames/Donkey Kong/Donkey_Kong_Juanito_v1.jpg", "wallpaper-donkey-kong",
     "Homenaje a Donkey Kong", "fondos", None, None, {}),
    ("Difusion/Wallpapers/Videogames/Kung Fu Master/Kung_Fu_Master_Juanito_v2.jpg", "wallpaper-kung-fu-master",
     "Homenaje a Kung Fu Master", "fondos", None, None, {}),
    ("Difusion/Wallpapers/Videogames/Snow Bros/Snow_Bros_Juanito_v2.jpg", "wallpaper-snow-bros",
     "Homenaje a Snow Bros", "fondos", None, None, {}),
    ("Difusion/Wallpapers/Videogames/Wonder Boy/Wonder_Boy_Juanito_HD.png", "wallpaper-wonder-boy",
     "Homenaje a Wonder Boy", "fondos", None, None, {}),
    ("Difusion/Wallpapers/Videogames/Zombies Ate My Neighbors/Zombies_Ate_v1.png", "wallpaper-zombies",
     "Zombies Walked with Juanito", "fondos", None, "Homenaje a Zombies Ate My Neighbors.", {"fmt": "jpg"}),

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


# -------------------------------------------------------------------- main

GROUPS = {
    "fanart": export_fanart,
    "eventos": export_eventos,
    "galeria": export_galeria,
    "pirateria": export_pirateria,
    "radio": export_radio,
}

if __name__ == "__main__":
    names = sys.argv[1:] or list(GROUPS)
    for n in names:
        if n not in GROUPS:
            sys.exit(f"Grupo desconocido: {n}. Opciones: {', '.join(GROUPS)}")
        GROUPS[n]()
