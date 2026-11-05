"""Ролик «Сайт за 120 000 ₽ — из брендбука клиента» (сценарий R033), ~8,4 с, без голоса. Улучшенный R024.

Результат сначала: первый экран 36kopeek.ru крупно + уведомление «+ 60 000 ₽» (предоплата 50%) →
чат: клиент присылает брендбук и логотип, «120 000 ₽, предоплата 50%», «Ок, оплатил» →
экран Claude (как R024) → сайт листается вниз и возвращается к первому экрану — ролик зацикливается.

По аналитике 05.11: результат и деньги в первом кадре, телефон/браузер крупнее, конец = начало.
Части — из r024_site (чат, Claude, сайт work/r024/site-full.png) и r030_silent (крупная карточка, payment_note).

    python r033_brandbook.py              # -> example-r033-brandbook/final.mp4, cover.jpg
    python r033_brandbook.py peek 0.5 3 6 # кадры work/r033/peek_<t>.png
"""
import os, sys, pathlib, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r024_site as V
import r019_harvi as T
import r017_presentation as Q
import payment_note
import r014_avito as R
from r014_avito import (W, H, FPS, GRAPH, OFF, BLUE, K, clamp, prog, eout, ss, eback, lerp, put, plates,
                        background, xfade)

WORK = pathlib.Path(os.environ.get("R033_WORK", K / "work" / "r033"))
OUT = pathlib.Path(__file__).resolve().parent / "example-r033-brandbook"
AMOUNT = 60000                                        # предоплата 50% от 120 000 ₽; суммы в роликах разные

# ── крупнее: чат 980 px (как R030), браузер 1000 px вместо 900 ───────────────
T.CX0, T.CX1, T.CY0, T.CY1 = 50, 1030, 600, 1660
T.CW, T.CHH = T.CX1 - T.CX0, T.CY1 - T.CY0
T.SC = T.CW / T.SW; T.SHW = int(round(T.CHH / T.SC))
T.MSG_Y1 = T.SHW - (T.SH - T.BOT_Y0)
V.BX0, V.BX1, V.BY0, V.BY1 = 40, 1040, 600, 1680
V.BW, V.BH = V.BX1 - V.BX0, V.BY1 - V.BY0


