#!/usr/bin/env python3
"""
Portadas llamativas (estilo YouTube viral) y gancho de texto para el inicio del video.
Todo con Pillow: sin servicios de pago, sin claves.

  hook_overlay(text, W, H, path)           -> PNG transparente con texto enorme (primeros segundos del video)
  make_covers(img_path, text, out_dir, blog) -> cover_h.jpg (1280x720, miniatura de YouTube)
                                               cover_v.jpg (1080x1920, TikTok / Reels / Shorts)
"""
import itertools
import os

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
YELLOW, WHITE, RED, BLACK = (255, 230, 0), (255, 255, 255), (255, 60, 60), (0, 0, 0)


def _split_lines(text, k):
    words = text.split()
    k = max(1, min(k, len(words)))
    best = None
    for cuts in itertools.combinations(range(1, len(words)), k - 1):
        idx = (0,) + cuts + (len(words),)
        lines = [" ".join(words[idx[i]:idx[i + 1]]) for i in range(k)]
        score = max(len(x) for x in lines)
        if best is None or score < best[0]:
            best = (score, lines)
    return best[1]


def _fit(draw, text, box_w, box_h, max_size, max_lines=3, spacing=0.08):
    """Elige el reparto en líneas y el mayor tamaño de letra que cabe en la caja."""
    best = None
    for k in range(1, min(max_lines, max(1, len(text.split()))) + 1):
        lines = _split_lines(text, k)
        size = max_size
        while size > 28:
            f = ImageFont.truetype(FONT_BOLD, size)
            sw = max(2, int(size * 0.11))
            w = max(draw.textlength(x, font=f) for x in lines) + 2 * sw
            h = len(lines) * size * (1 + spacing)
            if w <= box_w and h <= box_h:
                break
            size -= 4
        if best is None or size > best[0]:
            best = (size, lines)
    size, lines = best
    return ImageFont.truetype(FONT_BOLD, size), lines


def _draw_block(img, lines, font, x, y, box_w, align="left", colors=(YELLOW, WHITE, RED), spacing=0.08):
    """Texto grande con contorno negro grueso y sombra. Devuelve la 'y' final."""
    d = ImageDraw.Draw(img)
    size = font.size
    sw = max(2, int(size * 0.11))
    cy = y
    for i, line in enumerate(lines):
        w = d.textlength(line, font=font)
        px = x if align == "left" else x + (box_w - w) / 2
        d.text((px + sw * 0.8, cy + sw * 0.8), line, font=font, fill=(0, 0, 0), stroke_width=sw, stroke_fill=(0, 0, 0))
        d.text((px, cy), line, font=font, fill=colors[i % len(colors)], stroke_width=sw, stroke_fill=BLACK)
        cy += size * (1 + spacing)
    return cy


def _enhance(im):
    """Más color, contraste y nitidez: la foto 'salta' en la miniatura."""
    im = ImageEnhance.Color(im).enhance(1.4)
    im = ImageEnhance.Contrast(im).enhance(1.2)
    im = ImageEnhance.Brightness(im).enhance(1.05)
    return im.filter(ImageFilter.UnsharpMask(radius=2, percent=90, threshold=3))


def _badge(D):
    """Foto del doctor en círculo con aro amarillo."""
    foto = Image.open(os.path.join(ASSETS, "luis.png")).convert("RGBA")
    cara = ImageOps.fit(foto.crop((5, 0, 175, 170)), (D, D), Image.LANCZOS)
    mask = Image.new("L", (D, D), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, D, D], fill=255)
    fondo = Image.new("RGBA", (D, D), (255, 255, 255, 255))
    fondo.alpha_composite(cara)
    av = Image.new("RGBA", (D + 16, D + 16), (0, 0, 0, 0))
    ImageDraw.Draw(av).ellipse([0, 0, D + 15, D + 15], fill=(255, 193, 7, 255))
    av.paste(fondo, (8, 8), mask)
    return av


