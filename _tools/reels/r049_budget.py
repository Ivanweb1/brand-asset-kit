"""Ролик R049 «Сайт ЖК за 10 000 ₽ — и за 100 000 ₽» (~10,4 с, без голоса, без автора).

Чат Telegram с клиентом: «Нужен сайт для ЖК, бюджет 10к» → «Держите» → браузер: кринж-экран (дефолтный сайт
по одному запросу, Desktop/cringe-screens/realty) листается → снова чат: «Ой… вообще-то бюджет 100к» → «Тогда так» →
браузер: вау-экран ЖК «Ориентир» с влётом через окно (кадры R048) → чат: «Куда предоплату?» → уведомление об оплате.

Оба экрана — в одной и той же браузерной рамке 16:10, чтобы сравнение было честным.
Исходники:
  work/r049/cringe-full.png — полный скриншот кринж-экрана, ширина 1440 × 1.5 (cringe-screens/tools/fullpage.mjs)
  work/r048/site            — кадры вау-экрана 2160×1350, 30 к/с (window_record.py)
  work/r019/av_anna.jpg     — аватар клиента (как R024)

    python r049_budget.py              # -> example-r049-budget/final.mp4, cover.jpg
    python r049_budget.py peek 1 3 6   # кадры work/r049/peek_<t>.png
"""
import os, sys, pathlib, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r019_harvi as T                    # чат Telegram
from r014_avito import (W, H, FPS, GRAPH, OFF, BLUE, K, clamp, prog, eout, ss, eback, lerp,
                        put, plates, background, xfade)
import r014_avito as R

WORK = pathlib.Path(os.environ.get("R049_WORK", K / "work" / "r049"))
OUT = pathlib.Path(__file__).resolve().parent / "example-r049-budget"
WOW_DIR = K / "work" / "r048" / "site"

# ── чат ──────────────────────────────────────────────────────────────────────
T.NAME = "Анна"
SUB = "в сети"


