"""Ролики R028 «Клиент хочет сайт как с Pinterest» и R029 «Сможете так — закажу», без голоса.

Формат R024: чат Telegram → экран Claude (промпт и вложения размыты) → браузер с сайтом кофейни.
- R028: клиент присылает видео с Pinterest → цена → чек → Claude → сайт → призыв «пришлите свой вау-сайт».
- R029: видео + «сможете такой — закажу» → «Сейчас покажу» → Claude → сайт → снова чат: ссылка → «куда скинуть предоплату?».

Исходники (в work/r028, в репо не кладутся):
- pin/p%04d.jpg — кадры видео пина (ffmpeg -i pin-video-720.mp4 -vf fps=30 pin/p%04d.jpg);
- site/f%04d.jpg + site/times.json — запись сайта https://ivanweb1.github.io/coffee-wow-demo/?demo=1 (work/r028/capture.py).

    python r028_pin.py r028            # -> example-r028-pin/final.mp4, cover.jpg
    python r028_pin.py r029            # -> example-r029-prepay/final.mp4, cover.jpg
    python r028_pin.py r028 peek 1 4 7 # кадры work/r028/peek_r028_<t>.png
"""
import os, sys, json, bisect, pathlib, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r024_site as S                     # чат, Claude и браузер из R024
from r024_site import T, Q, P, R
from r014_avito import (W, H, FPS, GRAPH, OFF, BLUE, K, clamp, prog, eout, ss, eback, lerp, put, plates, background, xfade)

VAR = (sys.argv[1] if len(sys.argv) > 1 else "r028").lower()
WORK = pathlib.Path(os.environ.get("R028_WORK", K / "work" / "r028"))
OUT = pathlib.Path(__file__).resolve().parent / ("example-r028-pin" if VAR == "r028" else "example-r029-prepay")

# ── сценарий ─────────────────────────────────────────────────────────────────
# (время, кто, текст, вложение): вложение ("video",) — видео пина в пузыре, ("link",) — ссылка на сайт (размыта)
if VAR == "r028":
    CHAT = [
        (0.15, "in", "Здравствуйте! Хочу такой сайт для нашей кофейни", ("video",)),
        (1.25, "out", "Здравствуйте! Такой сайт — 120 000 ₽", None),
        (1.85, "out", "Предоплата 50%, начинаю сразу после оплаты", None),
        (2.75, "in", "Отлично, оплатила", None),
        (3.15, "in", None, ("receipt_04.11.2026.pdf", "58,8 КБ", "PDF", "receipt")),
    ]
    A = 4.2
    CHAT_CAPS = [(0.0, A - 0.25, [("Клиент хочет сайт", OFF, GRAPH), ("как с Pinterest", BLUE, OFF)])]
    SITE_LEN = 3.7
    SITE_CAPS = [(0.05, 1.0, [("Готово", BLUE, OFF)]),
                 (1.35, 99, [("Забирай инструкцию для Claude", OFF, GRAPH), ("в описании", BLUE, OFF)])]
    END = []; END_LEN = 0.0
    COVER = [("Сайт как с Pinterest", OFF, GRAPH), ("Видео → Claude", BLUE, OFF)]; COVER_T = 1.2
else:
    CHAT = [
        (0.15, "in", "Здравствуйте! Если сделаете такой для нашей кофейни — закажу у вас сайт", ("video",)),
        (1.85, "out", "Здравствуйте! Сейчас покажу", None),
        # продолжение после сайта (время чата — после A)
        (10.15, "out", None, ("link",)),
        (10.85, "in", "Вау! Куда скинуть предоплату?", None),
    ]
    A = 3.1
    CHAT_CAPS = [(0.0, A - 0.25, [("Сможете так —", OFF, GRAPH), ("закажу", BLUE, OFF)])]
    SITE_LEN = 3.1
    SITE_CAPS = [(0.05, 1.1, [("Готово", BLUE, OFF)])]
    END_AT = 10.0; END_LEN = 2.35           # финал в чате; ролик кончается на реплике клиента
    END = [1]
    COVER = [("Сможете так —", OFF, GRAPH), ("закажу", BLUE, OFF)]; COVER_T = 1.4

