"""Exporta assets desde el material original (solo lectura) a src/assets/.

Uso:  npm run assets            (exporta todo)
      npm run assets -- hero    (solo un grupo)

El material original vive en JUANITO_SRC (por defecto E:\\Game Ever\\TRABAJOS\\Juanito)
y NUNCA se modifica: solo se abren los archivos para leer.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from psd_tools import PSDImage

ROOT = Path(__file__).resolve().parent.parent
SRC = Path(os.environ.get("JUANITO_SRC", r"E:\Game Ever\TRABAJOS\Juanito"))
OUT = ROOT / "src" / "assets"


# ---------------------------------------------------------------- utilidades

def walk(group):
    for layer in group:
        yield layer
        if layer.is_group():
            yield from walk(layer)


def ancestors(layer):
    p = layer.parent
    while p is not None and getattr(p, "kind", "psdimage") != "psdimage":
        yield p
        p = p.parent


def composite_only(psd: PSDImage, keep) -> Image.Image:
    """Compone el PSD dejando visibles solo las capas que cumplen keep(layer)
    (y sus grupos contenedores / descendientes)."""
    selected = {id(l) for l in walk(psd) if keep(l)}
    allowed = set(selected)
    for l in walk(psd):
        if id(l) in selected:
            allowed.update(id(a) for a in ancestors(l))
        elif any(id(a) in selected for a in ancestors(l)):
            allowed.add(id(l))
    img = psd.composite(layer_filter=lambda l: id(l) in allowed and l.is_visible(), force=True)
    return img.convert("RGBA")


def fit_lut(raw: Image.Image, target: Image.Image) -> np.ndarray:
    """LUT por canal (256 valores) que lleva el composite de psd-tools al merge de
    Photoshop. Sirve para 'bakear' ajustes globales (Curvas, Equilibrio de color)
    que psd-tools no aplica."""
    a = np.asarray(raw.convert("RGB")).reshape(-1, 3)
    b = np.asarray(target.convert("RGB")).reshape(-1, 3)
    lut = np.zeros((3, 256), dtype=np.float64)
    for c in range(3):
        sums = np.bincount(a[:, c], weights=b[:, c], minlength=256)
        counts = np.bincount(a[:, c], minlength=256)
        known = counts > 0
        xs = np.nonzero(known)[0]
        ys = sums[known] / counts[known]
        lut[c] = np.interp(np.arange(256), xs, ys)
        lut[c] = np.maximum.accumulate(lut[c])  # monótona
    return np.clip(lut, 0, 255).astype(np.uint8)


def apply_lut(img: Image.Image, lut: np.ndarray) -> Image.Image:
    arr = np.asarray(img.convert("RGBA")).copy()
    for c in range(3):
        arr[..., c] = lut[c][arr[..., c]]
    return Image.fromarray(arr, "RGBA")


MANIFEST: dict[str, dict] = {}


def save(img: Image.Image, rel: str, crop=True, max_w: int | None = None) -> None:
    """Guarda en src/assets/<rel>. Si crop, recorta al contenido visible y anota
    la posición original (x, y, w, h en px del lienzo) en el manifest."""
    out = OUT / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    meta = ""
    x, y = 0, 0
    if crop and img.mode == "RGBA":
        # umbral de alfa: ignora píxeles casi invisibles sueltos que inflan el bbox
        bbox = img.getchannel("A").point(lambda a: 255 if a > 12 else 0).getbbox()
        if bbox:
            meta = f" bbox={bbox}"
            img = img.crop(bbox)
            x, y = bbox[0], bbox[1]
    MANIFEST[rel] = {"x": x, "y": y, "w": img.width, "h": img.height}
    if max_w and img.width > max_w:
        img = img.resize((max_w, round(img.height * max_w / img.width)), Image.LANCZOS)
    img.save(out, optimize=True)
    print(f"  -> {out.relative_to(ROOT)}  {img.size}{meta}")


# ------------------------------------------------------------------- grupos

def export_hero() -> None:
    """Capas del hero de la home desde Mobile Game/Pantallas/BG_Main_v6.psd."""
    path = SRC / "Mobile Game" / "Pantallas" / "BG_Main_v6.psd"
    print(f"hero: {path}")
    psd = PSDImage.open(path)
    W, H = psd.size

    # LUT para bakear Curvas/Equilibrio de color globales.
    hidden = {"HUD", "BTNS", "GUIAS", "FANTAMAS"}
    raw_full = psd.composite(layer_filter=lambda l: l.is_visible() and l.name not in hidden, force=True)
    merged = psd.topil()  # merge guardado por Photoshop (incluye ajustes)
    lut = fit_lut(raw_full, merged)
    save(merged.convert("RGB"), "hero/full.png", crop=False)

    def chain(l):
        return [a.name for a in ancestors(l)][::-1] + [l.name]

    # Planos, de atrás hacia adelante. El BG incluye el relleno sólido,
    # el grupo EDIT/BG/BG (grilla Tron + luces) y la pintura EDIT/BG/BG.
    planes = {
        "hero/bg.png": lambda l: l.name == "Relleno de color 2" or chain(l) == ["EDIT", "BG", "BG"],
        "hero/cables-far.png": lambda l: l.name in ("CABLES AT", "CLONOS AT"),
        "hero/mono.png": lambda l: l.name == "MONO" and l.parent.name == "EDIT",
        "hero/cables-near.png": lambda l: l.name in ("CABLE GRUESO", "CABLES"),
        "hero/gluk.png": lambda l: l.name == "GLUK" and l.parent.name == "EDIT",
        "hero/juanito.png": lambda l: l.name == "JUANITO" and l.parent.name == "EDIT",
        "hero/light-front.png": lambda l: l.name == "LUZ ADELANTE",
    }
    for rel, keep in planes.items():
        img = apply_lut(composite_only(psd, keep), lut)
        save(img, rel, crop=rel != "hero/bg.png")

    # Clonocélulas sueltas, una por archivo (cada una flota con su propio loop).
    clonos = [l for l in walk(psd) if l.parent is not None and getattr(l.parent, "name", "") == "CLONOCELULAS"]
    for l in clonos:
        slug = l.name.lower().replace(" ", "-")
        img = apply_lut(composite_only(psd, lambda x, n=l.name: x.name == n), lut)
        save(img, f"hero/clonos/{slug}.png")

    layers = {k.removeprefix("hero/").removesuffix(".png"): v for k, v in MANIFEST.items() if k.startswith("hero/")}
    (OUT / "hero" / "layers.json").write_text(
        json.dumps({"canvas": {"w": W, "h": H}, "layers": layers}, indent=2), encoding="utf-8"
    )
    print(f"  -> src/assets/hero/layers.json  (lienzo {W}x{H})")


def export_characters() -> None:
    """Juanito y Gluk recortados SIN la sombra del piso (para fondos espaciales).
    Salen del mismo BG_Main_v6.psd; la sombra de piso es la primera capa 'SOMBRA'
    de cada grupo."""
    path = SRC / "Mobile Game" / "Pantallas" / "BG_Main_v6.psd"
    print(f"characters: {path}")
    psd = PSDImage.open(path)
    hidden = {"HUD", "BTNS", "GUIAS", "FANTAMAS"}
    lut = fit_lut(
        psd.composite(layer_filter=lambda l: l.is_visible() and l.name not in hidden, force=True), psd.topil()
    )
    for name in ("JUANITO", "GLUK"):
        group = next(l for l in psd.descendants() if l.is_group() and l.name == name and l.parent.name == "EDIT")
        floor_shadow = group[0]
        assert floor_shadow.name == "SOMBRA", f"{name}: esperaba SOMBRA como primera capa"
        allowed = {id(a) for a in ancestors(group)} | {id(group)}
        allowed |= {id(l) for l in group.descendants() if l is not floor_shadow}
        img = psd.composite(layer_filter=lambda l: id(l) in allowed and l.is_visible(), force=True)
        save(apply_lut(img.convert("RGBA"), lut), f"characters/{name.lower()}.png")
    (OUT / "characters" / "layers.json").write_text(
        json.dumps({k.split("/")[1][:-4]: v for k, v in MANIFEST.items() if k.startswith("characters/")}, indent=2),
        encoding="utf-8",
    )


def export_logo() -> None:
    """Logo vectorial de Scuzzo (variante superior del .ai, compatible PDF) a SVG."""
    import pymupdf

    path = SRC / "Logo" / "Logo Juanito Vector Scuzzo v1.ai"
    print(f"logo: {path}")
    page = pymupdf.open(path)[0]
    mid = page.rect.height / 2
    rect = pymupdf.Rect()
    for d in page.get_drawings():  # el .ai tiene dos variantes apiladas: nos quedamos con la de arriba
        if d["rect"].y1 < mid + 5:
            rect |= d["rect"]
    page.set_cropbox(rect + (-2, -2, 2, 2))
    out = OUT / "logo" / "logo.svg"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page.get_svg_image(text_as_path=True), encoding="utf-8")
    print(f"  -> {out.relative_to(ROOT)}")

    # Logo pintado (el oficial para usos grandes). El vectorial queda para tamaños chicos.
    painted = Image.open(SRC / "Logo" / "Logo_Juanito_Pintura_v1.png").convert("RGBA")
    save(painted, "logo/logo-pintado.png", max_w=2400)

    # Versión blanca del pintado (footer): lo claro queda blanco y el contorno oscuro, transparente,
    # así las letras siguen separadas y el volumen se ve como un gris suave.
    rgba = np.asarray(painted, dtype=np.float32)
    brillo = rgba[..., :3].max(axis=2)
    alfa = rgba[..., 3] * np.clip((brillo - 90) / (190 - 90), 0, 1)
    blanco = np.dstack([np.full(alfa.shape, 255, np.float32)] * 3 + [alfa]).astype(np.uint8)
    save(Image.fromarray(blanco, "RGBA"), "logo/logo-pintado-blanco.png", max_w=2400)

    # Logo de Game Ever (versión blanca, el mismo que usa la web del estudio).
    ge = Image.open(SRC / "Video" / "Cover Logo" / "After" / "(Footage)" / "Final" / "LOGO_GAMEEVER_WHITE_01.png")
    save(ge.convert("RGBA"), "logo/game-ever.png", max_w=900)


# ------------------------------------------------------------ el juego
# Todo lo de la sección "El juego" va a src/assets/juego/. Tamaños: fondos y arte
# grande hasta 1920 px del lado largo (JPG q88), recortes de personajes ~800 px,
# clonocélulas ~400 px e íconos 256 px (PNG con alfa).

JUEGO = OUT / "juego"
Y2017 = SRC / "2017"
MATERIAL = SRC / "Artbook" / "Material"
PLAYABLE = (680, 166, 4520, 2326)  # zona útil 3840x2160 de los PSD de nivel de 5200x2924


def _fit(img: Image.Image, max_side: int | None) -> Image.Image:
    if max_side and max(img.size) > max_side:
        k = max_side / max(img.size)
        img = img.resize((max(1, round(img.width * k)), max(1, round(img.height * k))), Image.LANCZOS)
    return img


def _save_png(img: Image.Image, rel: str, max_side: int | None = 800, crop: bool = True) -> None:
    """PNG con alfa en src/assets/juego/<rel>, recortado al contenido visible."""
    img = img.convert("RGBA")
    if crop:
        bbox = img.getchannel("A").point(lambda a: 255 if a > 12 else 0).getbbox()
        if bbox:
            img = img.crop(bbox)
    img = _fit(img, max_side)
    out = JUEGO / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, optimize=True)
    print(f"  -> {out.relative_to(ROOT)}  {img.size}")


def _save_jpg(img: Image.Image, rel: str, max_side: int | None = 1920, quality: int = 88) -> None:
    img = _fit(img.convert("RGB"), max_side)
    out = JUEGO / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, quality=quality, optimize=True, progressive=True)
    print(f"  -> {out.relative_to(ROOT)}  {img.size}")


def _pixel_layer(psd: PSDImage, name: str) -> Image.Image:
    layer = next(l for l in psd.descendants() if l.name == name and l.kind == "pixel")
    return layer.topil().convert("RGBA")


def _white_to_alpha(img: Image.Image, thresh: int = 150, seeds=()) -> Image.Image:
    """Saca el fondo blanco de una ilustración con contorno: rellena desde el
    borde (y desde `seeds`, para huecos cerrados) los píxeles claros conectados
    y les da alfa según cuán oscuros son (des-premultiplicando del blanco para no
    dejar halo)."""
    from PIL import ImageDraw

    rgb = np.asarray(img.convert("RGB")).astype(np.float64)
    mn = rgb.min(axis=2)
    # .copy(): fromarray comparte un buffer de solo lectura y floodfill no lo modificaría
    light = Image.fromarray(np.where(mn > thresh, 255, 0).astype(np.uint8), "L").copy()
    w, h = light.size
    border = [(x, y) for x in range(0, w, 4) for y in (0, h - 1)] + [(x, y) for y in range(0, h, 4) for x in (0, w - 1)]
    for seed in [*border, *seeds]:
        if light.getpixel(seed) == 255:
            ImageDraw.floodfill(light, seed, 128)
    bg = np.asarray(light) == 128
    alpha = np.ones(mn.shape)
    alpha[bg] = np.clip((255 - mn[bg]) / (255 - thresh), 0, 1)
    alpha[alpha < 0.08] = 0
    a = np.maximum(alpha, 1e-6)[..., None]
    color = np.clip((rgb - (1 - a) * 255) / a, 0, 255)
    out = np.dstack([color, alpha * 255]).round().astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def _split_sheet(img: Image.Image, gap: int = 25) -> list[tuple[int, int, int, int]]:
    """Cajas de las figuras de una hoja de poses transparente (filas y columnas
    separadas por al menos `gap` px de alfa vacío)."""

    def runs(mask, g):
        idx = np.nonzero(mask)[0]
        if len(idx) == 0:
            return []
        out, s, p = [], idx[0], idx[0]
        for i in idx[1:]:
            if i - p > g:
                out.append((s, p + 1))
                s = i
            p = i
        out.append((s, p + 1))
        return out

    a = np.asarray(img.getchannel("A")) > 12
    boxes = []
    for y0, y1 in runs(a.any(axis=1), gap):
        band = a[y0:y1]
        for x0, x1 in runs(band.any(axis=0), gap):
            ys = runs(band[:, x0:x1].any(axis=1), 0)
            boxes.append((int(x0), int(y0 + ys[0][0]), int(x1), int(y0 + ys[-1][1])))
    return boxes


# slug: (chip, fondo). El fondo sale de la capa aplanada que el propio Photoshop
# guardó en cada PSD de nivel ("<MUNDO> copia" o equivalente, exactamente la zona
# útil 680,166 → 4520,2326, sin HUD, marco ni referencias). Así los ajustes de
# Curvas/Tono que psd-tools no sabe aplicar ya vienen bakeados. Excepciones:
#  - donkeykong: los PSD guardan un escenario viejo (2016, oscuro); el fondo final
#    de 2017 (la obra en construcción del mono) solo existe a 960x540.
#  - pong: el PSD no tiene capa aplanada; el PNG HD es el mismo arte a 1920x1080.
MUNDOS = {
    "tetris": ("chip_Tetris.png", ("bg_tetris_v1.psd", "TETRIS copia")),
    "arkanoid": ("chip_Arkanoid.png", ("bg_arkanoid_v1.psd", "ARKANOID copia")),
    "wonderboy": ("chip_WonderBoy.png", ("bg_wonderboy_v1.psd", "WONDERBOY copia")),
    "snowbros": ("chip_SnowBros.png", ("bg_snowbros_v3.psd", "SNOWBROS 2")),  # EXPORTS/SNOWBROS 2 (2017)
    "kungfu": ("chip_KunfuMaster.png", ("bg_kungfumaster_v1.psd", "KUNG_FU_MASTER 3")),
    "donkeykong": ("chip_DonkeyKong.png", "bg_donkeykong2.png"),
    "pacman": ("chip_Pacman.png", ("bg_pacman_v1.psd", "PACMAN copia")),
    "pong": ("chip_Pong.png", "HD/bg_pong_hd.png"),
}


def export_juego_mundos() -> None:
    """Chips (tarjetas) y fondos HD de los 8 mundos, más el chip del jefe final."""
    levels = Y2017 / "Backgrounds" / "Levels"
    print(f"juego-mundos: {levels}")
    for slug, (chip, fondo) in MUNDOS.items():
        img = Image.open(Y2017 / "Worlds" / chip)
        if slug == "wonderboy":  # el PNG está espejado ("HIGH 30000" al revés); el artbook lo usa al derecho
            img = img.transpose(Image.FLIP_LEFT_RIGHT)
        _save_png(img, f"mundos/chip-{slug}.png", max_side=None)
        if isinstance(fondo, tuple):
            psd_name, layer = fondo
            psd = PSDImage.open(levels / psd_name)
            img = _pixel_layer(psd, layer)
            assert img.size == (3840, 2160), f"{psd_name}/{layer}: esperaba la zona útil de 3840x2160"
        else:
            img = Image.open(levels / fondo)
        _save_jpg(img, f"mundos/fondo-{slug}.jpg")
    _save_png(Image.open(Y2017 / "Worlds" / "chip_Boss.png"), "mundos/chip-jefe-final.png", max_side=None)


def export_juego_jefes() -> None:
    """Jefe final (3 fases: recorte transparente + escena completa sin HUD) y los
    jefes de mundo con arte propio: Trevor, Paskus y la esfera de bloques de Tetris."""
    boss_dir = Y2017 / "Boss"
    print(f"juego-jefes: {boss_dir}")
    # Se compone solo el grupo de arte de cada fase con layer.composite() (renderiza
    # únicamente el bbox del grupo: ~15x más rápido que psd.composite con filtro).
    # Las capas de referencia sueltas (BG, 1920*1080x2, JUA REF, HUD, MARCO, BTN REF)
    # quedan afuera solas.
    for n, (group, boss) in enumerate((("BOSS 1", "JEFE"), ("BOSS 2", "BOSS 2"), ("BOSS 3", "BOSS 3")), 1):
        psd = PSDImage.open(boss_dir / f"bg_boss_fase_{n}.psd")
        top = next(l for l in psd if l.name == group and l.is_group())
        scene = Image.new("RGBA", psd.size, (0, 0, 0, 255))
        art = top.composite().convert("RGBA")
        scene.paste(art, (top.left, top.top), art)  # paste admite offsets negativos (el arte se pasa del lienzo)
        # LUT contra el merge guardado por Photoshop (bakea Curvas/Equilibrio de color),
        # medida solo donde el merge muestra el arte: dentro de la zona útil, debajo
        # del HUD y donde el marco CRT es transparente.
        merged = psd.topil()
        marco = next(l for l in psd if l.name == "MARCO").topil().getchannel("A")
        mask = np.zeros((psd.height, psd.width), bool)
        mask[600:1840, 700:4500] = True
        mask &= np.asarray(marco) == 0
        a = np.asarray(scene.convert("RGB"))[mask][None]
        b = np.asarray(merged.convert("RGB"))[mask][None]
        lut = fit_lut(Image.fromarray(a), Image.fromarray(b))
        _save_jpg(apply_lut(scene, lut).crop(PLAYABLE), f"jefes/escena-fase-{n}.jpg")
        jefe = next(l for l in top if l.name == boss and l.is_group())
        _save_png(apply_lut(jefe.composite().convert("RGBA"), lut), f"jefes/final-fase-{n}.png", 1920)

    # Jefes de mundo (arte del artbook, 2017).
    # Trevor está sobre blanco: se recorta por encima de la línea de piso (y=603) y se
    # vacía también el hueco blanco entre el puño y el brazo (290,235).
    trevor = Image.open(MATERIAL / "char_dk_color_01.jpg").crop((0, 0, 837, 603))
    _save_png(_white_to_alpha(trevor, seeds=[(290, 235)]), "jefes/trevor.png")
    _save_png(Image.open(MATERIAL / "char_ark_01.png"), "jefes/paskus.png")
    _save_png(Image.open(MATERIAL / "tetris_boss_idle_0.png"), "jefes/tetris-esfera.png")


GLUK_POSES = ["Neutral", "Feliz", "Pensando", "Enojado", "Buuu", "Lluvia_1", "Lluvia_2"]
# Índices de _split_sheet sobre Characters/Juanito_Completo_Color.png (hoja de 2014).
JUANITO_HOJA = {1: 0, 2: 7, 3: 14, 4: 27, 5: 30}


def export_juego_personajes() -> None:
    """Poses extra: las 7 HD de Gluk, la pose canónica de cada uno (artbook),
    5 poses de la hoja de Juanito 2014 y bocetos de Dubi (el perro)."""
    print("juego-personajes")
    for i, name in enumerate(GLUK_POSES, 1):
        _save_png(Image.open(Y2017 / "Gluk" / "HD" / f"Gluk_{name}.png"), f"gluk/pose-{i}.png")
    _save_png(Image.open(MATERIAL / "concept_glu_01.png"), "gluk/pose-artbook.png")
    _save_png(Image.open(MATERIAL / "concept_jua_01.png"), "juanito/pose-artbook.png")

    sheet = Image.open(SRC / "Characters" / "Juanito_Completo_Color.png").convert("RGBA")
    boxes = _split_sheet(sheet)
    assert len(boxes) == 42, f"la hoja de Juanito cambió: {len(boxes)} figuras"
    for n, i in JUANITO_HOJA.items():
        _save_png(sheet.crop(boxes[i]), f"juanito/pose-2014-{n}.png", 600)

    # Dubi solo existe en bocetos a lápiz: van con su papel (JPG).
    _save_jpg(Image.open(MATERIAL / "dubi_sketch_02.png"), "dubi/boceto-1.jpg", 800)
    _save_jpg(Image.open(MATERIAL / "dubi_sketch_01.png"), "dubi/boceto-2.jpg", 800)


# Hoja "ENEMIGOS" (2017/Bocetos/Clono_Nuevas_v1.png, 2829x1824, transparente): es
# la fuente de la página "Clonocells – The Second Generation" del artbook, con los
# nombres internos en castellano. Cajas en px de la hoja (sin los rótulos).
CLONOS = {
    "grande": (226, 240, 509, 516),
    "mediana": (919, 283, 1146, 495),
    "chica": (1499, 325, 1648, 460),
    "general": (1980, 177, 2263, 516),
    "soldado": (2418, 148, 2701, 516),
    "madre": (85, 714, 679, 1351),
    "tiradora": (834, 990, 1259, 1323),
    "escudo": (1471, 990, 1697, 1202),
    "explosiva": (1917, 933, 2284, 1266),
    "babosa": (2475, 983, 2694, 1394),
}


def export_juego_clonos() -> None:
    """Bestiario: las 10 clonocélulas de segunda generación, recortadas (~400 px)."""
    path = Y2017 / "Bocetos" / "Clono_Nuevas_v1.png"
    print(f"juego-clonos: {path}")
    sheet = Image.open(path).convert("RGBA")
    for slug, box in CLONOS.items():
        _save_png(sheet.crop(box), f"clonos/{slug}.png", 400)


# slug: archivo en 2017/Power Ups/HD (íconos pintados de 2014) o en Artbook/Material.
POWERUPS = {
    "bomba": "power_up_bomb.png",
    "vida": "power_up_energy.png",
    "congelar": "power_up_freeze.png",
    "invulnerabilidad": "power_up_invulnerability.png",
    "escudo": "power_up_shield.png",
    "arma-normal": "power_up_wpNormal.png",
    "arma-doble": "power_up_wpMini.png",
    "arma-laser": "power_up_wpContinued.png",
    "arma-fuego": "power_up_wpFire.png",
    "arma-multiple": "power_up_wpMulti.png",
    "arma-parabolica": "power_up_wpParabolic.png",
}


def export_juego_items() -> None:
    """Íconos de power-ups y armas (256 px) e ítems sueltos."""
    print("juego-items")
    for slug, name in POWERUPS.items():
        path = Y2017 / "Power Ups" / "HD" / name
        if not path.exists():
            path = MATERIAL / name
        _save_png(Image.open(path), f"powerups/{slug}.png", 256)
    # Ítem post-lanzamiento (2018). Las esferas tipo Dragon Ball quedan afuera (IP ajena).
    _save_png(Image.open(Y2017 / "Items" / "trebol.png"), "items/trebol.png", 256)


GROUPS = {
    "hero": export_hero,
    "characters": export_characters,
    "logo": export_logo,
    "juego-mundos": export_juego_mundos,
    "juego-jefes": export_juego_jefes,
    "juego-personajes": export_juego_personajes,
    "juego-clonos": export_juego_clonos,
    "juego-items": export_juego_items,
}


def main(argv: list[str]) -> None:
    if not SRC.exists():
        sys.exit(f"No encuentro el material en {SRC} (variable JUANITO_SRC)")
    for name in argv or GROUPS:
        GROUPS[name]()


if __name__ == "__main__":
    main(sys.argv[1:])