# ── чат: новый клиент ────────────────────────────────────────────────────────
@functools.lru_cache(None)
def face(path, d=128):
    ph = Image.open(path).convert("RGB")
    s = ph.width * 0.62; ph = ph.crop(((ph.width - s) / 2, ph.height * 0.02, (ph.width + s) / 2, ph.height * 0.02 + s))
    ph = ph.resize((d, d), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", (d * 4, d * 4), 0); ImageDraw.Draw(m).ellipse([0, 0, d * 4 - 1, d * 4 - 1], fill=255)
    ph.putalpha(m.resize((d, d), Image.LANCZOS)); return ph


T.NAME = "Игорь"; T.harvi_avatar = lambda d=128: face(K / "work" / "r019" / "av_igor.jpg", d)
T.empty_chat.cache_clear()
V.CHAT = [
    (0.10, "in", "Здравствуйте! Нужен сайт в нашем фирменном стиле", None),
    (0.40, "in", None, ("Брендбук.pdf", "18,4 МБ", "PDF")),
    (0.60, "in", None, ("Логотип.svg", "36 КБ", "SVG")),
    (0.95, "out", "120 000 ₽, предоплата 50%", None),
    (1.40, "in", "Ок, оплатил", None),
]
C_LEN = 2.0
V.CHAT_CAPS = [(0.0, C_LEN - 0.2, [("Клиент прислал брендбук", OFF, GRAPH)])]
CL = V.CL                                              # экран Claude — как в R024


@functools.lru_cache(None)
def note():
    im = Image.open(payment_note.make(AMOUNT, WORK / "payment.png")).convert("RGBA"); w = 880
    im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    sh = Image.new("RGBA", (w + 80, im.height + 80)); ImageDraw.Draw(sh).rounded_rectangle([40, 50, 40 + w, 50 + im.height], 40, fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(18)); sh.alpha_composite(im, (40, 40)); return sh


# ── сайт ─────────────────────────────────────────────────────────────────────
def browser(off, sc=1.0):
    pg, s = V.page()
    c = Image.new("RGBA", (V.BW, V.BH), (255, 255, 255, 255))
    c.paste(pg.crop((0, int(off * s), V.BW, int(off * s) + V.BH - V.BAR)), (0, V.BAR))
    c.alpha_composite(V.browser_bar()); c.putalpha(V.bmask())
    ImageDraw.Draw(c).rounded_rectangle([0, 0, V.BW - 1, V.BH - 1], 40, outline=(255, 255, 255, 40), width=2)
    if sc != 1.0: c = c.resize((int(V.BW * sc), int(V.BH * sc)), Image.LANCZOS)
    return c


def site_on(fr, c, dy=0, a=1.0):
    x, y = V.BX0 + (V.BW - c.width) / 2, V.BY0 + (V.BH - c.height) / 2 + dy
    put(fr, V.bshadow(), V.BX0 - 80, V.BY0 - 100 + dy, a); put(fr, c, x, y, a)


HOOK = [("Сайт за 120 000 ₽ —", OFF, GRAPH), ("из брендбука клиента", BLUE, OFF)]
S_LEN = 1.5
T_NOTE0 = 0.3
NOTE_Y = 1330


def result_frame(t, caps=True, dy=0):
    """Первая сцена: сайт уже на экране (без въезда), лёгкий наезд, на 0,3 с — уведомление об оплате."""
    fr = background().copy()
    site_on(fr, browser(0, 1 + 0.025 * ss(prog(t, 0, S_LEN))), dy)
    if t >= T_NOTE0:
        p = eback(prog(t, T_NOTE0, 0.45)); n = note()
        put(fr, n, (W - n.width) / 2, NOTE_Y + dy + 160 * (1 - p), clamp(p * 1.6))
    if caps: V.caps(fr, t, [(0.0, 99, HOOK)])
    return fr


E_LEN = 3.0
DOWN = (0.25, 1.55); UP = (2.0, 2.75); DEPTH = 3000     # вниз на 2–3 блока и обратно к первому экрану
E_CAPS = [(0.05, 99, [("Сайт в стиле бренда", BLUE, OFF)])]


def end_frame(t):
    fr = background().copy()
    off = DEPTH * (ss(prog(t, DOWN[0], DOWN[1] - DOWN[0])) - ss(prog(t, UP[0], UP[1] - UP[0])))
    wp = eout(prog(t, 0, 0.4)); c = browser(off, lerp(0.94, 1.0, wp))
    site_on(fr, c, 40 * (1 - wp), clamp(wp * 1.3))
    V.caps(fr, t, E_CAPS)
    return fr


Q.CAPS = [(0.0, CL - 0.2, [("Закидываю в Claude", OFF, GRAPH)])]
SCENES = [(S_LEN, result_frame), (C_LEN, lambda t: V.chat_frame(t)), (CL, Q.frame), (E_LEN, end_frame)]
TOT = sum(d for d, _ in SCENES)


def at(i):
    t = i / FPS; XF = R.XF; t0 = 0.0
    for j, (dur, fn) in enumerate(SCENES):
        if t < t0 + dur or j == len(SCENES) - 1:
            fr = fn(t - t0).convert("RGB")
            if j + 1 < len(SCENES) and t > t0 + dur - XF:
                fr = xfade(fr, SCENES[j + 1][1](0).convert("RGB"), (t - (t0 + dur - XF)) / XF)
            return fr
        t0 += dur


def make_cover():
    fr = result_frame(S_LEN, caps=False, dy=140)          # на обложке сайт ниже хука
    plates(fr, HOOK, 76, 450, lambda k: 1.0)
    fr.convert("RGB").save(OUT / "cover.jpg", quality=95)


def main(peek=None):
    OUT.mkdir(exist_ok=True); WORK.mkdir(parents=True, exist_ok=True)
    if peek:
        for s in peek: at(int(s * FPS)).save(WORK / f"peek_{s}.png")
        return
    sfx = [("sfx-click.mp3", T_NOTE0, 0.3)]
    sfx += [("sfx-pop.mp3", S_LEN + c[0], 0.2) for c in V.CHAT]
    a = S_LEN + C_LEN
    sfx += [("sfx-click.mp3", a + Q.T_CLICK_PLUS, 0.25), ("sfx-click.mp3", a + Q.T_SEND, 0.25)]
    sfx += [("sfx-pop.mp3", a + ta, 0.12) for ta in Q.T_REFS]
    sfx += [("sfx-pop.mp3", a + CL + 0.05, 0.16)]
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
