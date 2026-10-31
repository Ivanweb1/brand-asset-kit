"""Ролик «Тот самый клиент» — ответ на отзыв на картах через Харви (сценарий R020).

Аватар, сверху пуш от Харви с отзывом ★☆☆☆☆ → «Тот самый клиент, сейчас мы ему ответим.» →
чат Telegram «Харви» (пустой чат и шапка — из r019_harvi.py): карточка отзыва, три варианта ответа,
кнопки «1 / 2 / 3 / Свой вариант», выбор «2» → «Ответ опубликован» →
аватар: «Хотите такого агента? Напишите слово «ОТЗЫВ» в директ.»

Отзыв и ответы постановочные; имя автора и название заведения размыты (правило R019).

Исходники (не публикуются) — work/r020/: heygen-full.mp4 → hook.mp4, cta.mp4; clip.json — тайминги слов.

    python r020_reviews.py screen 1 3 6   # кадры экрана work/r020/screen_<t>.png (без аватара)
    python r020_reviews.py peek 1 5 9     # кадры ролика work/r020/peek_<t>.png
    python r020_reviews.py                # -> example-r020-reviews/final.mp4, cover.jpg
"""
import os, sys, json, math, pathlib, functools, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r019_harvi as T
from r019_harvi import (SW, TXT, ui, rr_mask, blur_box, rich_text, plain, wrap, harvi_avatar,
                        top_layer, bottom_layer, chat_bg, card_mask, card_shadow,
                        CX0, CY0, CW, CHH, SHW, MSG_Y0, MSG_Y1, INB, INMUTED, OUTB)
import r014_avito as R
from r014_avito import (W, H, FPS, GRAPH, OFF, BLUE, SS, clamp, prog, eout, ss, eback, lerp,
                        put, plates, font, down, background, Clip, avatar_frame, xfade)

K = T.K
WORK = pathlib.Path(os.environ.get("R020_WORK", K / "work" / "r020"))
OUT = pathlib.Path(__file__).resolve().parent / "example-r020-reviews"
R.CLIP_DIR = WORK

# ── текст ────────────────────────────────────────────────────────────────────
REVIEW = ("{Анна}", "Ждали заказ 40 минут, никто даже не извинился.")
PLACE = "{Кофейня «Зерно»}"
OPTIONS = [
    "{Анна}, извините за ожидание — так быть не должно. Разобрались со сменой, приходите снова — угостим десертом.",
    "{Анна}, спасибо, что написали. 40 минут — это слишком долго, мы уже поменяли порядок выдачи заказов. Будем рады исправиться.",
    "{Анна}, нам очень жаль. Напишите нам в директ — разберёмся лично и компенсируем ожидание.",
]
PICK = 1                                   # выбран вариант 2

# ── таймлайн экрана ──────────────────────────────────────────────────────────
T_REVIEW = 0.45
WRITING = [(1.05, 1.95)]
T_OPTIONS = 1.95
T_TAP = 5.6                                # нажатие «2»
T_DONE = 6.15
CH = 7.7
CAPS = [(0.2, 1.85, [("Новый отзыв —", OFF, GRAPH), ("сразу у Харви", BLUE, OFF)]),
        (1.95, 5.2, [("Три варианта ответа", OFF, GRAPH), ("в вашем тоне", BLUE, OFF)]),
        (5.6, CH - 0.2, [("Выбираю —", OFF, GRAPH), ("и готово", BLUE, OFF)])]

