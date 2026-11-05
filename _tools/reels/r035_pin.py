"""Ролик «Сайт как с Pinterest — за 100 000 ₽» (сценарий R035), ~8,6 с, без голоса. Улучшенный R028/R029.

Результат сначала: сайт кофейни «Зерно» в браузере, на 0,6 с тема перекрашивается (карамель → эспрессо),
на 0,3 с — уведомление «+ 50 000 ₽» (предоплата 50%) → чат: видео с Pinterest «хочу такой сайт для кофейни»,
«100 000 ₽, предоплата 50%», «Ок, оплатил» → экран Claude (видео и кадры размыты, как R028) →
сайт: эспрессо → матча → карамель; конец на карамели, как первый кадр — ролик зацикливается.

Части — из r028_pin (видео пина в чате, запись сайта work/r028/site, Claude) и r033_brandbook (результат сначала).

    python r035_pin.py              # -> example-r035-pin/final.mp4, cover.jpg
    python r035_pin.py peek 0.5 3   # кадры work/r035/peek_<t>.png
"""
import os, sys, pathlib, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
_argv = sys.argv; sys.argv = [_argv[0], "r028"]       # r028_pin выбирает вариант по argv при импорте
import r028_pin as M
sys.argv = _argv
from r028_pin import S, T, Q, R
import payment_note
from r014_avito import (W, H, FPS, GRAPH, OFF, BLUE, K, clamp, prog, eout, ss, eback, lerp, put, plates,
                        background, xfade)

WORK = pathlib.Path(os.environ.get("R035_WORK", K / "work" / "r035"))
OUT = pathlib.Path(__file__).resolve().parent / "example-r035-pin"
AMOUNT = 50000                                        # 10 000 — R034, 35 000 — R030, 40 000 — R031, 45 000 — R032, 60 000 — R033

# ── крупнее: чат 980 px, браузер 1000 px ─────────────────────────────────────
T.CX0, T.CX1, T.CY0, T.CY1 = 50, 1030, 600, 1660
T.CW, T.CHH = T.CX1 - T.CX0, T.CY1 - T.CY0
T.SC = T.CW / T.SW; T.SHW = int(round(T.CHH / T.SC))
T.MSG_Y1 = T.SHW - (T.SH - T.BOT_Y0)
M.BX0, M.BX1 = 40, 1040; M.BW = M.BX1 - M.BX0
M.PH = int(M.BW * 900 / 1440); M.BH = M.PH + M.BAR; M.BY0 = 700
T.empty_chat.cache_clear()
if hasattr(T.top_layer, "cache_clear"): T.top_layer.cache_clear()

# ── чат ──────────────────────────────────────────────────────────────────────
M.CHAT = [
    (0.15, "in", "Здравствуйте! Хочу такой сайт для нашей кофейни", ("video",)),
    (0.95, "out", "100 000 ₽, предоплата 50%", None),
    (1.45, "in", "Ок, оплатила", None),           # клиентка — Анна, как в R028
]
S.CHAT = M.CHAT
C_LEN = 2.0
C_CAPS = [(0.0, C_LEN - 0.2, [("Клиент прислал видео", OFF, GRAPH), ("с Pinterest", BLUE, OFF)])]
CL = M.CL
Q.CAPS = [(0.0, CL - 0.2, [("Закидываю в Claude", OFF, GRAPH)])]


@functools.lru_cache(None)
def note():
    im = Image.open(payment_note.make(AMOUNT, WORK / "payment.png")).convert("RGBA"); w = 880
    im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    sh = Image.new("RGBA", (w + 80, im.height + 80)); ImageDraw.Draw(sh).rounded_rectangle([40, 50, 40 + w, 50 + im.height], 40, fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(18)); sh.alpha_composite(im, (40, 40)); return sh


# ── сайт ─────────────────────────────────────────────────────────────────────
def browser(rt, sc=1.0):
    c = Image.new("RGBA", (M.BW, M.BH), (255, 255, 255, 255))
    c.paste(M.site_img(round(rt * 60) / 60, M.BW, M.PH), (0, M.BAR))
    c.alpha_composite(M.browser_bar()); c.putalpha(M.bmask())
    ImageDraw.Draw(c).rounded_rectangle([0, 0, M.BW - 1, M.BH - 1], 40, outline=(255, 255, 255, 40), width=2)
    if sc != 1.0: c = c.resize((int(M.BW * sc), int(M.BH * sc)), Image.LANCZOS)
    return c


def site_on(fr, c, dy=0, a=1.0):
    x, y = M.BX0 + (M.BW - c.width) / 2, M.BY0 + (M.BH - c.height) / 2 + dy
    put(fr, M.bshadow(), M.BX0 - 80, M.BY0 - 100 + dy, a); put(fr, c, x, y, a)


HOOK = [("Сайт как с Pinterest —", OFF, GRAPH), ("за 100 000 ₽", BLUE, OFF)]
S_LEN = 1.5
R_FROM = 2.2                                          # запись: карамель, на 2,8 с — эспрессо
T_NOTE0 = 0.3
NOTE_Y = 1440


def result_frame(t, caps=True, dy=0, rt=None):
    fr = background().copy()
    site_on(fr, browser(R_FROM + t if rt is None else rt, 1 + 0.025 * ss(prog(t, 0, S_LEN))), dy)
    if t >= T_NOTE0:
        p = eback(prog(t, T_NOTE0, 0.45)); n = note()
        put(fr, n, (W - n.width) / 2, NOTE_Y + dy + 160 * (1 - p), clamp(p * 1.6))
    if caps: S.caps(fr, t, [(0.0, 99, HOOK)])
    return fr


E_LEN = 3.3
E_FROM, E_SPEED = 4.8, 1.6                            # эспрессо → матча (5,8) → карамель (8,7); конец на карамели
E_CAPS = [(0.05, 99, [("Сайт под их кофейню", BLUE, OFF)])]


def end_frame(t):
    fr = background().copy()
    wp = eout(prog(t, 0, 0.4)); c = browser(E_FROM + t * E_SPEED, lerp(0.94, 1.0, wp))
    site_on(fr, c, 40 * (1 - wp), clamp(wp * 1.3))
    S.caps(fr, t, E_CAPS)
    return fr


SCENES = [(S_LEN, result_frame), (C_LEN, lambda t: M.chat_frame(t, C_CAPS)), (CL, Q.frame), (E_LEN, end_frame)]
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
    fr = result_frame(S_LEN, caps=False, dy=60, rt=1.0)  # обложка: карамельный латте, сайт ниже хука
    plates(fr, HOOK, 76, 450, lambda k: 1.0)
    fr.convert("RGB").save(OUT / "cover.jpg", quality=95)


def main(peek=None):
    OUT.mkdir(exist_ok=True); WORK.mkdir(parents=True, exist_ok=True)
    if peek:
        for s in peek: at(int(s * FPS)).save(WORK / f"peek_{s}.png")
        return
    sfx = [("sfx-click.mp3", T_NOTE0, 0.3)]
    sfx += [("sfx-pop.mp3", S_LEN + c[0], 0.2) for c in M.CHAT]
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
