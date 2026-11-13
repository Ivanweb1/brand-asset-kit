"""R048 «Окно» в мокапе: те же сцены, тайминг, надписи и звуки, что в r048_window_screen.py,
но экран не парит на тёмном фоне, а стоит в ноутбуке на столе в кофейне.

Мокап — work/r048/cafe-mockup.png (9:16, экран залит хромакеем #00FF00): углы экрана ищутся по зелёному,
запись каждой сцены ложится в экран с перспективой. Стена сверху светлая — надписи тёмные, без тени;
уведомление об оплате — на столе под ноутбуком, чтобы не закрывать экран.

    python r048_cafe.py              # -> example-r048-window-cafe/final.mp4, cover.jpg
    python r048_cafe.py peek 0.5 7   # кадры work/r048/cafe_peek_<t>.png
"""
import functools, pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import r048_window_screen as base

W, H, FPS = base.W, base.H, base.FPS
MOCKUP = base.WORK / "cafe-mockup.png"
OUT = pathlib.Path(__file__).resolve().parent / "example-r048-window-cafe"
INK = (27, 31, 28, 255)
CAP_Y = 300
NOTE_Y = 1600


@functools.lru_cache(None)
def mockup():
    im = Image.open(MOCKUP).convert("RGB")
    k = W / im.width
    big = im.resize((W, round(im.height * k)), Image.LANCZOS)
    if big.height != H:                                  # подгон по высоте к 1920 с обрезкой по центру
        big = big.resize((round(big.width * H / big.height), H), Image.LANCZOS)
        x = (big.width - W) // 2; big = big.crop((x, 0, x + W, H))
    return big


@functools.lru_cache(None)
def screen_quad():
    a = np.asarray(mockup()).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    ys, xs = np.nonzero((g > 150) & (g - r > 80) & (g - b > 80))
    s, d = xs + ys, xs - ys
    q = [(xs[s.argmin()], ys[s.argmin()]), (xs[d.argmax()], ys[d.argmax()]),
         (xs[s.argmax()], ys[s.argmax()]), (xs[d.argmin()], ys[d.argmin()])]
    cx, cy = np.mean([p[0] for p in q]), np.mean([p[1] for p in q])
    grow = 3                                             # на 3 px наружу — под бортик, чтобы не было зелёной каймы
    return [(float(x + np.sign(x - cx) * grow), float(y + np.sign(y - cy) * grow)) for x, y in q]


@functools.lru_cache(None)
def glare():
    """Еле заметный блик по экрану — чтобы запись не выглядела наклейкой."""
    g = Image.new("L", (W, H), 0)
    q = screen_quad(); x0 = min(p[0] for p in q); y0 = min(p[1] for p in q); x1 = max(p[0] for p in q)
    ImageDraw.Draw(g).polygon([(x0 + (x1 - x0) * 0.55, y0), (x1, y0), (x1, y0 + 260), (x0 + (x1 - x0) * 0.30, y0 + 520)], fill=255)
    return g.filter(ImageFilter.GaussianBlur(90)).point(lambda v: int(v * 0.07))


def put_screen(fr, sc, i):
    src = base.src_frame(sc["src"], sc["f0"] + i)
    cw, ch = src.size
    q = screen_quad()
    c = base.coeffs(q, [(0, 0), (cw, 0), (cw, ch), (0, ch)])
    img = src.transform((W, H), Image.PERSPECTIVE, c, Image.BICUBIC)
    m = Image.new("L", (cw, ch), 255).transform((W, H), Image.PERSPECTIVE, c, Image.BILINEAR)
    fr.paste(img, (0, 0), m)
    fr.paste(Image.new("RGB", (W, H), (255, 255, 255)), (0, 0), Image.fromarray(np.minimum(np.asarray(glare()), np.asarray(m))))


@functools.lru_cache(None)
def caption(lines):
    size = 74
    while max(base.line_w(s, base.font(size), int(size * 1.08)) for s in lines) > 900: size -= 2
    f = base.font(size); lh = int(size * 1.3); ic = int(size * 1.08); asc = f.getmetrics()[0]
    im = Image.new("RGBA", (W, lh * len(lines) + 60), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k, s in enumerate(lines):
        x = (W - base.line_w(s, f, ic)) / 2; bl = 30 + k * lh + asc
        for p in base.parts(s):
            if p == base.LOGO:
                im.alpha_composite(base.logo(ic), (int(x), int(bl - size * 0.36 - ic / 2))); x += ic
            else:
                d.text((x, bl), p, font=f, fill=INK, anchor="ls"); x += f.getlength(p)
    return im


def camera(fr, p):
    """Медленный наезд на экран за сцену, как наезд в R044."""
    z = 1 + 0.05 * base.ss(p)
    q = screen_quad(); cx = sum(x for x, _ in q) / 4; cy = sum(y for _, y in q) / 4
    w, h = W / z, H / z
    x0 = min(max(cx - w / 2 - (cx - W / 2) / z, 0), W - w); y0 = min(max(cy - h / 2 - (cy - H / 2) / z, 0), H - h)
    return fr.crop((x0, y0, x0 + w, y0 + h)).resize((W, H), Image.BICUBIC)


def at(i, cover=False):
    t = i / FPS
    sc = next(s for s in reversed(base.SCENES) if t >= s["t"] - 1e-6)
    j = i - int(round(sc["t"] * FPS)); p = (t - sc["t"]) / sc["d"]
    if cover: sc = dict(sc, f0=base.COVER_F)
    fr = mockup().copy()
    put_screen(fr, sc, j)
    fr = camera(fr, p)
    for lines, a0, a1 in sc["caps"]:
        lt = t - sc["t"]
        if a0 <= lt < a1:
            a = 1.0 if sc["t"] == 0 else base.eout((lt - a0) / 0.22)
            im = caption(tuple(lines))
            if a < 1: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
            fr.paste(im, (0, int(CAP_Y + (1 - a) * 14)), im)
    if t >= base.T_NOTE:
        n = base.note(); k = base.eout((t - base.T_NOTE) / 0.35)
        im = n.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * k)))
        fr.paste(im, ((W - n.width) // 2, int(NOTE_Y + (1 - k) * 160)), im)
    return fr


if __name__ == "__main__":
    import sys
    base.at = at; base.OUT = OUT
    if len(sys.argv) > 1 and sys.argv[1] == "peek":
        for s in sys.argv[2:]: at(int(round(float(s) * FPS))).save(base.WORK / f"cafe_peek_{s}.png")
    else:
        base.main()