# ── аватар (заполняется по расшифровке, work/r020/clip.json) ──────────────────
HOOK_SUB = [[("О,", .2), ("тот", .4), ("самый", .6), ("клиент.", .9)], [("Сейчас", 1.4), ("мы", 1.7), ("ему", 1.85), ("ответим.", 2.0)]]
CTA_SUB = [[("Хотите", .2), ("такого", .5), ("агента?", .8)], [("Напишите", 1.4), ("«ОТЗЫВЫ»", 1.8)], [("в", 2.3), ("директ.", 2.4)]]
CTA_PL_AT = [.2, 1.8]; T_PUSH_CTA = 1.8; HOLD = 0.45
COVER_T = 1.0
COVER = [("Тот самый клиент", OFF, GRAPH), ("Сейчас ответим", BLUE, OFF)]
if (WORK / "clip.json").exists():
    _c = json.load(open(WORK / "clip.json", encoding="utf-8"))
    HOOK_SUB = [[tuple(w) for w in ln] for ln in _c["hook_sub"]]
    CTA_SUB = [[tuple(w) for w in ln] for ln in _c["cta_sub"]]
    CTA_PL_AT = _c["cta_pl"]; T_PUSH_CTA = _c.get("push_cta", CTA_PL_AT[1]); COVER_T = _c.get("cover_t", COVER_T)
CTA_PL = [(CTA_PL_AT[0], 99, [("Хотите такого агента?", OFF, GRAPH), ("«ОТЗЫВ» в директ", BLUE, OFF)], CTA_PL_AT)]

# ── экран: пузыри Харви ──────────────────────────────────────────────────────
GOLD = (255, 196, 46); DIM = (88, 100, 116)
PAD, RAD = 34, 38


def star(d, cx, cy, r, fill):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5; rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill)


def stars(d, x, cy, n, r=17):
    for k in range(5): star(d, x + r + k * (2 * r + 6), cy, r, GOLD if k < n else DIM)


@functools.lru_cache(None)
def review_bubble():
    """Харви пересылает новый отзыв: шапка, звёзды, автор, текст."""
    f = ui(40, False); lines = wrap(REVIEW[1], f, 900)
    bw = 980; bh = 60 + 48 + 46 + len(lines) * 52 + 56
    im = Image.new("RGBA", (SW, bh)); d = ImageDraw.Draw(im); x0 = 24
    d.rounded_rectangle([x0, 0, x0 + bw, bh], RAD, fill=INB + (255,))
    d.text((x0 + PAD, 46), "Новый отзыв на картах", font=ui(40), fill=(110, 175, 255), anchor="lm")
    y = 92; stars(d, x0 + PAD, y + 4, 1)
    rich_text(im, d, x0 + PAD + 200, y + 4, "· " + PLACE, ui(32, False), INMUTED)
    y += 46; rich_text(im, d, x0 + PAD, y + 4, REVIEW[0], ui(36), TXT)
    y += 30
    for l in lines: d.text((x0 + PAD, y + 26), l, font=f, fill=TXT, anchor="lm"); y += 52
    d.text((x0 + bw - PAD, bh - 34), "18:45", font=ui(30, False), fill=INMUTED, anchor="rm")
    return im


OF = 34; OLH = 44


@functools.lru_cache(None)
def options_bubble(sel=-1):
    """«Три варианта ответа» — пронумерованные, выбранный подсвечен."""
    f = ui(OF, False); bw = 1080
    blocks = [wrap(o, f, bw - 2 * PAD - 70) for o in OPTIONS]
    Q = 104                                       # цитата отзыва, как ответ на сообщение в Telegram
    bh = Q + 100 + sum(len(b) * OLH + 26 for b in blocks) + 34
    im = Image.new("RGBA", (SW, bh)); d = ImageDraw.Draw(im); x0 = 24
    d.rounded_rectangle([x0, 0, x0 + bw, bh], RAD, fill=INB + (255,))
    d.rounded_rectangle([x0 + 18, 18, x0 + bw - 18, 18 + Q - 8], 14, fill=(44, 60, 82, 255))
    d.rectangle([x0 + 18, 18, x0 + 25, 18 + Q - 8], fill=(110, 175, 255, 255))
    d.text((x0 + 44, 44), "Отзыв на картах", font=ui(32), fill=(110, 175, 255), anchor="lm")
    stars(d, x0 + 44 + ui(32).getlength("Отзыв на картах") + 14, 45, 1, r=13)
    d.text((x0 + 44, 84), "Ждали заказ 40 минут, никто даже не извинился.", font=ui(32, False), fill=(200, 210, 222), anchor="lm")
    d.text((x0 + PAD, Q + 52), "Три варианта ответа:", font=ui(40), fill=TXT, anchor="lm")
    y = Q + 100
    for k, b in enumerate(blocks):
        hh = len(b) * OLH + 16
        if k == sel:
            d.rounded_rectangle([x0 + 14, y - 10, x0 + bw - 14, y + hh], 22, fill=(52, 84, 122, 255), outline=(110, 175, 255, 255), width=3)
        d.ellipse([x0 + PAD, y + 4, x0 + PAD + 44, y + 48], fill=(110, 175, 255) if k == sel else DIM)
        d.text((x0 + PAD + 22, y + 26), str(k + 1), font=ui(30), fill=(255, 255, 255), anchor="mm")
        for j, l in enumerate(b):
            rich_text(im, d, x0 + PAD + 66, y + 26 + j * OLH, l, f, TXT)
        y += hh + 10
    d.text((x0 + bw - PAD, bh - 30), "18:45", font=ui(30, False), fill=INMUTED, anchor="rm")
    return im


