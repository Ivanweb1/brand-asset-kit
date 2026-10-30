"""Ролик «Спасение для всех, кто делает презентации» (сценарий R017).

Аватар HeyGen (хук) → экран Claude: печатаю задачу, прикладываю рефы, отправляю →
готовая презентация «ВСЕКУПОНЫ» листается → аватар (призыв «ПРЕЗА»).
Интерфейс Claude собран по скриншоту приложения: иконки, плейсхолдер, нижняя строка
и маскот — кропы со скриншота (×2); набранный текст, рефы и кнопка отправки рисуются кодом.
Боковая панель скриншота (список сессий, аккаунт) в кадр не попадает.

Исходники (не публикуются) — work/r017/:
    intro.mp4, outro.mp4   — одна и та же запись HeyGen (Avatar 6), id 800b35fe5ed7407ba4998e5faeb51f33
    claude-app.png         — скриншот приложения Claude 1919×1030
    ref1.png ref2.png ref3.jpg — рефы (логотип, сайт, купон) из coupon-prototype
    slide01…slide13.png    — слайды vsekupony-deck-v5.pdf

    python r017_presentation.py              # -> example-r017-presentation/final.mp4, cover.jpg
    python r017_presentation.py peek 1 4 8   # кадры work/r017/peek_<t>.png
"""
import os, sys, pathlib, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r014_avito as R
from r014_avito import (W, H, FPS, GRAPH, OFF, BLUE, SS, K, clamp, prog, eout, ss, eback, lerp,
                        put, plates, font, down, background, Clip, avatar_frame, xfade, camera)

WORK = pathlib.Path(os.environ.get("R017_WORK", K / "work" / "r017"))
OUT = pathlib.Path(__file__).resolve().parent / "example-r017-presentation"
R.CLIP_DIR = WORK

# ── запись аватара (тайминги слов — faster-whisper по work/r017/intro.mp4) ────
INTRO_MAX = 2.95                     # «Спасение для всех, кто делает презентации»
OUTRO_START = 3.2                    # «Напишите «ПРЕЗА» в комментариях — пришлю промпт»
HOLD = 0.5                           # последний кадр после «промпт»
INTRO_SUB = [[("Спасение", .32), ("для", .80), ("всех,", .98)],
             [("кто", 1.64), ("делает", 1.76), ("презентации", 2.08)]]
OUTRO_SUB = [[("Напишите", 3.32), ("«ПРЕЗА»", 3.72)],
             [("в", 4.08), ("комментариях —", 4.16)],
             [("пришлю", 5.16), ("промпт", 5.46)]]
OUTRO_PL = [(3.32, 99, [("Напишите в комментариях", OFF, GRAPH), ("«ПРЕЗА»", BLUE, OFF)], [3.32, 3.72])]
T_PUSH_CTA = 3.72
COVER_T = 0.12
COVER = [("Спасение для всех,", OFF, GRAPH), ("кто делает", OFF, GRAPH), ("презентации", BLUE, OFF)]

# ── экран Claude: таймлайн от начала экранного куска ─────────────────────────
PROMPT = ("Сделай презентацию для предпринимателей о сервисе ВСЕКУПОНЫ: "
          "13 слайдов по структуре ниже. Стиль бери из референсов")
T_CARD = 0.0                         # карточка приложения выезжает снизу
T_TYPE = (0.55, 2.75)                # печать задачи
CUR_PLUS = (2.95, 3.35); T_CLICK_PLUS = 3.4
T_REFS = [3.6, 3.8, 4.0]
CUR_SEND = (4.15, 4.5); T_SEND = 4.55
T_VIEW = 4.95                        # вместо окна чата — готовая презентация
SLIDES = [1, 3, 5, 8, 13]; T_SLIDE = 0.65; TOTAL_SLIDES = 13
CH = T_VIEW + 0.1 + len(SLIDES) * T_SLIDE
CAPS = [(0.3, 2.85, [("Пишу задачу", OFF, GRAPH)]),
        (2.95, 4.55, [("Прикладываю рефы", OFF, GRAPH), ("и отправляю", BLUE, OFF)]),
        (4.75, CH - 0.25, [("Claude собрал", OFF, GRAPH), ("презентацию", BLUE, OFF)])]

