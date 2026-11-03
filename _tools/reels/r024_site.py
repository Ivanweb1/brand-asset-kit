"""Ролик «Клиенту нужен сайт» (сценарий R024), 7,6 с, без голоса.

Чат Telegram с клиентом: «нужен сайт» → «скиньте брендбук и логотип» → два файла →
экран Claude (как R017/R018): промпт печатается размытым, прикрепляются файлы, отправка →
браузер: листается готовый сайт 36kopeek.ru → плашка-призыв «САЙТ».

Части берутся из готовых роликов: чат — r019_harvi (скриншот Telegram work/r019/tg-chat.png),
экран Claude — r017_presentation + вложения-файлы из r018_kp (work/r018/claude-app.png).
Сайт — скриншот всей страницы 36kopeek.ru на 1440 px: work/r024/site-full.png.

    python r024_site.py              # -> example-r024-site/final.mp4, cover.jpg
    python r024_site.py peek 1 3 6   # кадры work/r024/peek_<t>.png
"""
import os, sys, pathlib, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r019_harvi as T                    # чат Telegram
import r018_kp as P                       # вложения-файлы для Claude
import r017_presentation as Q             # экран Claude
from r014_avito import (W, H, FPS, GRAPH, OFF, BLUE, K, clamp, prog, eout, ss, eback, lerp,
                        put, plates, background, xfade)
import r014_avito as R

WORK = pathlib.Path(os.environ.get("R024_WORK", K / "work" / "r024"))
OUT = pathlib.Path(__file__).resolve().parent / "example-r024-site"
Q.WORK = K / "work" / "r018"             # скриншот приложения Claude — тот же, что в R018

# ── чат с клиентом ───────────────────────────────────────────────────────────
T.NAME = "Анна"                           # имя клиента, без компании


