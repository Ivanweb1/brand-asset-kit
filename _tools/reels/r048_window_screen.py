"""Ролик R048 «Окно» — R044 один в один, заменён только экран: ЖК «Ориентир» с влётом в квартиру.

Вау-хук — сборка экрана с первой секунды → 2 коротких шага → готовый экран и призыв в кадре. Стиль свой:
тёмный фон с зелёным свечением в цвет сайта, белый жирный текст без плашек, экран под небольшим углом.

Исходники — покадровые записи (30 к/с, 2160×1350):
  work/r048/site    — Desktop/realty-window-demo/?demo=1, 8 с (window_record.py): сборка 0–1,8 с,
                      влёт 2,5–7,5 с (рама окна ~3,7 с), дальше гостиная
  work/r044/kit     — сцена набора из R044 без изменений
  work/r044/claude  — сцена Claude из R044 без изменений

    python r048_window_screen.py              # -> example-r048-window-screen/final.mp4, cover.jpg
    python r048_window_screen.py peek 0.5 4   # кадры work/r048/peek_<t>.png
"""
import sys, pathlib, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
K = pathlib.Path(__file__).resolve().parents[2]
WORK = K / "work" / "r048"
WORK44 = K / "work" / "r044"
SRC_DIRS = {"site": WORK / "site", "kit": WORK44 / "kit", "claude": WORK44 / "claude"}
OUT = pathlib.Path(__file__).resolve().parent / "example-r048-window-screen"
FONT = K / "00_BRAND_GUIDE" / "fonts" / "Manrope-ExtraBold.ttf"
BG = (11, 14, 13)
GLOW = (30, 158, 106)                                   # акцент сайта «Ориентир»
SRC_W, SRC_H = 2160, 1350


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eout(x): x = clamp(x); return 1 - (1 - x) ** 3
def ss(x): x = clamp(x); return x * x * (3 - 2 * x)


# ── монтажный лист: (начало в ролике, длительность, исходник, кадр исходника в начале, кроп, ширина экрана, текст)
#    кроп — доля исходника (x0, y0, x1, y1); текст — строки, (начало, конец) внутри сцены
HOOK = ["{C} + мой промпт =", "сайт за 100 000 ₽"]
CTA = ["Напишите «ОКНО» —", "отдам промпт и скилл"]
FULL = (0, 0, 1, 1)
SCENES = [
    # 0–3,2 с: вау-хук — сразу полёт: рама окна ~0,8 с, цифры квартиры, к ~1,5 с гостиная
    dict(t=0.0, d=3.2, src="site", f0=int(3.2 * FPS), crop=FULL, w=990, dx=0, caps=[(HOOK, 0, 9)]),
    # 3,2–4,6 с: карточка набора, клик «Скопировать промпт» на 0,7 с
    dict(t=3.2, d=1.4, src="kit", f0=int(0.3 * FPS), crop=(0.40, 0.0, 1.0, 0.72), w=1000, dx=0,
         caps=[(["Забираете", "промпт и скилл"], 0, 9)]),
    # 4,6–6,2 с: Claude — промпт уже вставлен, отправка на 1,15 с
    dict(t=4.6, d=1.6, src="claude", f0=int(0.45 * FPS), crop=(0.06, 0.08, 0.94, 0.86), w=1000, dx=0,
         caps=[(["Вставляете в {C}"], 0, 9)]),
    # 6,2–10 с: тот же переход целиком: квартал → рама окна (~1,75 с, уже под призывом) → гостиная
    dict(t=6.2, d=3.8, src="site", f0=int(2.0 * FPS), crop=FULL, w=990, dx=0,
         caps=[(["Сайт готов"], 0, 0.9), (CTA, 0.9, 9)]),
]
TOT = SCENES[-1]["t"] + SCENES[-1]["d"]
T_NOTE = 7.6                                            # уведомление об оплате (правило 06.11)
CLICKS = [3.2 + 0.7, 4.6 + 1.15]                         # копирование, отправка
COVER_F = int(7.7 * FPS)                                # обложка (1-й кадр): гостиная с видом на квартал, не пустой старт