KB_H = 92


@functools.lru_cache(None)
def keyboard(pressed=-1):
    """Инлайн-кнопки под сообщением бота."""
    labels = ["1", "2", "3", "Свой вариант"]; ws = [150, 150, 150, 402]; gap = 12; x = 24
    im = Image.new("RGBA", (SW, KB_H)); d = ImageDraw.Draw(im)
    for k, (s, w) in enumerate(zip(labels, ws)):
        on = k == pressed
        d.rounded_rectangle([x, 8, x + w, KB_H - 4], 24, fill=((110, 175, 255, 255) if on else (40, 54, 72, 235)))
        d.text((x + w / 2, (KB_H + 4) / 2), s, font=ui(38), fill=(255, 255, 255), anchor="mm"); x += w + gap
    return im


@functools.lru_cache(None)
def done_bubble():
    s = "Ответ опубликован"; f = ui(42, False); bw = int(f.getlength(s)) + 2 * PAD + 70 + 110; bh = 96
    im = Image.new("RGBA", (SW, bh)); d = ImageDraw.Draw(im); x0 = 24
    d.rounded_rectangle([x0, 0, x0 + bw, bh], RAD, fill=INB + (255,))
    cx, cy = x0 + PAD + 22, bh / 2
    d.ellipse([cx - 22, cy - 22, cx + 22, cy + 22], fill=(76, 196, 110))
    d.line([(cx - 11, cy), (cx - 3, cy + 9), (cx + 12, cy - 9)], fill=(255, 255, 255), width=6, joint="curve")
    d.text((x0 + PAD + 60, bh / 2), s, font=f, fill=TXT, anchor="lm")
    d.text((x0 + bw - PAD, bh / 2 + 10), "18:45", font=ui(30, False), fill=INMUTED, anchor="rm")
    return im