# ── видео пина в пузыре Telegram ─────────────────────────────────────────────
VW = 640                                   # сторона видео в координатах экрана Telegram (1170)
PIN = sorted((WORK / "pin").glob("p*.jpg"))


@functools.lru_cache(64)
def pin_frame(i):
    im = Image.open(PIN[i % len(PIN)]).convert("RGBA").resize((VW, VW), Image.LANCZOS)
    im.putalpha(T.rr_mask(VW, VW, 30)); return im


def caption_lines(text):
    return T.wrap(text, T.ui(T.BF, False), VW - 2 * T.PADX + 16) if text else []


@functools.lru_cache(None)
def video_bubble_base(k):
    _, who, text, _ = CHAT[k]
    f = T.ui(T.BF, False); tf = T.ui(30, False); lines = caption_lines(text)
    bw = VW + 16; bh = 8 + VW + (T.PADY + len(lines) * T.LH + 44 if lines else 8)
    im = Image.new("RGBA", (T.SW, bh)); d = ImageDraw.Draw(im)
    x0 = 24; d.rounded_rectangle([x0, 0, x0 + bw, bh], T.RAD, fill=T.INB + (255,))
    y = 8 + VW + T.PADY
    for l in lines:
        d.text((x0 + T.PADX, y + T.LH / 2), l, font=f, fill=T.TXT, anchor="lm"); y += T.LH
    tm = "18:42"; d.text((x0 + bw - T.PADX - tf.getlength(tm), bh - T.PADY - 10), tm, font=tf, fill=T.INMUTED, anchor="lm")
    return im, x0


def video_bubble(k, tt):
    base, x0 = video_bubble_base(k); im = base.copy()
    im.alpha_composite(pin_frame(int(max(0.0, tt) * 30)), (x0 + 8, 8))
    d = ImageDraw.Draw(im); f = T.ui(28, False)       # бейдж длительности, как у видео в Telegram
    left = max(0, 9 - int(max(0.0, tt)) % 9); s = f"0:{left:02d}"
    d.rounded_rectangle([x0 + 24, 24, x0 + 24 + f.getlength(s) + 28, 66], 21, fill=(0, 0, 0, 120))
    d.text((x0 + 38, 45), s, font=f, fill=(255, 255, 255), anchor="lm")
    return im


# ── ссылка на сайт (R029): адрес размыт, превью — кадр сайта ────────────────
@functools.lru_cache(None)
def link_bubble():
    f = T.ui(T.BF, False); tf = T.ui(30, False)
    pw = 600; ph = int(pw * 900 / 1440)
    bw = pw + 2 * T.PADX; bh = T.PADY + T.LH + 14 + ph + 70 + T.PADY
    im = Image.new("RGBA", (T.SW, bh)); d = ImageDraw.Draw(im)
    x0 = T.SW - 24 - bw; d.rounded_rectangle([x0, 0, x0 + bw, bh], T.RAD, fill=T.OUTB + (255,))
    txt = Image.new("RGBA", im.size); ImageDraw.Draw(txt).text((x0 + T.PADX, T.PADY + T.LH / 2), "https://zerno-demo.site/coffee",
                                                            font=f, fill=(160, 205, 255), anchor="lm")
    im.alpha_composite(txt.filter(ImageFilter.GaussianBlur(9)))          # адрес размыт (правило R019)
    y = T.PADY + T.LH + 14
    d.rounded_rectangle([x0 + T.PADX - 14, y, x0 + T.PADX - 8, y + ph], 3, fill=(120, 180, 255))
    pv = site_img(0.2, pw, ph).convert("RGBA"); pv.putalpha(T.rr_mask(pw, ph, 16))
    im.alpha_composite(pv, (x0 + T.PADX, y))
    tm = "18:47"; tx = x0 + bw - T.PADX - tf.getlength(tm) - 44
    d.text((tx, bh - T.PADY - 14), tm, font=tf, fill=T.OUTMUTED, anchor="lm")
    T.checks(d, x0 + bw - T.PADX - 36, bh - T.PADY - 12, T.OUTMUTED)
    return im


S.CHAT = CHAT                                    # bubble() из R024 рисует текст и чек по этому списку


