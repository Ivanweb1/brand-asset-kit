"""Shared renderer for the brand Reels edits: camera, sprites, compositing, encode."""
import io, math, subprocess, functools
import numpy as np, cv2, cairosvg
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
import os, pathlib
K = os.environ.get("BRAND_KIT", str(pathlib.Path(__file__).resolve().parents[2]))   # корень brand-asset-kit
WORK = os.environ.get("REEL_WORK", os.path.abspath("work"))                          # рабочая папка ролика
GRAPH = (17, 19, 21); OFF = (245, 244, 240); BLUE = (23, 105, 255)
SURF = (27, 30, 33); LINE = (44, 48, 53); MUTED = (154, 158, 164)
SRC_W, SRC_H = 1440, 2560
FACE_SRC = (800.0, 1260.0)                  # face centre in the 1440x2560 source
SS = 2                                      # supersampling for sprites


# ---------- easing ----------
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, a, d): return clamp((t - a) / d)
def ss(x): x = clamp(x); return x * x * (3 - 2 * x)
def eout(x): x = clamp(x); return 1 - (1 - x) ** 3
def ein(x): x = clamp(x); return x ** 3
def eback(x):
    x = clamp(x); c1 = 1.4; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def lerp(a, b, p): return a + (b - a) * p


# ---------- fonts / text ----------
@functools.lru_cache(None)
def font(weight, size):
    return ImageFont.truetype(f"{K}/00_BRAND_GUIDE/fonts/Manrope-{weight}.ttf", size)


def _down(img):
    return img.resize((max(1, img.width // SS), max(1, img.height // SS)), Image.LANCZOS)


def plate(text, size=64, weight="Bold", fg=GRAPH, bg=OFF, padx=30, pady=16, r=16):
    f = font(weight, size * SS)
    bb = f.getbbox(text)
    asc, desc = f.getmetrics()
    tw = bb[2] - bb[0]; th = asc + desc
    w = tw + 2 * padx * SS; h = int(th * 0.86) + 2 * pady * SS
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], r * SS, fill=bg + (255,))
    d.text((padx * SS - bb[0], pady * SS - int(th * 0.07)), text, font=f, fill=fg + (255,))
    return np.array(_down(im))


def text_sprite(text, size, weight="Bold", fg=OFF, spacing=1.12, maxw=None):
    f = font(weight, size * SS)
    lines = text.split("\n")
    asc, desc = f.getmetrics(); lh = int(size * SS * spacing)
    w = max(f.getbbox(l)[2] for l in lines) + 8
    h = lh * (len(lines) - 1) + asc + desc
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i, l in enumerate(lines):
        d.text((0, i * lh), l, font=f, fill=fg + (255,))
    return np.array(_down(im))


def rrect(w, h, r, fill, stroke=None, sw=0):
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], r * SS, fill=fill + (255,) if len(fill) == 3 else fill,
                        outline=(stroke + (255,)) if stroke else None, width=sw * SS)
    return np.array(_down(im))


# ---------- brand logo: rasterised straight from the original SVG ----------
@functools.lru_cache(None)
def logo(size, main=OFF, accent=BLUE):
    svg = open(f"{K}/00_BRAND_GUIDE/logo-mark.original.svg").read()
    hexc = lambda c: "#%02X%02X%02X" % c
    svg = svg.replace("#111315", hexc(main)).replace("#1769FF", hexc(accent))
    png = cairosvg.svg2png(bytestring=svg.encode(), output_width=size, output_height=size)
    return np.array(Image.open(io.BytesIO(png)).convert("RGBA"))


@functools.lru_cache(None)
def icon(name, size, variant="on-dark"):
    png = cairosvg.svg2png(url=f"{K}/03_ICONS/SVG/icon-{name}-{variant}.svg", output_width=size, output_height=size)
    return np.array(Image.open(io.BytesIO(png)).convert("RGBA"))