# ── карточка приложения (координаты кадра; кропы скриншота ×2) ───────────────
CX0, CX1, CY0, CY1 = 110, 970, 600, 1560
CW, CHH = CX1 - CX0, CY1 - CY0
BX0, BX1 = 20, CW - 20                # поле ввода внутри карточки
BBOT = CHH - 84                       # низ поля ввода
LINE = (221, 221, 221); TXT = (31, 31, 31); SEND = (217, 119, 87)
TF = 31; LH = 46; TPAD = 28; ROW = 84; TILE = 124
BLUR_TEXT = False                     # размыть набранный промпт (R018)


@functools.lru_cache(None)
def app(): return Image.open(WORK / "claude-app.png").convert("RGB")


@functools.lru_cache(None)
def crop(box, k=2, nearest=False):
    im = app().crop(box)
    return im.resize((im.width * k, im.height * k), Image.NEAREST if nearest else Image.LANCZOS).convert("RGBA")


PLUS = (745, 960, 765, 981); MIC = (1468, 958, 1489, 982); HOLDER = (775, 958, 1000, 983)
BAR_L = (745, 1002, 952, 1024); BAR_R = (1300, 1002, 1493, 1024)
TITLE = (328, 8, 414, 28); MASCOT = (1231, 417, 1271, 448)


@functools.lru_cache(None)
def ui_font(size): return ImageFont.truetype("segoeui.ttf", size * SS)


def wrap(s, f, width):
    lines, cur = [], ""
    for wd in s.split(" "):
        cand = (cur + " " + wd).strip()
        if f.getlength(cand) <= width * SS: cur = cand
        else: lines.append(cur); cur = wd
    return lines + [cur] if cur else lines


