"""Ролик-шпаргалка «Что в бизнесе можно перестать делать руками» (сценарий R015).

Без речи: заголовок + 8 задач, тумблеры по очереди щёлкают «ручной → авто».
Только PIL + numpy (без cairosvg), поэтому работает и на Windows.

    python r015_card.py            # -> example-r015-card/final.mp4, card.png
"""
import os, pathlib, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, DUR = 1080, 1920, 30, 11.0
K = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(__file__).resolve().parent / "example-r015-card"
GRAPH = (17, 19, 21); OFF = (245, 244, 240); BLUE = (23, 105, 255)
SURF = (27, 30, 33); LINE = (44, 48, 53); MUTED = (154, 158, 164); BLUE_TXT = (120, 170, 255)
SS = 2

X0 = 96                  # левый край контента
X_MAX = 820              # ниже 920 px справа колонка кнопок Reels (x > 830)
TITLE = [("Что в бизнесе", OFF, GRAPH), ("можно перестать", OFF, GRAPH), ("делать руками", BLUE, OFF)]
ROWS = [
    ("Переносить заявки в CRM", "заявки попадают в CRM сами"),
    ("Отвечать клиентам ночью", "бот или AI-агент"),
    ("Напоминать об оплате", "рассылка по сроку счёта"),
    ("Делать счета и акты", "документ по шаблону из CRM"),
    ("Собирать отчёт за неделю", "дашборд обновляется сам"),
    ("Ставить задачи после сделки", "создаются по статусу сделки"),
    ("Искать нужный документ", "поиск по базе документов"),
    ("Отвечать новичкам на вопросы", "база знаний и бот"),
]
ROW_Y0, ROW_H = 884, 94
TG_W, TG_H = 92, 50
TX = X0 + TG_W + 30

# тайминг: клики курсора ускоряются к концу списка
T_TITLE = [0.15, 0.30, 0.45]
T_SUB = 0.75
T_ROW = [1.0 + 0.09 * k for k in range(len(ROWS))]
_GAPS = [0.8, 0.72, 0.64, 0.56, 0.5, 0.45, 0.42]
T_FLIP = [2.4 + sum(_GAPS[:k]) for k in range(len(ROWS))]
T_ZERO = T_FLIP[-1] + 0.45          # счётчик «вручную» загорается нулём
T_PUSH = T_ZERO + 0.3


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, a, d): return clamp((t - a) / d)
def eout(x): x = clamp(x); return 1 - (1 - x) ** 3
def ss(x): x = clamp(x); return x * x * (3 - 2 * x)
def eback(x):
    x = clamp(x); c1 = 1.6; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def lerp(a, b, p): return a + (b - a) * p
def mix(c1, c2, p): return tuple(int(round(lerp(a, b, p))) for a, b in zip(c1, c2))


@functools.lru_cache(None)
def font(weight, size):
    return ImageFont.truetype(str(K / "00_BRAND_GUIDE" / "fonts" / f"Manrope-{weight}.ttf"), size)


def down(im): return im.resize((im.width // SS, im.height // SS), Image.LANCZOS)


@functools.lru_cache(None)
def plate(text, size, fg, bg, padx=30, pady=16, r=18):
    f = font("ExtraBold", size * SS); bb = f.getbbox(text); asc, desc = f.getmetrics()
    th = asc + desc; w = bb[2] - bb[0] + 2 * padx * SS; h = int(th * 0.86) + 2 * pady * SS
    im = Image.new("RGBA", (w, h)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], r * SS, fill=bg + (255,))
    d.text((padx * SS - bb[0], pady * SS - int(th * 0.07)), text, font=f, fill=fg + (255,))
    return down(im)


@functools.lru_cache(None)
def text(s, size, weight, color, maxw=None):
    while True:
        f = font(weight, size * SS); bb = f.getbbox(s)
        if maxw is None or (bb[2]) / SS <= maxw or size <= 20: break
        size -= 1
    asc, desc = f.getmetrics()
    im = Image.new("RGBA", (bb[2] + 4, asc + desc)); ImageDraw.Draw(im).text((0, 0), s, font=f, fill=color + (255,))
    return down(im)


def toggle(p):
    im = Image.new("RGBA", (TG_W * SS, TG_H * SS)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, TG_W * SS - 1, TG_H * SS - 1], TG_H * SS // 2,
                        fill=mix(SURF, BLUE, p) + (255,), outline=mix((90, 95, 102), BLUE, p) + (255,), width=3 * SS)
    kw = TG_H - 14; kx = lerp(7, TG_W - 7 - kw, p)
    d.ellipse([kx * SS, 7 * SS, (kx + kw) * SS, (7 + kw) * SS], fill=mix(MUTED, OFF, p) + (255,))
    return down(im)