def sprite(k, t):
    file = CHAT[k][3]
    if file == ("video",): return video_bubble(k, t - CHAT[k][0])
    if file == ("link",): return link_bubble()
    return S.bubble(k)


def chat_screen(t):
    im = T.empty_chat(S.SUB).crop((0, 0, T.SW, T.SHW)).copy(); items, y = [], 30
    for k, c in enumerate(CHAT):
        if t < c[0]: break
        b = sprite(k, t); extra = 12 if k + 1 < len(CHAT) and CHAT[k + 1][1] != c[1] else 0
        items.append((b, y, prog(t, c[0], 0.32))); y += lerp(0, b.height + T.GAP + extra, eout(prog(t, c[0], 0.28)))
    shift = max(0, y - T.GAP - (T.MSG_Y1 - T.MSG_Y0 - 40))
    for spr, yy, p in items:
        yy -= shift
        if p >= 1: put(im, spr, 0, T.MSG_Y0 + yy)
        else:
            s = lerp(0.9, 1.0, eback(p)); sp = spr.resize((int(spr.width * s), max(1, int(spr.height * s))), Image.BICUBIC)
            put(im, sp, (T.SW - sp.width) / 2, T.MSG_Y0 + yy + (spr.height - sp.height) / 2 + 24 * (1 - eout(p)), eout(p * 1.6))
    im.alpha_composite(T.top_layer(S.SUB), (0, 0))
    im.alpha_composite(T.bottom_layer(), (0, T.SHW - T.bottom_layer().height))
    return im


def chat_frame(t, caps=None):
    fr = background().copy()
    c = chat_screen(t).resize((T.CW, T.CHH), Image.LANCZOS); c.putalpha(T.card_mask())
    ImageDraw.Draw(c).rounded_rectangle([0, 0, T.CW - 1, T.CHH - 1], 44, outline=(255, 255, 255, 40), width=2)
    put(fr, T.card_shadow(), T.CX0 - 80, T.CY0 - 100); put(fr, c, T.CX0, T.CY0)
    if caps: S.caps(fr, t, caps)
    return fr


# ── Claude: видео и кадры прикрепляются, всё размыто ─────────────────────────
Q.PROMPT = ("Сделай первый экран сайта кофейни как на этом видео: карточка над градиентом, напиток по центру, "
            "при переключении перекрашивается вся тема. Фото напитков сгенерируй")
P.FILES = [("видео Pinterest", "MP4", (124, 77, 200)), ("кадр 1", "PNG", (226, 140, 40)), ("кадр 2", "PNG", (60, 60, 66))]


@functools.lru_cache(None)
def blurred_tile(k):
    im = P.file_card(k); return im.filter(ImageFilter.GaussianBlur(5))   # вложения размыты (Иван, 04.11)


Q.tile = blurred_tile
Q.BLUR_TEXT = True
Q.T_REFS = [1.05, 1.17, 1.29]
CL = S.CL
Q.CAPS = [(0.0, CL - 0.2, [("Кидаю видео в Claude", OFF, GRAPH)])]

# ── сайт: запись экрана ?demo=1, ускорена ────────────────────────────────────
SITE_FROM, SPEED = 2.0, 2.2               # с какой секунды записи и во сколько раз быстрее
TIMES = json.loads((WORK / "site" / "times.json").read_text())
ORDER = sorted(range(len(TIMES)), key=lambda i: TIMES[i]); ST = [TIMES[i] for i in ORDER]
BX0, BX1 = 60, 1020; BW = BX1 - BX0; BAR = 74
PH = int(BW * 900 / 1440); BH = PH + BAR; BY0 = 640


@functools.lru_cache(8)
def site_img(rt, w=BW, h=PH):
    j = min(len(ST) - 1, bisect.bisect_left(ST, rt)); i = ORDER[j]
    return Image.open(WORK / "site" / f"f{i:04d}.jpg").convert("RGB").resize((w, h), Image.LANCZOS)


@functools.lru_cache(None)
def browser_bar():
    im = Image.new("RGBA", (BW, BAR), (236, 236, 239, 255)); d = ImageDraw.Draw(im)
    for k, col in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        d.ellipse([26 + k * 30, BAR / 2 - 9, 44 + k * 30, BAR / 2 + 9], fill=col)
    d.rounded_rectangle([150, 14, BW - 150, BAR - 14], 23, fill=(255, 255, 255, 255))
    d.rounded_rectangle([BW / 2 - 110, BAR / 2 - 6, BW / 2 + 110, BAR / 2 + 6], 6, fill=(205, 205, 210))   # адрес размыт
    d.line([(0, BAR - 1), (BW, BAR)], fill=(210, 210, 215), width=2)
    return im