# ── геометрия ────────────────────────────────────────────────────────────────
def coeffs(dst, src):
    """Коэффициенты PERSPECTIVE для PIL: точка кадра (dst) -> точка исходника (src)."""
    A, B = [], []
    for (x, y), (u, v) in zip(dst, src):
        A += [[x, y, 1, 0, 0, 0, -u * x, -u * y], [0, 0, 0, x, y, 1, -v * x, -v * y]]
        B += [u, v]
    return np.linalg.solve(np.array(A, float), np.array(B, float)).tolist()


def quad(sc, p):
    """Четырёхугольник экрана в кадре: правый край уходит вглубь, камера медленно наезжает."""
    x0, y0, x1, y1 = sc["crop"]
    aspect = ((y1 - y0) * SRC_H) / ((x1 - x0) * SRC_W)
    z = 1 + 0.045 * ss(p)                               # медленный наезд за сцену
    w = sc["w"] * z; h = w * aspect
    cx = W / 2 + sc["dx"] - 18 * ss(p); cy = 1010 + (1 - z) * 40
    hl, hr = h * 1.05, h * 0.95                          # левый край ближе
    lx, rx = cx - w / 2, cx + w / 2 - w * 0.015
    return [(lx, cy - hl / 2), (rx, cy - hr / 2), (rx, cy + hr / 2), (lx, cy + hl / 2)]


@functools.lru_cache(None)
def rmask(cw, ch, r):
    m = Image.new("L", (cw, ch), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, cw - 1, ch - 1], r, fill=255)
    return m


@functools.lru_cache(None)
def background():
    """Тёмный фон и зелёное свечение за экраном (как цветная подсветка у референса)."""
    im = Image.new("RGB", (W, H), BG)
    g = Image.new("L", (W, H), 0)
    ImageDraw.Draw(g).ellipse([60, 640, 1020, 1540], fill=255)
    g = g.filter(ImageFilter.GaussianBlur(190))
    col = Image.new("RGB", (W, H), GLOW)
    im = Image.composite(col, im, g.point(lambda v: int(v * 0.42)))
    vg = Image.new("L", (W, H), 0)                      # виньетка
    ImageDraw.Draw(vg).ellipse([-300, -200, W + 300, H + 200], fill=255)
    vg = vg.filter(ImageFilter.GaussianBlur(220))
    return Image.composite(im, Image.new("RGB", (W, H), (5, 7, 6)), vg)


@functools.lru_cache(maxsize=64)
def src_frame(name, i):
    d = SRC_DIRS[name]
    n = len(list(d.glob("f*.jpg"))) if name not in _N else _N[name]
    _N[name] = n
    return Image.open(d / f"f{min(i, n - 1):04d}.jpg").convert("RGB")


_N = {}


def screen(fr, sc, p, i):
    src = src_frame(sc["src"], sc["f0"] + i)
    x0, y0, x1, y1 = sc["crop"]
    box = (int(x0 * SRC_W), int(y0 * SRC_H), int(x1 * SRC_W), int(y1 * SRC_H))
    src = src.crop(box); cw, ch = src.size
    q = quad(sc, p)
    c = coeffs(q, [(0, 0), (cw, 0), (cw, ch), (0, ch)])
    # тень под экраном
    sh = Image.new("L", (W, H), 0); ImageDraw.Draw(sh).polygon([(x, y + 26) for x, y in q], fill=200)
    fr.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), sh.filter(ImageFilter.GaussianBlur(34)))
    img = src.transform((W, H), Image.PERSPECTIVE, c, Image.BICUBIC)
    m = rmask(cw, ch, int(cw * 0.022)).transform((W, H), Image.PERSPECTIVE, c, Image.BILINEAR)
    fr.paste(img, (0, 0), m)


# ── текст ────────────────────────────────────────────────────────────────────
@functools.lru_cache(None)
def font(size): return ImageFont.truetype(str(FONT), size)


LOGO = "{C}"                                            # в тексте плашки — значок Claude вместо слова
LOGO_SRC = K / "work" / "r031" / "logo-claude-src.png"  # значок приложения Claude (из R031)


@functools.lru_cache(None)
def logo(px):
    im = Image.open(LOGO_SRC).convert("RGBA").resize((px, px), Image.LANCZOS)
    m = Image.new("L", (px, px), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, px - 1, px - 1], int(px * 0.24), fill=255)
    im.putalpha(m); return im


def parts(s): return [p for p in s.replace(LOGO, "\0" + LOGO + "\0").split("\0") if p]


