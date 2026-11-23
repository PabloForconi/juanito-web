"""Arma la imagen para compartir el sitio (Open Graph / redes): public/og.jpg, 1200x630.

Usa la key art y el logo pintado ya exportados en src/assets (correr después de
`npm run assets` si cambian). Uso:
    tools/.venv/Scripts/python.exe tools/make_og.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / 'src' / 'assets'
OUT = ROOT / 'public' / 'og.jpg'
W, H = 1200, 630

art = Image.open(ASSETS / 'hero' / 'full.png').convert('RGB')
# recorte a 1200x630 (1,905:1) desde la key art 16:9, centrado en vertical
ch = round(art.width * H / W)
top = (art.height - ch) // 2
img = art.crop((0, top, art.width, top + ch)).resize((W, H), Image.LANCZOS).convert('RGBA')

# sombra suave abajo a la derecha para que el logo se lea sobre el piso
shade = Image.new('L', (W, H), 0)
ImageDraw.Draw(shade).ellipse((560, 330, 1320, 760), fill=170)
shade = shade.filter(ImageFilter.GaussianBlur(70))
dark = Image.new('RGBA', (W, H), (3, 10, 14, 255))
img = Image.composite(dark, img, shade)

logo = Image.open(ASSETS / 'logo' / 'logo-pintado.png').convert('RGBA')
lw = 540
logo = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
img.alpha_composite(logo, (W - lw - 40, H - logo.height - 48))

OUT.parent.mkdir(exist_ok=True)
img.convert('RGB').save(OUT, quality=86, optimize=True, progressive=True)
print('ok', OUT, img.size)