# ---------- compositing ----------
def blit(dst, spr, x, y, alpha=1.0, scale=1.0, anchor="tl"):
    """Alpha-composite RGBA sprite onto RGB float/uint8 frame. Sub-pixel via warpAffine."""
    if alpha <= 0.003 or scale <= 0.01: return
    h, w = spr.shape[:2]
    sw, sh = w * scale, h * scale
    if anchor == "c": x, y = x - sw / 2, y - sh / 2
    x0, y0 = int(math.floor(x)), int(math.floor(y))
    x1, y1 = int(math.ceil(x + sw)) + 1, int(math.ceil(y + sh)) + 1
    cx0, cy0, cx1, cy1 = max(0, x0), max(0, y0), min(dst.shape[1], x1), min(dst.shape[0], y1)
    if cx1 <= cx0 or cy1 <= cy0: return
    M = np.float32([[scale, 0, x - cx0], [0, scale, y - cy0]])
    s = cv2.warpAffine(spr, M, (cx1 - cx0, cy1 - cy0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                       borderValue=(0, 0, 0, 0)).astype(np.float32)
    a = s[..., 3:4] / 255.0 * alpha
    reg = dst[cy0:cy1, cx0:cx1].astype(np.float32)
    dst[cy0:cy1, cx0:cx1] = (reg * (1 - a) + s[..., :3] * a).astype(dst.dtype)


def fill_rect(dst, x0, y0, x1, y1, color, alpha=1.0):
    x0, y0 = max(0, int(round(x0))), max(0, int(round(y0)))
    x1, y1 = min(dst.shape[1], int(round(x1))), min(dst.shape[0], int(round(y1)))
    if x1 <= x0 or y1 <= y0: return
    reg = dst[y0:y1, x0:x1].astype(np.float32)
    dst[y0:y1, x0:x1] = (reg * (1 - alpha) + np.array(color, np.float32) * alpha).astype(dst.dtype)


# ---------- camera ----------
def camera(src, z, fx=540, fy=860, rw=W, rh=H):
    """Render the speaker into an rw x rh region. z=1 means the native 1080-wide framing;
    (fx, fy) is where the face lands. Sub-pixel affine, so slow zooms never jitter."""
    s = 0.75 * z
    x0 = fx - s * FACE_SRC[0]; y0 = fy - s * FACE_SRC[1]
    x0 = min(0, max(rw - s * SRC_W, x0)); y0 = min(0, max(rh - s * SRC_H, y0))
    M = np.float32([[s, 0, x0], [0, s, y0]])
    return cv2.warpAffine(src, M, (rw, rh), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)


# ---------- shared pieces ----------
HOOK = [("Сначала процесс,", OFF, GRAPH), ("потом", OFF, GRAPH), ("технология", BLUE, OFF)]


@functools.lru_cache(None)
def hook_sprites(size=66):
    return [plate(t, size, "Bold", fg=fg, bg=bg) for t, bg, fg in HOOK]


def draw_hook(fr, t, t_in=0.12, t_out=2.55, x=72, y=330, gap=12, size=66):
    sp = hook_sprites(size)
    yy = y
    for k, s in enumerate(sp):
        p = eout(prog(t, t_in + 0.16 * k, 0.38))
        q = ein(prog(t, t_out + 0.05 * k, 0.24))
        a = p * (1 - q)
        blit(fr, s, x, yy + 34 * (1 - p) - 30 * q, alpha=a)
        yy += s.shape[0] + gap


def key_thought(lines="Сначала наводим порядок,\nпотом автоматизируем\nпроцесс", w=936):
    body = text_sprite(lines, 48, "SemiBold", OFF, spacing=1.18)
    cap = text_sprite("ВАЖНО", 26, "Bold", MUTED)
    h = 36 + cap.shape[0] + 16 + body.shape[0] + 40
    bg = rrect(w, h, 26, GRAPH + (235,))
    bg = bg.copy()
    fr = bg[..., :3].copy(); a = bg[..., 3:4].copy()
    canvas = np.concatenate([fr, a], 2)
    # blue accent bar + dot
    cv2.rectangle(canvas, (34, 36), (39, h - 40), BLUE + (255,), -1)
    cv2.circle(canvas, (66, 36 + cap.shape[0] // 2), 7, BLUE + (255,), -1, cv2.LINE_AA)
    rgb = canvas[..., :3].copy()
    blit(rgb, cap, 84, 36); blit(rgb, body, 64, 36 + cap.shape[0] + 16)
    return np.concatenate([rgb, canvas[..., 3:4]], 2)


def toggle_widget(p, label=True):
    """Toggle 'РУЧНОЙ' -> 'АВТО', p in 0..1. Drawn at 2x for clean edges."""
    S = SS; w, h = 640, 250
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * S - 1, h * S - 1], 30 * S, fill=GRAPH + (238,))
    tw, th = 220, 116; tx, ty = 52, 40
    col = tuple(int(lerp(a, b, p)) for a, b in zip(SURF, BLUE))
    d.rounded_rectangle([tx * S, ty * S, (tx + tw) * S, (ty + th) * S], 30 * S, fill=col + (255,),
                        outline=(tuple(int(lerp(a, b, p)) for a, b in zip((90, 95, 102), BLUE)) + (255,)), width=3 * S)
    kw = 84; kx = lerp(tx + 16, tx + tw - 16 - kw, p); ky = ty + (th - kw) / 2
    kc = tuple(int(lerp(a, b, p)) for a, b in zip((154, 158, 164), OFF))
    d.rounded_rectangle([kx * S, ky * S, (kx + kw) * S, (ky + kw) * S], 20 * S, fill=kc + (255,))
    f1 = font("Bold", 30 * S); f2 = font("Bold", 64 * S)
    d.text(((tx + tw + 50) * S, (ty + 8) * S), "РЕЖИМ", font=f1, fill=MUTED + (255,))
    word = "ручной" if p < 0.5 else "авто"
    wc = OFF if p < 0.5 else (120, 170, 255)
    d.text(((tx + tw + 48) * S, (ty + 40) * S), word, font=f2, fill=wc + (255,))
    d.text((tx * S, (ty + th + 26) * S), "Выключаем ручной режим", font=font("SemiBold", 34 * S), fill=OFF + (255,))
    return np.array(_down(im))


def wipe(fr, t, tc, dur=0.5):
    """Brand wipe: blue panel with the original mark sweeps bottom->top, cut happens under it."""
    p = prog(t, tc - dur / 2, dur)
    if p <= 0 or p >= 1: return
    e = ss(p); ph = 2300
    y = H - (H + ph) * e
    fill_rect(fr, 0, y, W, y + ph, BLUE)
    blit(fr, logo(220, OFF, OFF), W / 2, y + ph / 2, anchor="c")