def line_w(s, f, ic): return sum(ic if p == LOGO else f.getlength(p) for p in parts(s))


@functools.lru_cache(None)
def caption(lines):
    size = 74
    while max(line_w(s, font(size), int(size * 1.08)) for s in lines) > 900: size -= 2
    f = font(size); lh = int(size * 1.3); ic = int(size * 1.08)
    asc = f.getmetrics()[0]
    im = Image.new("RGBA", (W, lh * len(lines) + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k, s in enumerate(lines):
        x = (W - line_w(s, f, ic)) / 2; base = 30 + k * lh + asc
        for p in parts(s):
            if p == LOGO:                               # по центру высоты прописных
                cy = base - size * 0.36
                im.alpha_composite(logo(ic), (int(x), int(cy - ic / 2))); x += ic
            else:
                d.text((x, base), p, font=f, fill=(255, 255, 255, 255), anchor="ls"); x += f.getlength(p)
    shadow = Image.new("RGBA", im.size, (0, 0, 0, 0))
    shadow.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.55)))
    out = Image.alpha_composite(shadow, im)
    return out


def put_caption(fr, lines, a, y=372):
    im = caption(tuple(lines))
    if a < 1:
        im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    fr.paste(im, (0, int(y + (1 - a) * 14)), im)


# ── уведомление об оплате ───────────────────────────────────────────────────
@functools.lru_cache(None)
def note():
    p = WORK44 / "payment.png"
    if not p.exists():
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        import payment_note
        payment_note.make(50000, p)
    im = Image.open(p).convert("RGBA")
    w = 900; im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], 34, fill=255)
    im.putalpha(Image.fromarray(np.minimum(np.asarray(m), np.asarray(im.getchannel("A")))))
    return im


# ── кадр ─────────────────────────────────────────────────────────────────────
def at(i, cover=False):
    t = i / FPS
    sc = next(s for s in reversed(SCENES) if t >= s["t"] - 1e-6)
    j = i - int(round(sc["t"] * FPS)); p = (t - sc["t"]) / sc["d"]
    if cover: sc = dict(sc, f0=COVER_F)
    fr = background().copy()
    screen(fr, sc, p, j)
    for lines, a0, a1 in sc["caps"]:
        lt = t - sc["t"]
        if a0 <= lt < a1:
            a = 1.0 if sc["t"] == 0 else eout((lt - a0) / 0.22)  # хук виден с первого кадра
            put_caption(fr, lines, a)
    if t >= T_NOTE:
        n = note(); k = eout((t - T_NOTE) / 0.35)
        y = int(1370 + (1 - k) * 160)
        im = n.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * k)))
        fr.paste(im, ((W - n.width) // 2, y), im)
    return fr


def main(peek=None):
    OUT.mkdir(exist_ok=True); WORK.mkdir(parents=True, exist_ok=True)
    if peek:
        for s in peek: at(int(round(s * FPS))).save(WORK / f"peek_{s}.png")
        return
    ins = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-t", f"{TOT:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
    sfx = [("sfx-click.mp3", t, 0.25) for t in CLICKS] + [("sfx-pop.mp3", T_NOTE, 0.25)]
    fl, labs = [], []
    for j, (f, t, v) in enumerate(sfx):
        ins += ["-i", str(K / "11_MOTION" / f)]; ms = int(t * 1000)
        fl.append(f"[{j + 2}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={v},adelay={ms}|{ms}[s{j}]")
        labs.append(f"[s{j}]")
    fl.append(f"[1:a]{''.join(labs)}amix=inputs={1 + len(labs)}:normalize=0:duration=first,alimiter=limit=0.95[a]")
    cmd = ["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fl), "-map", "0:v", "-map", "[a]",
           "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-profile:v", "high", "-pix_fmt", "yuv420p",
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(OUT / "final.mp4")]
    at(0, cover=True).save(OUT / "cover.jpg", quality=95)
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(round(TOT * FPS))):
        p.stdin.write(np.asarray(at(i, cover=(i == 0)).convert("RGB"), np.uint8).tobytes())
    p.stdin.close(); p.wait(); print("done", OUT / "final.mp4", f"{TOT:.2f} s")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "peek":
        main([float(x) for x in sys.argv[2:]])
    else:
        main()