@functools.lru_cache(None)
def tile(k):
    p = [WORK / "ref1.png", WORK / "ref2.png", WORK / "ref3.jpg"][k]
    im = Image.open(p).convert("RGB"); s = min(im.size)
    im = im.crop(((im.width - s) // 2, (im.height - s) // 2, (im.width + s) // 2, (im.height + s) // 2))
    if k == 0: im = Image.open(p).convert("RGBA")   # логотип целиком на белом
    if k == 0:
        bg = Image.new("RGB", (max(im.size),) * 2, (255, 255, 255)); bg.paste(im, ((bg.width - im.width) // 2, (bg.height - im.height) // 2), im); im = bg
    im = im.resize((TILE * SS, TILE * SS), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, im.width - 1, im.height - 1], 18 * SS, fill=255)
    im.putalpha(m); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, im.width - 1, im.height - 1], 18 * SS, outline=LINE + (255,), width=2 * SS)
    return down(im)


@functools.lru_cache(None)
def send_btn(pressed=False):
    s = 60 * SS; im = Image.new("RGBA", (s, s)); d = ImageDraw.Draw(im)
    c = tuple(int(v * 0.85) for v in SEND) if pressed else SEND
    d.rounded_rectangle([0, 0, s - 1, s - 1], 16 * SS, fill=c + (255,))
    cx, cy = s / 2, s / 2; a = 15 * SS; w = 5 * SS
    d.line([(cx, cy + a), (cx, cy - a)], fill=(255, 255, 255), width=w)
    d.line([(cx - a * 0.8, cy - a * 0.15), (cx, cy - a), (cx + a * 0.8, cy - a * 0.15)], fill=(255, 255, 255), width=w, joint="curve")
    return down(im)


@functools.lru_cache(None)
def cursor():
    s = 4; pts = [(0, 0), (0, 34), (9, 26), (15, 40), (21, 37), (15, 24), (26, 24)]
    im = Image.new("RGBA", (34 * s, 46 * s)); d = ImageDraw.Draw(im)
    pp = [((x + 3) * s, (y + 2) * s) for x, y in pts]
    d.polygon(pp, fill=(255, 255, 255, 255)); d.line(pp + [pp[0]], fill=(255, 255, 255, 255), width=5 * s)
    d.polygon(pp, fill=(20, 20, 20, 255))
    return im.resize((34, 46), Image.LANCZOS)


def composer(t):
    """Поле ввода по состоянию на момент t; возвращает (картинка, y-верх в карточке, точки + и отправки)."""
    n = 0 if t < T_TYPE[0] else int(len(PROMPT) * clamp((t - T_TYPE[0]) / (T_TYPE[1] - T_TYPE[0])))
    typed = PROMPT[:n]; refs = sum(t >= a for a in T_REFS)
    f = ui_font(TF); bw = BX1 - BX0
    if not typed and not refs:   # пустое поле — как на скриншоте
        h = 92; im = Image.new("RGBA", (bw * SS, h * SS)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, bw * SS - 1, h * SS - 1], 24 * SS, fill=(255, 255, 255, 255), outline=LINE + (255,), width=2 * SS)
        im = down(im); pl, mic, ho = crop(PLUS), crop(MIC), crop(HOLDER)
        im.alpha_composite(pl, (24, (h - pl.height) // 2)); im.alpha_composite(ho, (66, (h - ho.height) // 2))
        im.alpha_composite(mic, (bw - 24 - mic.width, (h - mic.height) // 2))
        if int(t * 2.2) % 2 == 0:
            ImageDraw.Draw(im).rectangle([64, h / 2 - 17, 66, h / 2 + 17], fill=TXT)
        return im, BBOT - h, (24 + 20, BBOT - h / 2), None
    lines = wrap(typed, f, bw - 2 * TPAD) if typed else []
    th = (TILE + 18) if refs else 0
    h = TPAD - 6 + th + max(1, len(lines)) * LH + ROW
    im = Image.new("RGBA", (bw * SS, h * SS)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, bw * SS - 1, h * SS - 1], 24 * SS, fill=(255, 255, 255, 255), outline=LINE + (255,), width=2 * SS)
    y = (TPAD - 6) * SS + th * SS
    txt = Image.new("RGBA", im.size); td = ImageDraw.Draw(txt)
    for k, ln in enumerate(lines):
        td.text((TPAD * SS, y + k * LH * SS), ln, font=f, fill=TXT + (255,))
    if BLUR_TEXT:   # промпт виден как набор, но не читается (его выдают по кодовому слову)
        txt = txt.filter(ImageFilter.GaussianBlur(11 * SS))
    im.alpha_composite(txt)
    if lines and t < T_SEND and int(t * 2.2) % 2 == 0:   # курсор ввода
        x = TPAD * SS + f.getlength(lines[-1]) + 4 * SS; yy = y + (len(lines) - 1) * LH * SS
        d.rectangle([x, yy + 8 * SS, x + 3 * SS, yy + 44 * SS], fill=TXT + (255,))
    im = down(im)
    for k in range(refs):   # рефы появляются с лёгким отскоком
        p = eback(prog(t, T_REFS[k], 0.3)); tl = tile(k)
        sz = max(1, int(TILE * lerp(0.6, 1.0, p))); sp = tl.resize((sz, sz), Image.LANCZOS)
        put(im, sp, TPAD - 6 + k * (TILE + 14) + (TILE - sz) / 2, TPAD - 10 + (TILE - sz) / 2, clamp(p * 1.4))
    pl = crop(PLUS); im.alpha_composite(pl, (24, h - ROW // 2 - pl.height // 2))
    sb = send_btn(T_SEND <= t < T_SEND + 0.15); sx = bw - 18 - sb.width; sy = h - ROW // 2 - sb.height // 2
    im.alpha_composite(sb, (sx, sy))
    return im, BBOT - h, (24 + 20, BBOT - ROW / 2), (sx + sb.width / 2, BBOT - ROW / 2)


@functools.lru_cache(None)
def slide(k):
    im = Image.open(WORK / f"slide{k:02d}.png").convert("RGB")
    sw = CW - 40; im = im.resize((sw, int(im.height * sw / im.width)), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", (im.width * 3, im.height * 3), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, m.width - 1, m.height - 1], 16 * 3, fill=255)
    im.putalpha(m.resize(im.size, Image.LANCZOS)); return im


def viewer(card, t):
    tv = t - T_VIEW - 0.1; i = int(clamp(tv / T_SLIDE, 0, len(SLIDES) - 1)) if tv > 0 else 0
    sh = slide(SLIDES[0]).height; y0 = (CHH - sh) // 2 - 10
    d = ImageDraw.Draw(card)
    d.rounded_rectangle([18, y0 - 2, CW - 18, y0 + sh + 2], 18, outline=LINE)
    if tv > 0 and i > 0:
        p = eout(prog(tv, i * T_SLIDE, 0.28))
        put(card, slide(SLIDES[i - 1]), 20 - 80 * p, y0, 1 - p)
        put(card, slide(SLIDES[i]), 20 + 120 * (1 - p), y0, p)
    else:
        put(card, slide(SLIDES[i]), 20, y0)
    lab = f"{SLIDES[i]} / {TOTAL_SLIDES}"; f = ui_font(26)
    im = Image.new("RGBA", (300 * SS, 50 * SS)); ImageDraw.Draw(im).text((150 * SS, 25 * SS), lab, font=f, fill=(120, 120, 120, 255), anchor="mm")
    im = down(im); card.alpha_composite(im, ((CW - im.width) // 2, y0 + sh + 26))


@functools.lru_cache(None)
def card_mask():
    m = Image.new("L", (CW * 4, CHH * 4), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, CW * 4 - 1, CHH * 4 - 1], 36 * 4, fill=255)
    return m.resize((CW, CHH), Image.LANCZOS)


@functools.lru_cache(None)
def card_shadow():
    im = Image.new("RGBA", (CW + 160, CHH + 160)); ImageDraw.Draw(im).rounded_rectangle([80, 100, 80 + CW, 100 + CHH], 36, fill=(0, 0, 0, 170))
    return im.filter(ImageFilter.GaussianBlur(30))


def card(t):
    c = Image.new("RGBA", (CW, CHH), (255, 255, 255, 255))
    c.alpha_composite(crop(TITLE), (28, 26))
    view = prog(t, T_VIEW, 0.35)
    if view < 1:   # окно приложения: маскот и поле ввода
        layer = Image.new("RGBA", (CW, CHH))
        ms = crop(MASCOT, 4, nearest=True); layer.alpha_composite(ms, ((CW - ms.width) // 2, 300))
        comp, cy, plus_pt, send_pt = composer(t)
        lift = eout(prog(t, T_SEND + 0.05, 0.35))   # отправленное уходит вверх
        put(layer, comp, BX0, cy - 260 * lift, 1 - lift)
        if lift > 0:
            e, _, _, _ = composer(0); put(layer, e, BX0, BBOT - e.height, lift)
        bl, br = crop(BAR_L), crop(BAR_R)
        layer.alpha_composite(bl, (BX0 + 6, BBOT + 22)); layer.alpha_composite(br, (BX1 - 6 - br.width, BBOT + 22))
        # курсор мыши: к «+», клик, к кнопке отправки, клик
        if CUR_PLUS[0] <= t < T_SEND + 0.3:
            start = (CW * 0.62, CHH * 0.55)
            if t < CUR_SEND[0]:
                p = ss(prog(t, *(CUR_PLUS[0], CUR_PLUS[1] - CUR_PLUS[0]))); a, b = start, plus_pt
            else:
                p = ss(prog(t, CUR_SEND[0], CUR_SEND[1] - CUR_SEND[0])); a = plus_pt; b = send_pt or plus_pt
            x, y = lerp(a[0], b[0], p), lerp(a[1], b[1], p)
            for tc in (T_CLICK_PLUS, T_SEND):   # круг клика
                q = prog(t, tc, 0.3)
                if 0 < q < 1:
                    r = 14 + 26 * eout(q); ImageDraw.Draw(layer).ellipse([x - r, y - r, x + r, y + r], outline=BLUE + (int(200 * (1 - q)),), width=4)
            put(layer, cursor(), x - 4, y - 2, clamp(prog(t, CUR_PLUS[0], 0.15)) * (1 - prog(t, T_SEND + 0.15, 0.15)))
        put(c, layer, 0, 0, 1 - view)
    if view > 0:
        v = Image.new("RGBA", (CW, CHH)); viewer(v, t); put(c, v, 0, 30 * (1 - eout(view)), view)
    c.putalpha(Image.fromarray(np.minimum(np.asarray(c.getchannel("A")), np.asarray(card_mask()))))
    ImageDraw.Draw(c).rounded_rectangle([0, 0, CW - 1, CHH - 1], 36, outline=(255, 255, 255, 40), width=2)
    return c


def frame(t, cover=False):
    fr = background().copy()
    wp = eout(prog(t, T_CARD, 0.5)); y = CY0 + 520 * (1 - wp)
    put(fr, card_shadow(), CX0 - 80, y - 100, wp); put(fr, card(t), CX0, y, wp)
    for a, b, rows in CAPS:
        if a <= t < b + 0.3:
            o = ss(prog(t, b, 0.25))
            plates(fr, rows, 60, 356, lambda k: clamp(prog(t, a + 0.1 * k, 0.35) - o))
    return fr.convert("RGB")


def shift(lst, d):
    if isinstance(lst[0][0], tuple): return [[(w, ts - d) for w, ts in ln] for ln in lst]
    return [(a - d, b - d, rows, [x - d for x in ts]) for a, b, rows, ts in lst]


def make_cover():
    src = Clip("intro").at(int(COVER_T * FPS)); z = 1.4
    x0 = clamp(R.FACE[0] - 540 / z, 0, W - W / z); y0 = clamp(R.FACE[1] - 1190 / z, 0, H - H / z)
    fr = src.transform((W, H), Image.AFFINE, (1 / z, 0, x0, 0, 1 / z, y0), Image.BICUBIC).convert("RGBA")
    plates(fr, COVER, 84, 500, lambda k: 1.0)
    fr.convert("RGB").save(OUT / "cover.jpg", quality=95)


def main(peek=None):
    OUT.mkdir(exist_ok=True)
    A = INTRO_MAX; Bo = 6.0 - OUTRO_START + HOLD; TOT = A + CH + Bo
    osub, opl = shift(OUTRO_SUB, OUTRO_START), shift(OUTRO_PL, OUTRO_START)
    intro, outro = Clip("intro"), Clip("outro")
    XF = R.XF

    def at(i):
        t = i / FPS
        if t < A:
            fr = avatar_frame(intro.at(i), t, A, INTRO_SUB, [])
            if t > A - XF: fr = xfade(fr, frame(0), (t - (A - XF)) / XF)
        elif t < A + CH:
            fr = frame(t - A)
        else:
            tb = t - A - CH
            fr = avatar_frame(outro.at(int(round((tb + OUTRO_START) * FPS))), tb, Bo, osub, opl, T_PUSH_CTA - OUTRO_START)
            if tb < XF: fr = xfade(frame(CH), fr, tb / XF)
        return fr

    if peek:
        for i in range(int(max(peek) * FPS) + 1):
            fr = at(i)
            for s in peek:
                if int(s * FPS) == i: fr.save(WORK / f"peek_{s}.png")
        return
    sfx = [("sfx-click.mp3", A + T_CLICK_PLUS, 0.25), ("sfx-click.mp3", A + T_SEND, 0.25)]
    sfx += [("sfx-pop.mp3", A + ta, 0.12) for ta in T_REFS]
    sfx += [("sfx-pop.mp3", A + T_VIEW + 0.1 + k * T_SLIDE, 0.1) for k in range(1, len(SLIDES))]
    ins = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-t", f"{TOT:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
           "-i", str(WORK / "intro.mp4"), "-i", str(WORK / "outro.mp4")]
    oms = int((A + CH) * 1000)
    fl = [f"[2:a]atrim=0:{A:.3f},loudnorm=I=-14:TP=-1.5,aformat=sample_rates=48000:channel_layouts=stereo,afade=t=out:st={A - 0.08:.3f}:d=0.08[v0]",
          f"[3:a]atrim=start={OUTRO_START},asetpts=PTS-STARTPTS,afade=t=in:d=0.03,loudnorm=I=-14:TP=-1.5,aformat=sample_rates=48000:channel_layouts=stereo,adelay={oms}|{oms}[v1]"]
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
    cover = OUT / "cover.jpg"
    for i in range(int(round(TOT * FPS))):
        fr = Image.open(cover).convert("RGB") if i == 0 else at(i)
        p.stdin.write(np.ascontiguousarray(np.asarray(fr.convert("RGB")), np.uint8).tobytes())
    p.stdin.close(); p.wait(); print("done", OUT / "final.mp4", f"{TOT:.2f} s")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "peek":
        main([float(s) for s in sys.argv[2:]])
    else:
        main()