@functools.lru_cache(None)
def client_avatar(d=128):
    ph = Image.open(K / "work" / "r019" / "av_anna.jpg").convert("RGB")
    s = ph.width * 0.62; ph = ph.crop(((ph.width - s) / 2, ph.height * 0.02, (ph.width + s) / 2, ph.height * 0.02 + s))
    ph = ph.resize((d, d), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", (d * 4, d * 4), 0); ImageDraw.Draw(m).ellipse([0, 0, d * 4 - 1, d * 4 - 1], fill=255)
    ph.putalpha(m.resize((d, d), Image.LANCZOS)); return ph


T.harvi_avatar = client_avatar
SUB = "в сети"
CHAT = [  # (время, кто: in — клиент / out — Иван, текст, файл (имя, размер, тип) | None)
    (0.15, "in", "Здравствуйте! Нужен сайт для нашего бренда", None),
    (0.80, "out", "Скиньте брендбук и логотип", None),
    (1.40, "in", None, ("Брендбук.pdf", "18,4 МБ", "PDF")),
    (1.70, "in", None, ("Логотип.svg", "36 КБ", "SVG")),
]
A = 2.55                                  # конец чата
CHAT_CAPS = [(0.0, A - 0.25, [("Клиенту нужен сайт", OFF, GRAPH)])]


@functools.lru_cache(None)
def bubble(k):
    _, who, text, file = CHAT[k]
    f = T.ui(T.BF, False); tf = T.ui(30, False)
    lines = T.wrap(text, f, T.TEXT_W) if text else []
    tw = max([f.getlength(l) for l in lines] + [0]); fh = 0
    if file:
        fh = 130; tw = max(tw, 122 + T.ui(40).getlength(file[0]), 300)
    if lines: tw = max(tw, f.getlength(lines[-1]) + 110)
    bw, bh = int(tw + 2 * T.PADX), int(len(lines) * T.LH + fh + 2 * T.PADY + (8 if lines else 30))
    im = Image.new("RGBA", (T.SW, bh)); d = ImageDraw.Draw(im)
    out = who == "out"; x0 = T.SW - 24 - bw if out else 24
    d.rounded_rectangle([x0, 0, x0 + bw, bh], T.RAD, fill=(T.OUTB if out else T.INB) + (255,))
    mut = T.OUTMUTED if out else T.INMUTED; y = T.PADY
    for l in lines:
        d.text((x0 + T.PADX, y + T.LH / 2), l, font=f, fill=T.TXT, anchor="lm"); y += T.LH
    if file:
        r = 50; T.doc_icon(d, x0 + T.PADX + r, y + r + 4, r)
        d.text((x0 + T.PADX + 2 * r + 22, y + 30), file[0], font=T.ui(40), fill=T.TXT, anchor="lm")
        d.text((x0 + T.PADX + 2 * r + 22, y + 80), f"{file[1]} · {file[2]}", font=T.ui(32, False), fill=mut, anchor="lm")
    tm = "18:45"; tx = x0 + bw - T.PADX - tf.getlength(tm) - (44 if out else 0)
    d.text((tx, bh - T.PADY - 14), tm, font=tf, fill=mut, anchor="lm")
    if out: T.checks(d, x0 + bw - T.PADX - 36, bh - T.PADY - 12, mut)
    return im


def chat_screen(t):
    im = T.empty_chat(SUB).crop((0, 0, T.SW, T.SHW)).copy(); items, y = [], 30
    for k, c in enumerate(CHAT):
        if t < c[0]: break
        b = bubble(k); extra = 12 if k + 1 < len(CHAT) and CHAT[k + 1][1] != c[1] else 0
        items.append((b, y, prog(t, c[0], 0.32))); y += lerp(0, b.height + T.GAP + extra, eout(prog(t, c[0], 0.28)))
    for spr, yy, p in items:
        if p >= 1: put(im, spr, 0, T.MSG_Y0 + yy)
        else:
            s = lerp(0.9, 1.0, eback(p)); sp = spr.resize((int(spr.width * s), max(1, int(spr.height * s))), Image.BICUBIC)
            put(im, sp, (T.SW - sp.width) / 2, T.MSG_Y0 + yy + (spr.height - sp.height) / 2 + 24 * (1 - eout(p)), eout(p * 1.6))
    im.alpha_composite(T.top_layer(SUB), (0, 0))
    im.alpha_composite(T.bottom_layer(), (0, T.SHW - T.bottom_layer().height))
    return im


def caps(fr, t, lst, size=60, y=356):
    for a, b, rows in lst:
        if a <= t < b + 0.3:
            o = ss(prog(t, b, 0.25))
            plates(fr, rows, size, y, lambda k: clamp(prog(t, a + 0.1 * k, 0.35) - o))


def chat_frame(t, with_caps=True):
    fr = background().copy()
    c = chat_screen(t).resize((T.CW, T.CHH), Image.LANCZOS); c.putalpha(T.card_mask())
    ImageDraw.Draw(c).rounded_rectangle([0, 0, T.CW - 1, T.CHH - 1], 44, outline=(255, 255, 255, 40), width=2)
    put(fr, T.card_shadow(), T.CX0 - 80, T.CY0 - 100); put(fr, c, T.CX0, T.CY0)
    if with_caps: caps(fr, t, CHAT_CAPS)
    return fr


# ── Claude: короткий таймлайн, карточка уже на месте ─────────────────────────
Q.PROMPT = ("Сделай сайт для бренда по брендбуку: цвета, шрифты и логотип бери из файлов, "
            "главная — новинки, хиты, каталог, где купить")
P.FILES = [("Брендбук", "PDF", (200, 60, 50)), ("Логотип", "SVG", (226, 140, 40))]
Q.T_CARD = -1.0
Q.T_TYPE = (0.1, 0.8)
Q.CUR_PLUS = (0.82, 1.0); Q.T_CLICK_PLUS = 1.03
Q.T_REFS = [1.1, 1.25]
Q.CUR_SEND = (1.32, 1.52); Q.T_SEND = 1.55
Q.T_VIEW = 99.0                           # презентации нет — после отправки сразу сайт
CL = 2.0                                  # длительность экрана Claude
Q.CAPS = [(0.0, CL - 0.2, [("Закидываю в Claude", OFF, GRAPH)])]

# ── сайт в браузере ──────────────────────────────────────────────────────────
BX0, BX1, BY0, BY1 = 90, 990, 660, 1620
BW, BH = BX1 - BX0, BY1 - BY0; BAR = 74
SITE_LEN = 3.05
SCROLL = (0.35, 2.35); SCROLL_TO = 4380   # до блока «Где купить?» (пикселей страницы 1440)
SITE_CAPS = [(0.05, 1.35, [("Готово", BLUE, OFF)]),
             (1.45, 99, [("Напишите в комментариях", OFF, GRAPH), ("«САЙТ» — пришлю промпт", BLUE, OFF)])]
TOT = A + CL + SITE_LEN


@functools.lru_cache(None)
def page():
    im = Image.open(WORK / "site-full.png").convert("RGB"); s = BW / im.width
    return im.resize((BW, int(im.height * s)), Image.LANCZOS), s


@functools.lru_cache(None)
def browser_bar():
    im = Image.new("RGBA", (BW, BAR), (236, 236, 239, 255)); d = ImageDraw.Draw(im)
    for k, col in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        d.ellipse([26 + k * 30, BAR / 2 - 9, 44 + k * 30, BAR / 2 + 9], fill=col)
    d.rounded_rectangle([150, 14, BW - 150, BAR - 14], 23, fill=(255, 255, 255, 255))
    f = T.ui(26, False); s = "36kopeek.ru"; tw = f.getlength(s)
    lx = BW / 2 - tw / 2 - 16                 # замок
    d.rounded_rectangle([lx - 10, BAR / 2 - 2, lx + 4, BAR / 2 + 10], 3, fill=(110, 110, 115))
    d.arc([lx - 8, BAR / 2 - 13, lx + 2, BAR / 2 + 1], 180, 360, fill=(110, 110, 115), width=3)
    d.text((BW / 2 + 6, BAR / 2), s, font=f, fill=(40, 40, 45), anchor="mm")
    d.line([(0, BAR - 1), (BW, BAR)], fill=(210, 210, 215), width=2)
    return im


@functools.lru_cache(None)
def bmask(): return T.rr_mask(BW, BH, 40)


@functools.lru_cache(None)
def bshadow():
    im = Image.new("RGBA", (BW + 160, BH + 160)); ImageDraw.Draw(im).rounded_rectangle([80, 100, 80 + BW, 100 + BH], 40, fill=(0, 0, 0, 170))
    from PIL import ImageFilter
    return im.filter(ImageFilter.GaussianBlur(30))


def site_frame(t):
    fr = background().copy()
    pg, s = page(); off = ss(prog(t, SCROLL[0], SCROLL[1] - SCROLL[0])) * SCROLL_TO * s
    c = Image.new("RGBA", (BW, BH), (255, 255, 255, 255))
    c.paste(pg.crop((0, int(off), BW, int(off) + BH - BAR)), (0, BAR))
    c.alpha_composite(browser_bar()); c.putalpha(bmask())
    ImageDraw.Draw(c).rounded_rectangle([0, 0, BW - 1, BH - 1], 40, outline=(255, 255, 255, 40), width=2)
    wp = eout(prog(t, 0, 0.4)); sc = lerp(0.94, 1.0, wp)
    cs = c.resize((int(BW * sc), int(BH * sc)), Image.LANCZOS) if sc < 1 else c
    x, y = BX0 + (BW - cs.width) / 2, BY0 + (BH - cs.height) / 2 + 40 * (1 - wp)
    put(fr, bshadow(), BX0 - 80, y - 100, wp); put(fr, cs, x, y, clamp(wp * 1.3))
    caps(fr, t, SITE_CAPS)
    return fr


# ── сборка ───────────────────────────────────────────────────────────────────
COVER = [("Клиенту нужен сайт", OFF, GRAPH), ("Брендбук → Claude", BLUE, OFF)]


def make_cover():
    fr = chat_frame(2.3, with_caps=False)
    dim = Image.new("RGBA", (W, H), (17, 19, 21, 90)); fr.alpha_composite(dim)
    plates(fr, COVER, 84, 760, lambda k: 1.0)
    fr.convert("RGB").save(OUT / "cover.jpg", quality=95)


def at(i):
    t = i / FPS; XF = R.XF
    if t < A:
        fr = chat_frame(t).convert("RGB")
        if t > A - XF: fr = xfade(fr, Q.frame(0), (t - (A - XF)) / XF)
    elif t < A + CL:
        fr = Q.frame(t - A)
        if t > A + CL - XF: fr = xfade(fr, site_frame(0).convert("RGB"), (t - (A + CL - XF)) / XF)
    else:
        fr = site_frame(t - A - CL).convert("RGB")
    return fr


def main(peek=None):
    OUT.mkdir(exist_ok=True); WORK.mkdir(exist_ok=True)
    if peek:
        for s in peek: at(int(s * FPS)).save(WORK / f"peek_{s}.png")
        return
    sfx = [("sfx-pop.mp3", c[0], 0.2) for c in CHAT]
    sfx += [("sfx-click.mp3", A + Q.T_CLICK_PLUS, 0.25), ("sfx-click.mp3", A + Q.T_SEND, 0.25)]
    sfx += [("sfx-pop.mp3", A + ta, 0.12) for ta in Q.T_REFS]
    sfx += [("sfx-pop.mp3", A + CL + 0.05, 0.16), ("sfx-pop.mp3", A + CL + SITE_CAPS[1][0], 0.18)]
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