@functools.lru_cache(None)
def bmask(): return T.rr_mask(BW, BH, 40)


@functools.lru_cache(None)
def bshadow():
    im = Image.new("RGBA", (BW + 160, BH + 160)); ImageDraw.Draw(im).rounded_rectangle([80, 100, 80 + BW, 100 + BH], 40, fill=(0, 0, 0, 170))
    return im.filter(ImageFilter.GaussianBlur(30))


def site_frame(t):
    fr = background().copy()
    c = Image.new("RGBA", (BW, BH), (255, 255, 255, 255))
    c.paste(site_img(round((SITE_FROM + t * SPEED) * 60) / 60), (0, BAR))
    c.alpha_composite(browser_bar()); c.putalpha(bmask())
    ImageDraw.Draw(c).rounded_rectangle([0, 0, BW - 1, BH - 1], 40, outline=(255, 255, 255, 40), width=2)
    wp = eout(prog(t, 0, 0.4)); sc = lerp(0.94, 1.0, wp)
    cs = c.resize((int(BW * sc), int(BH * sc)), Image.LANCZOS) if sc < 1 else c
    x, y = BX0 + (BW - cs.width) / 2, BY0 + (BH - cs.height) / 2 + 40 * (1 - wp)
    put(fr, bshadow(), BX0 - 80, y - 100, wp); put(fr, cs, x, y, clamp(wp * 1.3))
    S.caps(fr, t, SITE_CAPS[:1]); S.caps(fr, t, SITE_CAPS[1:], size=56)
    return fr


# ── сборка ───────────────────────────────────────────────────────────────────
TS = A + CL                                # начало сайта
TE = TS + SITE_LEN                         # начало финала в чате (R029)
TOT = TE + END_LEN


def make_cover():
    fr = chat_frame(COVER_T)
    plates(fr, COVER, 84, 450, lambda k: 1.0)
    fr.convert("RGB").save(OUT / "cover.jpg", quality=95)


def at(i):
    t = i / FPS; XF = R.XF
    if t < A:
        fr = chat_frame(t, CHAT_CAPS).convert("RGB")
        if t > A - XF: fr = xfade(fr, Q.frame(0), (t - (A - XF)) / XF)
    elif t < TS:
        fr = Q.frame(t - A)
        if t > TS - XF: fr = xfade(fr, site_frame(0).convert("RGB"), (t - (TS - XF)) / XF)
    elif t < TE:
        fr = site_frame(t - TS).convert("RGB")
        if END_LEN and t > TE - XF: fr = xfade(fr, chat_frame(END_AT).convert("RGB"), (t - (TE - XF)) / XF)
    else:
        fr = chat_frame(END_AT + (t - TE)).convert("RGB")
    return fr


def main(peek=None):
    OUT.mkdir(exist_ok=True); WORK.mkdir(exist_ok=True)
    if peek:
        for s in peek: at(int(s * FPS)).save(WORK / f"peek_{VAR}_{s}.png")
        return
    sfx = [("sfx-pop.mp3", c[0], 0.2) for c in CHAT if c[0] < A]
    sfx += [("sfx-click.mp3", A + Q.T_CLICK_PLUS, 0.25), ("sfx-click.mp3", A + Q.T_SEND, 0.25)]
    sfx += [("sfx-pop.mp3", A + ta, 0.12) for ta in Q.T_REFS]
    sfx += [("sfx-pop.mp3", TS + 0.05, 0.16)]
    sfx += [("sfx-pop.mp3", TS + c[0], 0.18) for c in SITE_CAPS[1:]]
    sfx += [("sfx-pop.mp3", TE + (c[0] - END_AT), 0.2) for c in CHAT if END_LEN and c[0] >= END_AT]
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
    if sys.argv[2:3] == ["peek"]:
        main([float(s) for s in sys.argv[3:]])
    else:
        main()