def _ribbon(img, x, y, label, size):
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT_BOLD, size)
    w = d.textlength(label, font=f) + size
    h = int(size * 1.7)
    d.rounded_rectangle([x, y, x + w, y + h], radius=h // 2, fill=(255, 193, 7))
    d.text((x + size / 2, y + (h - size * 1.15) / 2), label, font=f, fill=(20, 20, 20))
    return w


def hook_overlay(text, W, H, path):
    """Texto-gancho enorme que aparece en los primeros segundos del short."""
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    f, lines = _fit(d, text, W * 0.86, H * 0.20, 170, max_lines=3)
    block_h = len(lines) * f.size * 1.08
    y = H * 0.20
    d.rounded_rectangle([36, y - 34, W - 36, y + block_h + 26], radius=44, fill=(0, 0, 0, 120))
    _draw_block(ov, lines, f, 0, y, W, align="center", colors=(YELLOW, WHITE, YELLOW))
    ov.save(path)


def cover_horizontal(photo, text, path, blog):
    W, H = 1280, 720
    base = ImageOps.fit(_enhance(photo.convert("RGB")), (W, H), Image.LANCZOS, centering=(0.5, 0.38))
    # velo oscuro a la izquierda para que el texto resalte sobre cualquier foto
    mask = Image.new("L", (W, 1))
    for x in range(W):
        a = 235 if x < W * 0.28 else int(max(0, 235 * (1 - (x - W * 0.28) / (W * 0.42))))
        mask.putpixel((x, 0), a)
    base = Image.composite(Image.new("RGB", (W, H), (8, 8, 22)), base, mask.resize((W, H)))
    d = ImageDraw.Draw(base)
    # círculo rojo que señala al protagonista de la foto
    cx, cy, rx, ry = int(W * 0.72), int(H * 0.46), int(W * 0.17), int(H * 0.36)
    for g, col in ((22, (120, 0, 0)), (14, (230, 20, 20))):
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=col, width=g)
    f, lines = _fit(d, text, W * 0.55, H * 0.64, 230, max_lines=3)
    _draw_block(base, lines, f, 42, 46, W * 0.55)
    av = _badge(170)
    base.paste(av, (30, H - av.height - 26), av)
    _ribbon(base, 30 + av.width + 12, H - av.height - 26 + (av.height - 62) // 2, blog, 30)
    base.save(path, "JPEG", quality=90, optimize=True)


def cover_vertical(photo, text, path, blog):
    W, H = 1080, 1920
    base = ImageOps.fit(_enhance(photo.convert("RGB")), (W, H), Image.LANCZOS, centering=(0.5, 0.4))
    # degradado oscuro en el tercio inferior para el texto
    mask = Image.new("L", (1, H))
    for y in range(H):
        t = max(0.0, (y - H * 0.40) / (H * 0.40))
        mask.putpixel((0, y), int(min(1.0, t) * 235))
    base = Image.composite(Image.new("RGB", (W, H), (6, 6, 20)), base, mask.resize((W, H)))
    d = ImageDraw.Draw(base)
    f, lines = _fit(d, text, W * 0.90, H * 0.30, 250, max_lines=3)
    _draw_block(base, lines, f, 0, H * 0.52, W, align="center", colors=(YELLOW, WHITE, RED))
    d.rectangle([0, 0, W, 110], fill=(0, 105, 92))
    ft = ImageFont.truetype(FONT_BOLD, 40)
    t1 = "Dr. Luis Arturo García · Médico Veterinario"
    d.text(((W - d.textlength(t1, font=ft)) / 2, 30), t1, font=ft, fill=WHITE)
    av = _badge(230)
    base.paste(av, (40, H - av.height - 70), av)
    _ribbon(base, 40 + av.width + 16, H - av.height - 70 + (av.height - 84) // 2, blog, 38)
    base.save(path, "JPEG", quality=90, optimize=True)


def make_covers(img_path, text, out_dir, blog):
    """Crea cover_h.jpg y cover_v.jpg a partir de la foto principal. Devuelve las rutas."""
    photo = Image.open(img_path)
    text = " ".join(str(text or "").upper().split())
    h = os.path.join(out_dir, "cover_h.jpg")
    v = os.path.join(out_dir, "cover_v.jpg")
    cover_horizontal(photo, text, h, blog)
    cover_vertical(photo, text, v, blog)
    return h, v