@functools.lru_cache(None)
def cursor(press=False):
    """Стрелка-указатель: белая с графитовым контуром и мягкой тенью."""
    s = 0.9 if press else 1.0
    pts = [(0, 0), (0, 44), (11, 34), (19, 52), (27, 48), (19, 31), (34, 31)]
    pts = [(x * 1.25 * s + 10, y * 1.25 * s + 8) for x, y in pts]
    im = Image.new("RGBA", (80 * SS, 90 * SS)); d = ImageDraw.Draw(im)
    d.polygon([(x * SS + 4 * SS, y * SS + 6 * SS) for x, y in pts], fill=(0, 0, 0, 90))
    from PIL import ImageFilter
    im = im.filter(ImageFilter.GaussianBlur(5 * SS)); d = ImageDraw.Draw(im)
    d.polygon([(x * SS, y * SS) for x, y in pts], fill=OFF + (255,), outline=GRAPH + (255,), width=3 * SS)
    return down(im)


@functools.lru_cache(None)
def counter_plate(n, on):
    bg, fg = (BLUE, OFF) if on else (SURF, OFF)
    lab = text("ВРУЧНУЮ", 24, "Bold", OFF if on else MUTED)
    num = text(str(n), 40, "ExtraBold", fg)
    w = 24 + lab.width + 14 + 44 + 16; h = 64
    im = Image.new("RGBA", (w * SS, h * SS)); ImageDraw.Draw(im).rounded_rectangle(
        [0, 0, w * SS - 1, h * SS - 1], 18 * SS, fill=bg + (255,),
        outline=(BLUE if on else LINE) + (255,), width=2 * SS)
    im = down(im)
    im.alpha_composite(lab, (24, (h - lab.height) // 2 + 1))
    return im, 24 + lab.width + 14   # плашка и x, где стоит цифра


def ring(r, a):
    im = Image.new("RGBA", (int(2 * r * SS) + 8, int(2 * r * SS) + 8)); d = ImageDraw.Draw(im)
    d.ellipse([4, 4, 2 * r * SS + 4, 2 * r * SS + 4], outline=BLUE + (int(255 * a),), width=4 * SS)
    return down(im)


@functools.lru_cache(None)
def background():
    im = Image.new("RGB", (W, H), GRAPH); d = ImageDraw.Draw(im)
    grid = mix(GRAPH, LINE, 0.55)
    for x in range(0, W, 72): d.line([(x, 0), (x, H)], fill=grid, width=1)
    for y in range(0, H, 72): d.line([(0, y), (W, y)], fill=grid, width=1)
    # затемнение к краям, чтобы сетка не спорила с текстом
    yy, xx = np.mgrid[0:H, 0:W]
    v = np.clip(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2, 0, 1)[..., None]
    arr = np.array(im, np.float32) * (1 - 0.6 * v) + np.array(GRAPH, np.float32) * 0.6 * v
    return Image.fromarray(arr.astype(np.uint8)).convert("RGBA")


def put(fr, spr, x, y, a=1.0):
    if a <= 0.003: return
    if a < 1:
        spr = spr.copy(); spr.putalpha(spr.getchannel("A").point(lambda v: int(v * a)))
    fr.alpha_composite(spr, (int(round(x)), int(round(y))))


def frame(t, push=True):
    fr = background().copy()
    y = 372
    for k, (s, bg, fg) in enumerate(TITLE):
        p = eout(prog(t, T_TITLE[k], 0.38)); sp = plate(s, 78, fg, bg)
        put(fr, sp, X0, y + 34 * (1 - p), p); y += sp.height + 12
    p = eout(prog(t, T_SUB, 0.35)); sub_y = y + 22 + 16 * (1 - p)
    put(fr, text("8 РУТИННЫХ ЗАДАЧ", 28, "Bold", MUTED), X0, sub_y + 4, p)
    # счётчик «ВРУЧНУЮ N»: убывает с каждым кликом, на нуле загорается синим
    done = sum(1 for tf in T_FLIP if t >= tf + 0.08)
    zero = eback(prog(t, T_ZERO, 0.35))
    cp, nx = counter_plate(len(ROWS) - done, zero > 0)
    cs = 1 + 0.12 * (1 - zero) * (zero > 0)
    if cs != 1: cp = cp.resize((int(cp.width * cs), int(cp.height * cs)), Image.LANCZOS)
    cx = X_MAX + 30 - cp.width; cy = sub_y - 16 - (cp.height - 64) / 2
    put(fr, cp, cx, cy, p)
    roll = eout(prog(t, max([tf + 0.08 for tf in T_FLIP if t >= tf + 0.08], default=-9), 0.25))
    n_new, n_old = len(ROWS) - done, len(ROWS) - done + 1
    ncol = OFF
    put(fr, text(str(n_new), 40, "ExtraBold", ncol), cx + nx * cs, cy + 6 + 18 * (1 - roll), p * roll)
    if done and roll < 1:
        put(fr, text(str(n_old), 40, "ExtraBold", ncol), cx + nx * cs, cy + 6 - 18 * roll, p * (1 - roll))
    for k, (task, fix) in enumerate(ROWS):
        ry = ROW_Y0 + k * ROW_H
        a = eout(prog(t, T_ROW[k], 0.32)); dy = 22 * (1 - a)
        f = eback(prog(t, T_FLIP[k], 0.3))
        # вспышка строки в момент клика
        fl = prog(t, T_FLIP[k], 0.08) * (1 - prog(t, T_FLIP[k] + 0.1, 0.6))
        if fl > 0:
            hl = Image.new("RGBA", (X_MAX - X0 + 28, ROW_H - 6))
            ImageDraw.Draw(hl).rounded_rectangle([0, 0, hl.width - 1, hl.height - 1], 18, fill=BLUE + (255,))
            put(fr, hl, X0 - 14, ry - 10 + dy, 0.22 * fl)
        if k:  # разделитель
            sep = Image.new("RGBA", (X_MAX - X0, 2), LINE + (255,)); put(fr, sep, X0, ry - 12 + dy, a)
        put(fr, toggle(clamp(f, 0, 1)), X0, ry + 10 + dy, a)
        r = prog(t, T_FLIP[k], 0.45)
        if 0 < r < 1:   # кольцо-отклик вокруг тумблера
            rg = ring(30 + 40 * eout(r), 1 - r); put(fr, rg, X0 + TG_W / 2 - rg.width / 2, ry + 10 + TG_H / 2 - rg.height / 2)
        put(fr, text(task, 34, "SemiBold", OFF, X_MAX - TX), TX, ry - 2 + dy, a)
        # «вручную» уходит раньше, чем появляется решение, — без наложения текста
        f_out, f_in = ss(prog(t, T_FLIP[k], 0.14)), eout(prog(t, T_FLIP[k] + 0.12, 0.3))
        put(fr, text("вручную", 27, "Medium", MUTED), TX, ry + 42 + dy - 6 * f_out, a * (1 - f_out))
        put(fr, text(fix, 27, "SemiBold", BLUE_TXT, X_MAX - TX), TX, ry + 42 + dy + 10 * (1 - f_in), a * f_in)
    # курсор: подъезжает к тумблеру, нажимает, едет к следующему
    if push:
        ca = eout(prog(t, T_FLIP[0] - 0.6, 0.3)) * (1 - prog(t, T_FLIP[-1] + 0.35, 0.3))
        if ca > 0:
            tx_ = lambda k: (X0 + TG_W * 0.62, ROW_Y0 + k * ROW_H + 10 + TG_H * 0.55)
            k = max([i for i, tf in enumerate(T_FLIP) if t >= tf - 0.0] + [0])
            nxt = min(k + 1, len(ROWS) - 1)
            p0 = tx_(k); p1 = tx_(nxt)
            if t < T_FLIP[0]:
                st = (X0 + 300, ROW_Y0 + 140); m = ss(prog(t, T_FLIP[0] - 0.6, 0.5)); pos = (lerp(st[0], p0[0], m), lerp(st[1], p0[1], m))
            else:
                end_k = T_FLIP[nxt] if nxt != k else T_FLIP[k] + 1
                m = ss(prog(t, T_FLIP[k] + 0.12, (end_k - T_FLIP[k]) - 0.2))
                pos = (lerp(p0[0], p1[0], m), lerp(p0[1], p1[1], m))
            press = any(tf - 0.05 <= t <= tf + 0.08 for tf in T_FLIP)
            put(fr, cursor(press), pos[0] - 10, pos[1] - 8, ca)
    out = fr.convert("RGB")
    z = 1 + 0.03 * ss(prog(t, T_PUSH, DUR - T_PUSH)) if push else 1.0
    if z > 1.0001:   # медленный наезд, чтобы финальная карточка не стояла статично (RULES §2)
        w2, h2 = W / z, H / z; x0 = (W - w2) / 2; y0 = (H - h2) * 0.45
        out = out.transform((W, H), Image.AFFINE, (1 / z, 0, x0, 0, 1 / z, y0), Image.BICUBIC)
    return np.asarray(out)


def main():
    OUT.mkdir(exist_ok=True)
    card = Image.fromarray(frame(DUR, push=False)); card.save(OUT / "card.png")
    sfx = ([("sfx-pop.mp3", T_TITLE[0], 0.14)] + [("sfx-click.mp3", t, 0.22) for t in T_FLIP]
           + [("sfx-pop.mp3", T_ZERO, 0.2)])
    ins = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-t", str(DUR), "-i", "anullsrc=r=48000:cl=stereo"]
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
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    cover = np.asarray(card.convert("RGB"))   # обложка первым кадром: готовая карточка
    for i in range(int(DUR * FPS)):
        fr = cover if i == 0 else frame(i / FPS)
        p.stdin.write(np.ascontiguousarray(fr, np.uint8).tobytes())
    p.stdin.close(); p.wait(); print("done", OUT / "final.mp4")


if __name__ == "__main__":
    main()