def screen(t):
    sub = "бот"
    for a, b in WRITING:
        if a <= t < b: sub = "печатает" + "." * (int((t - a) * 4) % 4)
    im = chat_bg().copy()
    sel = PICK if t >= T_TAP + 0.12 else -1
    seq = [(T_REVIEW, review_bubble()), (T_OPTIONS, options_bubble(sel))]
    kb_at = T_OPTIONS + 0.35
    items, y, gap = [], 30, 18
    for ta, b in seq:
        if t < ta: continue
        items.append((b, y, prog(t, ta, 0.32))); y += lerp(0, b.height + gap, eout(prog(t, ta, 0.28)))
    if t >= kb_at:
        kb = keyboard(PICK if T_TAP <= t < T_TAP + 0.35 else (-1 if t < T_TAP else -2))
        items.append((kb, y - gap + 6, prog(t, kb_at, 0.3))); y += lerp(0, KB_H + gap, eout(prog(t, kb_at, 0.28)))
    if t >= T_DONE:
        b = done_bubble(); items.append((b, y, prog(t, T_DONE, 0.32))); y += lerp(0, b.height + gap, eout(prog(t, T_DONE, 0.28)))
    shift = max(0, y - gap - (MSG_Y1 - MSG_Y0 - 10))
    for spr, yy, p in items:
        if p >= 1: put(im, spr, 0, MSG_Y0 + yy - shift)
        else:
            s = lerp(0.9, 1.0, eback(p)); sp = spr.resize((int(spr.width * s), max(1, int(spr.height * s))), Image.BICUBIC)
            put(im, sp, (SW - sp.width) / 2, MSG_Y0 + yy - shift + (spr.height - sp.height) / 2 + 24 * (1 - eout(p)), eout(p * 1.6))
    # палец-нажатие на «2»
    if T_TAP - 0.35 <= t < T_TAP + 0.5:
        bx = 24 + 150 + 12 + 75; by = MSG_Y0 + y - shift - KB_H - 18 - (done_bubble().height + 18 if t >= T_DONE else 0) + KB_H / 2
        p = prog(t, T_TAP - 0.35, 0.35); a = clamp(p * 2) * (1 - prog(t, T_TAP + 0.25, 0.25))
        r = lerp(70, 44, eout(p)); dot = Image.new("RGBA", (200, 200)); ImageDraw.Draw(dot).ellipse([100 - r, 100 - r, 100 + r, 100 + r], fill=(255, 255, 255, 110))
        put(im, dot, bx - 100, by - 100, a)
    im.alpha_composite(top_layer(sub), (0, 0))
    im.alpha_composite(bottom_layer(), (0, SHW - bottom_layer().height))
    return im


def screen_frame(t):
    fr = background().copy()
    wp = eout(prog(t, 0, 0.5)); y = CY0 + 520 * (1 - wp)
    c = screen(t).resize((CW, CHH), Image.LANCZOS); c.putalpha(card_mask())
    ImageDraw.Draw(c).rounded_rectangle([0, 0, CW - 1, CHH - 1], 44, outline=(255, 255, 255, 40), width=2)
    put(fr, card_shadow(), CX0 - 80, y - 100, wp); put(fr, c, CX0, y, wp)
    for a, b, rows in CAPS:
        if a <= t < b + 0.3:
            o = ss(prog(t, b, 0.25))
            plates(fr, rows, 60, 356, lambda k: clamp(prog(t, a + 0.1 * k, 0.35) - o))
    return fr.convert("RGB")


# ── пуш над аватаром ─────────────────────────────────────────────────────────
@functools.lru_cache(None)
def push():
    w, h = 880, 206; im = Image.new("RGBA", (w * SS, h * SS)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], 40 * SS, fill=(36, 37, 41, 250), outline=(255, 255, 255, 30), width=2 * SS)
    av = harvi_avatar(88 * SS); im.alpha_composite(av, (28 * SS, 30 * SS))
    tx = 136 * SS
    d.text((tx, 44 * SS), "ХАРВИ", font=font("SemiBold", 22 * SS), fill=(160, 160, 165, 255), anchor="lm")
    d.text(((w - 30) * SS, 44 * SS), "сейчас", font=font("Medium", 22 * SS), fill=(160, 160, 165, 255), anchor="rm")
    d.text((tx, 90 * SS), "Новый отзыв на картах", font=font("Bold", 32 * SS), fill=(250, 250, 250, 255), anchor="lm")
    tw = font("Bold", 32 * SS).getlength("Новый отзыв на картах")
    stars(d, tx + tw + 18 * SS, 92 * SS, 1, r=13 * SS)
    d.text((tx, 140 * SS), "«Ждали заказ 40 минут,", font=font("Medium", 29 * SS), fill=(225, 225, 228, 255), anchor="lm")
    d.text((tx, 178 * SS), "никто даже не извинился»", font=font("Medium", 29 * SS), fill=(225, 225, 228, 255), anchor="lm")
    return down(im)