@functools.lru_cache(None)
def client_avatar(d=128):
    ph = Image.open(K / "work" / "r019" / "av_anna.jpg").convert("RGB")
    s = ph.width * 0.62; ph = ph.crop(((ph.width - s) / 2, ph.height * 0.02, (ph.width + s) / 2, ph.height * 0.02 + s))
    ph = ph.resize((d, d), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", (d * 4, d * 4), 0); ImageDraw.Draw(m).ellipse([0, 0, d * 4 - 1, d * 4 - 1], fill=255)
    ph.putalpha(m.resize((d, d), Image.LANCZOS)); return ph


T.harvi_avatar = client_avatar

# монтажный лист (глобальное время): чат → кринж → чат → вау → чат
S_CR = (1.45, 3.45)                       # кринж-экран
S_WOW = (4.75, 8.35)                      # вау-экран
T_NOTE = 8.95                             # уведомление об оплате
TOT = 10.4
CHAT = [  # (время, кто, текст, время в чате)
    (0.10, "in", "Нужен сайт для ЖК, бюджет 10к", "18:02"),
    (0.80, "out", "Держите", "18:20"),
    (3.60, "in", "Ой… вообще-то бюджет 100к", "18:23"),
    (4.20, "out", "Тогда так", "18:24"),
    (8.50, "in", "Куда предоплату?", "18:31"),
]
HOOK = [("Сайт ЖК за 10 000 ₽ —", OFF, GRAPH), ("и за 100 000 ₽", BLUE, OFF)]
CAPS = [(0.0, S_CR[0] - 0.2, HOOK),
        (S_CR[0], S_CR[1] - 0.15, [("За 10 000 ₽", OFF, GRAPH)]),
        (S_CR[1], S_WOW[0] - 0.15, [("Бюджет 100 000 ₽", OFF, GRAPH)]),
        (S_WOW[0], S_WOW[1] - 0.15, [("За 100 000 ₽", BLUE, OFF)]),
        (T_NOTE, 99, [("Клиент оплатил", BLUE, OFF)])]


@functools.lru_cache(None)
def bubble(k):
    _, who, text, tm = CHAT[k]
    f = T.ui(T.BF, False); tf = T.ui(30, False); out = who == "out"
    lines = T.wrap(text, f, T.TEXT_W)
    tw = max(f.getlength(T.plain(l)) for l in lines)
    tw = max(tw, f.getlength(T.plain(lines[-1])) + (160 if out else 110))
    bw = int(tw + 2 * T.PADX); bh = int(len(lines) * T.LH + 2 * T.PADY + 8)
    im = Image.new("RGBA", (T.SW, bh)); d = ImageDraw.Draw(im)
    x0 = T.SW - 24 - bw if out else 24
    d.rounded_rectangle([x0, 0, x0 + bw, bh], T.RAD, fill=(T.OUTB if out else T.INB) + (255,))
    mut = T.OUTMUTED if out else T.INMUTED; y = T.PADY
    for l in lines:
        T.rich_text(im, d, x0 + T.PADX, y + T.LH / 2, l, f, T.TXT); y += T.LH
    tx = x0 + bw - T.PADX - tf.getlength(tm) - (44 if out else 0)
    d.text((tx, bh - T.PADY - 14), tm, font=tf, fill=mut, anchor="lm")
    if out: T.checks(d, x0 + bw - T.PADX - 36, bh - T.PADY - 12, mut)
    return im


def chat_screen(t):
    im = T.empty_chat(SUB).crop((0, 0, T.SW, T.SHW)).copy(); y = 30
    for k, c in enumerate(CHAT):
        if t < c[0]: break
        b = bubble(k); p = prog(t, c[0], 0.32)
        extra = 12 if k + 1 < len(CHAT) and CHAT[k + 1][1] != c[1] else 0
        if p >= 1: put(im, b, 0, T.MSG_Y0 + y)
        else:
            s = lerp(0.9, 1.0, eback(p)); sp = b.resize((int(b.width * s), max(1, int(b.height * s))), Image.BICUBIC)
            put(im, sp, (T.SW - sp.width) / 2, T.MSG_Y0 + y + (b.height - sp.height) / 2 + 24 * (1 - eout(p)), eout(p * 1.6))
        y += lerp(0, b.height + T.GAP + extra, eout(prog(t, c[0], 0.28)))
    im.alpha_composite(T.top_layer(SUB), (0, 0))
    im.alpha_composite(T.bottom_layer(), (0, T.SHW - T.bottom_layer().height))
    return im


def card(screen):
    c = screen.resize((T.CW, T.CHH), Image.LANCZOS); c.putalpha(T.card_mask())
    ImageDraw.Draw(c).rounded_rectangle([0, 0, T.CW - 1, T.CHH - 1], 44, outline=(255, 255, 255, 40), width=2)
    return c


@functools.lru_cache(None)
def note():
    p = WORK / "payment.png"
    if not p.exists():
        import payment_note
        payment_note.make(50000, p)
    im = Image.open(p).convert("RGBA"); w = 880
    im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    sh = Image.new("RGBA", (w + 80, im.height + 80))
    ImageDraw.Draw(sh).rounded_rectangle([40, 50, 40 + w, 50 + im.height], 40, fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(18)); sh.alpha_composite(im, (40, 40)); return sh


def caps(fr, t):
    for a, b, rows in CAPS:
        if a <= t < b + 0.3:
            o = ss(prog(t, b, 0.25))
            plates(fr, rows, 60, 356, lambda k: clamp(prog(t, a + 0.1 * k, 0.35) - o))


def chat_frame(t, with_caps=True):
    fr = background().copy()
    zoom = 1 + 0.025 * ss(prog(t, S_WOW[1], TOT - S_WOW[1]))       # лёгкий наезд в финале — без статики
    c = card(chat_screen(t))
    if zoom > 1: c = c.resize((int(T.CW * zoom), int(T.CHH * zoom)), Image.LANCZOS)
    put(fr, T.card_shadow(), T.CX0 - 80, T.CY0 - 100)
    put(fr, c, T.CX0 - (c.width - T.CW) / 2, T.CY0 - (c.height - T.CHH) / 2)
    if t >= T_NOTE:
        p = eback(prog(t, T_NOTE, 0.45)); n = note()
        put(fr, n, (W - n.width) / 2, 600 - 200 * (1 - p), clamp(p * 1.5))
    if with_caps: caps(fr, t)
    return fr


# ── браузер: одна рамка для обоих экранов ────────────────────────────────────
BW = 960; BAR = 74; VH = BW * 1350 // 2160; BH = BAR + VH
BX0 = (W - BW) // 2; BY0 = 640


@functools.lru_cache(None)
def browser_bar(url):
    im = Image.new("RGBA", (BW, BAR), (236, 236, 239, 255)); d = ImageDraw.Draw(im)
    for k, col in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        d.ellipse([26 + k * 30, BAR / 2 - 9, 44 + k * 30, BAR / 2 + 9], fill=col)
    d.rounded_rectangle([150, 14, BW - 150, BAR - 14], 23, fill=(255, 255, 255, 255))
    d.text((BW / 2, BAR / 2), url, font=T.ui(26, False), fill=(40, 40, 45), anchor="mm")
    d.line([(0, BAR - 1), (BW, BAR)], fill=(210, 210, 215), width=2)
    return im


@functools.lru_cache(None)
def bshadow():
    im = Image.new("RGBA", (BW + 160, BH + 160))
    ImageDraw.Draw(im).rounded_rectangle([80, 100, 80 + BW, 100 + BH], 40, fill=(0, 0, 0, 170))
    return im.filter(ImageFilter.GaussianBlur(30))


@functools.lru_cache(None)
def cringe_page():
    im = Image.open(WORK / "cringe-full.png").convert("RGB")
    return im.resize((BW, int(im.height * BW / im.width)), Image.LANCZOS)


@functools.lru_cache(maxsize=8)
def wow_src(i):
    n = len(list(WOW_DIR.glob("f*.jpg")))
    return Image.open(WOW_DIR / f"f{min(i, n - 1):04d}.jpg").convert("RGB").resize((BW, VH), Image.LANCZOS)


def browser_frame(view, url, t, d):
    fr = background().copy()
    c = Image.new("RGBA", (BW, BH), (255, 255, 255, 255))
    c.paste(view, (0, BAR)); c.alpha_composite(browser_bar(url)); c.putalpha(T.rr_mask(BW, BH, 36))
    ImageDraw.Draw(c).rounded_rectangle([0, 0, BW - 1, BH - 1], 36, outline=(255, 255, 255, 40), width=2)
    wp = eout(prog(t, 0, 0.35)); sc = lerp(0.94, 1.0, wp) * (1 + 0.03 * ss(prog(t, 0, d)))   # появление + медленный наезд
    cs = c.resize((int(BW * sc), int(BH * sc)), Image.LANCZOS)
    x, y = (W - cs.width) / 2, BY0 + (BH - cs.height) / 2 + 40 * (1 - wp)
    put(fr, bshadow(), BX0 - 80, y - 100, wp); put(fr, cs, x, y, clamp(wp * 1.3))
    return fr


def cringe_frame(t):
    d = S_CR[1] - S_CR[0]; pg = cringe_page()
    off = int(ss(prog(t, 0.35, d - 0.5)) * 1500)                  # листаем до карточек квартир
    return browser_frame(pg.crop((0, off, BW, off + VH)), "zhk-site.ru", t, d)


def wow_frame(t):
    d = S_WOW[1] - S_WOW[0]
    return browser_frame(wow_src(int((2.4 + t) * FPS)), "orientir-zhk.ru", t, d)


# ── сборка ───────────────────────────────────────────────────────────────────
def scene(t):
    if t < S_CR[0]: return chat_frame(t)
    if t < S_CR[1]:
        fr = cringe_frame(t - S_CR[0]); caps(fr, t); return fr
    if t < S_WOW[0]: return chat_frame(t)
    if t < S_WOW[1]:
        fr = wow_frame(t - S_WOW[0]); caps(fr, t); return fr
    return chat_frame(t)


def at(i):
    t = i / FPS; XF = R.XF
    fr = scene(t).convert("RGB")
    for b in (S_CR[0], S_CR[1], S_WOW[0], S_WOW[1]):
        if b - XF < t < b: fr = xfade(fr, scene(b).convert("RGB"), (t - (b - XF)) / XF)
    return fr


def make_cover():
    """Обложка: кринж сверху, вау снизу, хук и суммы — внутри центрального квадрата (y 420…1500)."""
    fr = background().copy().convert("RGBA")
    h = 360
    top = cringe_page().crop((0, 0, BW, h))
    bot = wow_src(int(7.6 * FPS)).crop((0, (VH - h) // 2, BW, (VH - h) // 2 + h))
    for img, y in ((top, 700), (bot, 1095)):
        c = img.convert("RGBA"); c.putalpha(T.rr_mask(BW, h, 32))
        put(fr, bshadow().resize((BW + 160, h + 160)), BX0 - 80, y - 90); put(fr, c, BX0, y)
    plates(fr, HOOK, 64, 440, lambda k: 1.0)
    plates(fr, [("10 000 ₽", OFF, GRAPH)], 54, 990, lambda k: 1.0)
    plates(fr, [("100 000 ₽", BLUE, OFF)], 54, 1385, lambda k: 1.0)
    fr.convert("RGB").save(OUT / "cover.jpg", quality=95)


def main(peek=None):
    OUT.mkdir(exist_ok=True); WORK.mkdir(exist_ok=True)
    if peek:
        for s in peek: at(int(s * FPS)).save(WORK / f"peek_{s}.png")
        return
    sfx = [("sfx-pop.mp3", c[0], 0.2) for c in CHAT]
    sfx += [("sfx-pop.mp3", S_CR[0] + 0.05, 0.14), ("sfx-pop.mp3", S_WOW[0] + 0.05, 0.16), ("sfx-click.mp3", T_NOTE, 0.3)]
    ins = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-t", f"{TOT:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
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
    make_cover()
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(round(TOT * FPS))):
        fr = Image.open(OUT / "cover.jpg").convert("RGB") if i == 0 else at(i)
        p.stdin.write(np.ascontiguousarray(np.asarray(fr.convert("RGB")), np.uint8).tobytes())
    p.stdin.close(); p.wait(); print("done", OUT / "final.mp4", f"{TOT:.2f} s")


if __name__ == "__main__":
    if sys.argv[1:2] == ["peek"]:
        main([float(s) for s in sys.argv[2:]])
    else:
        main()