T_PUSH = 0.1


def hook_frame(clip, t, dur):
    R.FACE_AT = (540, 1010)
    fr = avatar_frame(clip.at(int(t * FPS)), t, dur, HOOK_SUB, [])
    R.FACE_AT = (540, 870)
    fr = fr.convert("RGBA"); n = push()
    p = eback(prog(t, T_PUSH, 0.45)) - 1.2 * ss(prog(t, dur - 0.35, 0.3))
    put(fr, n, (W - n.width) / 2, 420 - 260 * (1 - p), clamp(p * 1.5))
    return fr.convert("RGB")


def clen(name):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 str(WORK / f"{name}.mp4")], capture_output=True, text=True).stdout)


def make_cover():
    src = Clip("hook").at(int(COVER_T * FPS)); z = 1.4
    x0 = clamp(R.FACE[0] - 540 / z, 0, W - W / z); y0 = clamp(R.FACE[1] - 1190 / z, 0, H - H / z)
    fr = src.transform((W, H), Image.AFFINE, (1 / z, 0, x0, 0, 1 / z, y0), Image.BICUBIC).convert("RGBA")
    plates(fr, COVER, 84, 560, lambda k: 1.0)
    fr.convert("RGB").save(OUT / "cover.jpg", quality=95)


def main(peek=None):
    OUT.mkdir(exist_ok=True)
    A = clen("hook"); Bo = clen("cta") + HOLD; TOT = A + CH + Bo; XF = R.XF
    hook, cta = Clip("hook"), Clip("cta"); last = int((Bo - HOLD) * FPS) - 1

    def at(i):
        t = i / FPS
        if t < A:
            fr = hook_frame(hook, t, A)
            if t > A - XF: fr = xfade(fr, screen_frame(0), (t - (A - XF)) / XF)
        elif t < A + CH:
            fr = screen_frame(t - A)
        else:
            tb = t - A - CH
            fr = avatar_frame(cta.at(min(int(tb * FPS), last)), tb, Bo, CTA_SUB, CTA_PL, T_PUSH_CTA)
            if tb < XF: fr = xfade(screen_frame(CH), fr, tb / XF)
        return fr

    if peek:
        for i in range(int(max(peek) * FPS) + 1):
            fr = at(i)
            for s in peek:
                if int(s * FPS) == i: fr.save(WORK / f"peek_{s}.png")
        return
    sfx = [("sfx-pop.mp3", T_PUSH, 0.25), ("sfx-pop.mp3", A + T_REVIEW, 0.16), ("sfx-pop.mp3", A + T_OPTIONS, 0.16),
           ("sfx-click.mp3", A + T_TAP, 0.25), ("sfx-pop.mp3", A + T_DONE, 0.16)]
    ins = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-t", f"{TOT:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
           "-i", str(WORK / "hook.mp4"), "-i", str(WORK / "cta.mp4")]
    oms = int((A + CH) * 1000)
    fl = ["[2:a]loudnorm=I=-14:TP=-1.5,aformat=sample_rates=48000:channel_layouts=stereo[v0]",
          f"[3:a]loudnorm=I=-14:TP=-1.5,aformat=sample_rates=48000:channel_layouts=stereo,adelay={oms}|{oms}[v1]"]
    labs = ["[v0]", "[v1]"]
    for j, (f, t, v) in enumerate(sfx):
        ins += ["-i", str(K / "11_MOTION" / f)]; ms = int(t * 1000)
        fl.append(f"[{j + 4}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={v},adelay={ms}|{ms}[s{j}]")
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
    WORK.mkdir(parents=True, exist_ok=True)
    if sys.argv[1:2] == ["screen"]:
        for s in sys.argv[2:]: screen_frame(float(s)).save(WORK / f"screen_{s}.png")
    elif sys.argv[1:2] == ["peek"]:
        main([float(s) for s in sys.argv[2:]])
    else:
        main()
