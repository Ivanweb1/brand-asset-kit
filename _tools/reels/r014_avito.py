"""Ролик «ИИ-агент отвечает на Авито, пока вы спите» (сценарий R014).

Без речи: заставка-хук → чат Авито в 23:40, клиент спрашивает про посуточный дом,
ИИ-агент сразу отвечает и бронирует → уведомление хозяину → финальная надпись.
Переписка рисуется кодом поверх скриншота чата Авито (тёмная тема, iPhone 1170×2532):
со скриншота берутся только строка состояния, шапка, поле ввода, галочки, эмодзи 🤝
и аватар клиента; имя продавца, фото объявления и старая переписка заменены.

Скриншот не публикуется (в нём чужая переписка): лежит в work/r014/avito-chat.png
(или путь в $R014_SHOT).

    python r014_avito.py           # -> example-r014-avito/final.mp4, cover.png
"""
import os, pathlib, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, DUR = 1080, 1920, 30, 16.0
K = pathlib.Path(__file__).resolve().parents[2]
OUT = pathlib.Path(__file__).resolve().parent / "example-r014-avito"
SHOT = pathlib.Path(os.environ.get("R014_SHOT", K / "work" / "r014" / "avito-chat.png"))
GRAPH = (17, 19, 21); OFF = (245, 244, 240); BLUE = (23, 105, 255); LINE = (44, 48, 53)
SS = 2

# ── экран Авито (координаты скриншота 1170 px по ширине) ─────────────────────
SW = 1170
CBG = (20, 20, 19); CTXT = (227, 227, 227); CMUTED = (135, 135, 135)
CBLUE = (0, 44, 86); CGRAY = (46, 42, 34); CPINK = (238, 59, 120); CSEND = (0, 153, 255)
TOP_H = 310                    # строка состояния + шапка
BOT_Y0, BOT_Y1 = 2228, 2440    # поле ввода (без полоски «домой»)
WIN_X, WIN_Y, WIN_W = 95, 596, 890
SC = WIN_W / SW
SH = int(round((1640 - 8 - WIN_Y) / SC))   # высота экрана: окно кончается над подписью Reels
MSG_Y0, MSG_Y1 = TOP_H, SH - (BOT_Y1 - BOT_Y0)

SELLER = "Сергей"
DATE = "четверг, 29 октября"
CHAT = [  # (кто, текст, время появления, время в чате)
    ("me", "Добрый вечер! Дом свободен с 7 по 9 ноября? Нас будет четверо", 5.1, "23:40"),
    ("ai", "Добрый вечер! Да, 7–9 ноября свободно. Две ночи — 12 000 ₽. Бронирую на вас?", 7.0, "23:40"),
    ("me", "Да, бронируем!", 10.0, "23:41"),
    ("ai", "Готово, даты за вами 🤝 Инструкцию по заселению пришлю накануне", 11.3, "23:41"),
]
TYPE = [(3.2, 4.95, 0), (9.3, 9.85, 2)]     # клиент набирает сообщение k: начало, конец
WRITING = [(5.7, 6.95), (10.4, 11.25)]       # «печатает…» в шапке
T_MIN41 = 9.0                                # часы 23:40 → 23:41

# ── надписи ──────────────────────────────────────────────────────────────────
INTRO = [("Так ИИ-агент", OFF, GRAPH), ("отвечает вашим", OFF, GRAPH),
         ("клиентам на Авито", OFF, GRAPH), ("пока вы спите", BLUE, OFF)]
T_INTRO_OUT = 2.25
USE_PLATE_INTRO = False      # заставка-плашка заменена вступлением аватара
CAPS = [  # (начало, конец, строки)
    (2.9, 5.55, [("23:40. Пишет клиент", OFF, GRAPH)]),
    (5.65, 9.15, [("Отвечает ИИ-агент —", OFF, GRAPH), ("сразу, даже ночью", BLUE, OFF)]),
    (9.25, 12.1, [("Клиент бронирует,", OFF, GRAPH), ("агент подтверждает", BLUE, OFF)]),
    (12.3, 14.2, [("Утром хозяин видит", OFF, GRAPH), ("готовую бронь", BLUE, OFF)]),
]
T_WIN = 2.35                                 # окно чата выезжает снизу
T_NOTE_IN, T_NOTE_OUT = 12.2, 14.15          # уведомление хозяину
NOTE = ("ИИ-агент", "Новая бронь с Авито", "7–9 ноября · 4 гостя · 12 000 ₽")


def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, a, d): return clamp((t - a) / d)
def eout(x): x = clamp(x); return 1 - (1 - x) ** 3
def ss(x): x = clamp(x); return x * x * (3 - 2 * x)
def eback(x):
    x = clamp(x); c1 = 1.4; c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2
def lerp(a, b, p): return a + (b - a) * p
def mix(c1, c2, p): return tuple(int(round(lerp(a, b, p))) for a, b in zip(c1, c2))


@functools.lru_cache(None)
def font(weight, size):
    return ImageFont.truetype(str(K / "00_BRAND_GUIDE" / "fonts" / f"Manrope-{weight}.ttf"), size)


@functools.lru_cache(None)
def ios_font(size):   # цифры часов в строке состояния — ближе к SF, чем Manrope
    return ImageFont.truetype("seguisb.ttf", size)


def down(im): return im.resize((im.width // SS, im.height // SS), Image.LANCZOS)


def put(fr, spr, x, y, a=1.0):
    if a <= 0.003: return
    if a < 1:
        spr = spr.copy(); spr.putalpha(spr.getchannel("A").point(lambda v: int(v * a)))
    fr.alpha_composite(spr, (int(round(x)), int(round(y))))


# ── фирменные плашки (как в r015_card.py) ────────────────────────────────────
@functools.lru_cache(None)
def plate(text, size, fg, bg, padx=30, pady=16, r=18):
    f = font("ExtraBold", size * SS); bb = f.getbbox(text); asc, desc = f.getmetrics()
    th = asc + desc; w = bb[2] - bb[0] + 2 * padx * SS; h = int(th * 0.86) + 2 * pady * SS
    im = Image.new("RGBA", (w, h)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], r * SS, fill=bg + (255,))
    d.text((padx * SS - bb[0], pady * SS - int(th * 0.07)), text, font=f, fill=fg + (255,))
    return down(im)


def plates(fr, rows, size, y, a_fn):
    for k, (s, bg, fg) in enumerate(rows):
        sp = plate(s, size, fg, bg); p = a_fn(k)
        put(fr, sp, (W - sp.width) / 2, y + 30 * (1 - eout(p)), eout(p)); y += sp.height + 12


@functools.lru_cache(None)
def background():
    im = Image.new("RGB", (W, H), GRAPH); d = ImageDraw.Draw(im)
    grid = mix(GRAPH, LINE, 0.55)
    for x in range(0, W, 72): d.line([(x, 0), (x, H)], fill=grid, width=1)
    for y in range(0, H, 72): d.line([(0, y), (W, y)], fill=grid, width=1)
    yy, xx = np.mgrid[0:H, 0:W]
    v = np.clip(((xx - W / 2) / (W * 0.75)) ** 2 + ((yy - H / 2) / (H * 0.62)) ** 2, 0, 1)[..., None]
    arr = np.array(im, np.float32) * (1 - 0.6 * v) + np.array(GRAPH, np.float32) * 0.6 * v
    return Image.fromarray(arr.astype(np.uint8)).convert("RGBA")


# ── детали со скриншота ──────────────────────────────────────────────────────
@functools.lru_cache(None)
def shot():
    return Image.open(SHOT).convert("RGB")


@functools.lru_cache(None)
def top_bar(writing_phase=-1, minute="23:40"):
    """Строка состояния и шапка. writing_phase ≥ 0 — «печатает» с бегущими точками."""
    im = shot().crop((0, 0, SW, TOP_H)).convert("RGBA"); d = ImageDraw.Draw(im)
    d.rectangle([110, 40, 290, 115], fill=CBG)                       # часы
    d.text((127, 50), minute, font=ios_font(52), fill=(255, 255, 255))
    th = shot().crop((173, 177, 326, 286)).filter(ImageFilter.GaussianBlur(9))  # фото объявления — размыто
    m = Image.new("L", th.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, th.width - 1, th.height - 1], 14, fill=255)
    d.rectangle([160, 160, 340, 295], fill=CBG); im.paste(th, (173, 177), m)
    d.ellipse([160, 163, 224, 227], fill=CPINK, outline=CBG, width=4)  # бейдж с буквой продавца
    f = font("Medium", 36); d.text((192, 195), SELLER[0], font=f, fill=(255, 255, 255), anchor="mm")
    d.rectangle([350, 175, 1160, 300], fill=CBG)                     # имя и подзаголовок
    d.text((361, 186), SELLER, font=font("Bold", 44), fill=CTXT)
    if writing_phase < 0:
        d.text((361, 244), "2-к. дом, 52 м² · 6 000 ₽ за сутки", font=font("Medium", 34), fill=(170, 170, 170))
    else:
        d.text((361, 244), "печатает" + "." * writing_phase, font=font("Medium", 34), fill=CSEND)
    return im


@functools.lru_cache(None)
def bottom_bar(typed="", caret=True):
    im = shot().crop((0, BOT_Y0, SW, BOT_Y1)).convert("RGBA"); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, SW, 30], fill=CBG)                            # обрезок чужого пузыря сверху
    fy = 2263 - BOT_Y0; fx0, fx1 = 157, 785
    if typed:
        d.rounded_rectangle([fx0, fy, fx1, fy + 129], 32, fill=(38, 38, 38))
        f = font("Medium", 40); w = d.textlength(typed, font=f); room = fx1 - fx0 - 80
        layer = Image.new("RGBA", (fx1 - fx0 - 48, 129)); ld = ImageDraw.Draw(layer)
        tx = min(0, room - w); ld.text((tx, 64), typed, font=f, fill=CTXT, anchor="lm")
        if caret: ld.rectangle([tx + w + 4, 40, tx + w + 7, 90], fill=CSEND)
        im.alpha_composite(layer, (fx0 + 44, fy))
        d.rectangle([1030, 70, 1150, 200], fill=CBG)                 # микрофон → кнопка «отправить»
        cx, cy, r = 1085, 2328 - BOT_Y0, 44
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=CSEND)
        d.line([(cx, cy + 20), (cx, cy - 20)], fill=(255, 255, 255), width=7)
        d.line([(cx - 17, cy - 3), (cx, cy - 20), (cx + 17, cy - 3)], fill=(255, 255, 255), width=7, joint="curve")
    return im


@functools.lru_cache(None)
def checks(): return shot().crop((186, 486, 236, 518)).convert("RGBA")
@functools.lru_cache(None)
def emoji(): return shot().crop((620, 1322, 682, 1368)).convert("RGBA")


@functools.lru_cache(None)
def avatar_me():
    a = shot().crop((1041, 393, 1129, 481)).convert("RGBA")
    m = Image.new("L", (a.width * 4, a.height * 4), 0); ImageDraw.Draw(m).ellipse([0, 0, m.width - 1, m.height - 1], fill=255)
    a.putalpha(m.resize(a.size, Image.LANCZOS)); return a


@functools.lru_cache(None)
def avatar_ai():
    im = Image.new("RGBA", (88 * 4, 88 * 4)); d = ImageDraw.Draw(im)
    d.ellipse([0, 0, im.width - 1, im.height - 1], fill=CPINK)
    d.text((im.width / 2, im.height / 2 + 4), SELLER[0], font=font("Medium", 48 * 4), fill=(255, 255, 255), anchor="mm")
    return im.resize((88, 88), Image.LANCZOS)


# ── пузыри ───────────────────────────────────────────────────────────────────
CHIP_H = 66; BF = 42; LH = 64; PADX = 36; PADY = 26; TEXT_W = 600; RAD = 30; GAP = 64


def wrap(s):
    f = font("Medium", BF); lines, cur = [], ""
    for wd in s.split(" "):
        cand = (cur + " " + wd).strip()
        if font_w(cand, f) <= TEXT_W: cur = cand
        else: lines.append(cur); cur = wd
    return lines + [cur]


def font_w(s, f):
    return sum(emoji().width + 4 if p == "🤝" else f.getlength(p) for p in _parts(s))


def _parts(s):
    out, buf = [], ""
    for ch in s:
        if ch == "🤝": out += [buf, ch]; buf = ""
        else: buf += ch
    return out + [buf]


@functools.lru_cache(None)
def bubble(who, s, tm):
    """Пузырь с аватаром и временем; возвращает картинку на всю ширину экрана."""
    f = font("Medium", BF); lines = wrap(s)
    tw = max(font_w(l, f) for l in lines); bw = int(tw + 2 * PADX); bh = len(lines) * LH + 2 * PADY
    im = Image.new("RGBA", (SW, bh)); d = ImageDraw.Draw(im)
    x0 = 1019 - bw if who == "me" else 151
    d.rounded_rectangle([x0, 0, x0 + bw, bh], RAD, fill=(CBLUE if who == "me" else CGRAY) + (255,))
    for i, l in enumerate(lines):
        x = x0 + PADX; y = PADY + i * LH + LH / 2
        for p in _parts(l):
            if p == "🤝": im.alpha_composite(emoji(), (int(x + 2), int(y - emoji().height / 2 - 2))); x += emoji().width + 4
            elif p: d.text((x, y), p, font=f, fill=CTXT + (255,), anchor="lm"); x += f.getlength(p)
    tf = font("Medium", 32); ty = bh - 58
    if who == "me":
        im.alpha_composite(avatar_me(), (1041, 6))
        tx = x0 - 18 - tf.getlength(tm); d.text((tx, ty), tm, font=tf, fill=CMUTED + (255,), anchor="lm")
        im.alpha_composite(checks(), (int(tx - 58), int(ty - 17)))
    else:
        im.alpha_composite(avatar_ai(), (40, 12))
        d.text((x0 + bw + 14, ty), tm, font=tf, fill=CMUTED + (255,), anchor="lm")
    # подпись над пузырём: кто пишет — клиент или ИИ-агент
    lab, bg, fg = ("Клиент", OFF, GRAPH) if who == "me" else ("ИИ-агент", BLUE, OFF)
    cf = font("ExtraBold", 34); cw = int(cf.getlength(lab)) + 40
    out = Image.new("RGBA", (SW, bh + CHIP_H)); out.alpha_composite(im, (0, CHIP_H))
    cd = ImageDraw.Draw(out); cx = x0 + bw - cw if who == "me" else x0
    cd.rounded_rectangle([cx, 0, cx + cw, CHIP_H - 14], 14, fill=bg + (255,))
    cd.text((cx + cw / 2, (CHIP_H - 14) / 2 + 1), lab, font=cf, fill=fg + (255,), anchor="mm")
    return out


@functools.lru_cache(None)
def top_fade(h=110):
    a = (np.clip(np.linspace(1.8, 0, h), 0, 1) ** 1.5 * 255).astype(np.uint8)
    im = Image.new("RGBA", (SW, h), CBG + (0,)); im.putalpha(Image.fromarray(np.repeat(a[:, None], SW, 1)))
    return im


@functools.lru_cache(None)
def date_sep():
    f = font("Bold", 38); w = int(f.getlength(DATE)) + 4
    im = Image.new("RGBA", (w, 56)); ImageDraw.Draw(im).text((0, 28), DATE, font=f, fill=CTXT + (255,), anchor="lm")
    return im


def screen(t):
    im = Image.new("RGBA", (SW, SH), CBG + (255,))
    # лента сообщений: сверху вниз, при переполнении плавно уезжает вверх
    y = 40; items = [(date_sep(), (SW - date_sep().width) / 2, y, 1.0, 0)]; y += date_sep().height + 44
    for who, s, ta, tm in CHAT:
        if t < ta: break
        b = bubble(who, s, tm); p = prog(t, ta, 0.32)
        items.append((b, 0, y, p, b.height)); y += lerp(0, b.height + GAP, eout(prog(t, ta, 0.28)))
    room = MSG_Y1 - MSG_Y0 - 30
    shift = max(0, y - GAP - room)
    for spr, x, yy, p, h in items:
        if p >= 1 or h == 0:
            put(im, spr, x, MSG_Y0 + yy - shift)
        else:  # появление: снизу вверх с лёгким пружинящим масштабом
            s = lerp(0.9, 1.0, eback(p)); sw_, sh_ = int(spr.width * s), max(1, int(spr.height * s))
            sp = spr.resize((sw_, sh_), Image.BICUBIC)
            put(im, sp, (SW - sw_) / 2, MSG_Y0 + yy - shift + (h - sh_) / 2 + 24 * (1 - eout(p)), eout(p * 1.6))
    # поле ввода: клиент набирает текст
    typed = ""
    for a, b, k in TYPE:
        if a <= t < b + 0.15:
            s = CHAT[k][1]; typed = s[:int(len(s) * clamp((t - a) / (b - a)))]
    caret = int(t * 2.4) % 2 == 0 or bool(typed)
    im.alpha_composite(bottom_bar(typed, caret), (0, MSG_Y1))
    ph = -1
    for a, b in WRITING:
        if a <= t < b: ph = int((t - a) * 4) % 4
    im.alpha_composite(top_fade(), (0, MSG_Y0))   # уезжающие сообщения мягко уходят под шапку
    im.alpha_composite(top_bar(ph, "23:41" if t >= T_MIN41 else "23:40"), (0, 0))
    return im


@functools.lru_cache(None)
def window_mask():
    m = Image.new("L", (WIN_W * 4, int(SH * SC) * 4), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, m.width - 1, m.height - 1], 44 * 4, fill=255)
    return m.resize((WIN_W, int(SH * SC)), Image.LANCZOS)


@functools.lru_cache(None)
def window_shadow():
    wh = int(SH * SC); im = Image.new("RGBA", (WIN_W + 160, wh + 160)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([80, 100, 80 + WIN_W, 100 + wh], 44, fill=(0, 0, 0, 170))
    return im.filter(ImageFilter.GaussianBlur(30))


def window(t):
    sc = screen(t).resize((WIN_W, int(SH * SC)), Image.LANCZOS); sc.putalpha(window_mask())
    d = ImageDraw.Draw(sc); d.rounded_rectangle([0, 0, sc.width - 1, sc.height - 1], 44, outline=(255, 255, 255, 28), width=2)
    return sc


@functools.lru_cache(None)
def notification():
    w, h = 880, 176; im = Image.new("RGBA", (w * SS, h * SS)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], 40 * SS, fill=(44, 44, 47, 250), outline=(255, 255, 255, 30), width=2 * SS)
    ix, iy, isz = 30, 30, 80
    d.rounded_rectangle([ix * SS, iy * SS, (ix + isz) * SS, (iy + isz) * SS], 20 * SS, fill=BLUE + (255,))
    d.text(((ix + isz / 2) * SS, (iy + isz / 2 + 2) * SS), "ИИ", font=font("ExtraBold", 34 * SS), fill=OFF + (255,), anchor="mm")
    tx = (ix + isz + 24) * SS
    d.text((tx, 40 * SS), NOTE[0].upper(), font=font("SemiBold", 22 * SS), fill=(160, 160, 165, 255), anchor="lm")
    d.text(((w - 32) * SS, 40 * SS), "сейчас", font=font("Medium", 22 * SS), fill=(160, 160, 165, 255), anchor="rm")
    d.text((tx, 84 * SS), NOTE[1], font=font("Bold", 32 * SS), fill=(250, 250, 250, 255), anchor="lm")
    d.text((tx, 128 * SS), NOTE[2], font=font("Medium", 30 * SS), fill=(225, 225, 228, 255), anchor="lm")
    return down(im)


def frame(t, cover=False):
    fr = background().copy()
    # окно чата
    wp = 1.0 if cover else eout(prog(t, T_WIN, 0.6))
    if wp > 0:
        y = WIN_Y + 520 * (1 - wp)
        put(fr, window_shadow(), WIN_X - 80, y - 100, wp)
        w = window(DUR if cover else t)
        if cover:  # обложка: готовая переписка приглушена под заголовком
            dim = Image.new("RGBA", w.size, GRAPH + (175,)); dim.putalpha(Image.eval(w.getchannel("A"), lambda v: v * 175 // 255))
            w = w.copy(); w.alpha_composite(dim)
        put(fr, w, WIN_X, y, wp)
    # уведомление хозяину выезжает сверху на окно
    if not cover and T_NOTE_IN - 0.1 < t < T_NOTE_OUT + 0.5:
        p = eback(prog(t, T_NOTE_IN, 0.45)) - ss(prog(t, T_NOTE_OUT, 0.35)) * 1.2
        n = notification(); put(fr, n, (W - n.width) / 2, WIN_Y + 24 - 260 * (1 - p), clamp(p * 1.5))
    # надписи
    if cover or (USE_PLATE_INTRO and t < T_INTRO_OUT + 0.4):
        out = 0 if cover else ss(prog(t, T_INTRO_OUT, 0.35))
        rows = INTRO; hh = sum(plate(s, 80, fg, bg).height + 12 for s, bg, fg in rows) - 12
        y0 = (H - hh) / 2 - 40 - 260 * out
        plates(fr, rows, 80, y0, lambda k: 1.0 if cover else clamp(prog(t, 0.06 + 0.12 * k, 0.4) - out))
    else:
        for a, b, rows in CAPS:
            if a <= t < b + 0.3:
                o = ss(prog(t, b, 0.25))
                plates(fr, rows, 60, 356, lambda k: clamp(prog(t, a + 0.1 * k, 0.35) - o))
    return np.asarray(fr.convert("RGB"))


# ── аватар HeyGen: вступление и финал (work/r014/intro.mp4, outro.mp4) ─────────
CLIP_DIR = SHOT.parent
CHAT_A, CHAT_B = 2.25, 14.55        # кусок таймлайна чата между аватарами
FACE, FACE_AT = (590, 950), (540, 870)   # лицо в исходнике → на ~870 px (RULES §2)
XF = 0.15                           # мягкая склейка
SUB_Y, SUB_W = 1526, 560
# слова субтитров со временем начала (расшифровка _tools/transcribe), строки — по смыслу
INTRO_SUB = [[("Клиент", .34), ("написал", .59), ("на", .99), ("Авито", 1.15)],
             [("в", 1.92), ("23:40.", 1.93)],
             [("ИИ-агент", 3.41)],
             [("проконсультировал", 4.2), ("его", 5.05)],
             [("и", 5.46), ("поставил", 5.55), ("бронь.", 5.91)]]
OUTRO_START = 3.42                  # финал — только призыв: «ИИ-агент работает 24/7» вырезано (решение Ивана)
OUTRO_SUB = [[("Напишите", 3.48), ("в", 3.85), ("директ", 3.97)],
             [("«ЗАЯВКА» —", 4.56), ("покажу,", 5.09)],
             [("как", 5.53), ("настроить", 5.69), ("такой", 6.17), ("у", 6.41), ("вас.", 6.53)]]
INTRO_PL = []                       # во вступлении только субтитры: плашки повторяли их (решение Ивана)
OUTRO_PL = [(3.48, 99, [("Напишите в директ", OFF, GRAPH), ("«ЗАЯВКА»", BLUE, OFF)], [3.48, 4.56])]
T_PUSH_CTA = 4.56                   # наезд на «ЗАЯВКА» (RULES §2: без статичных отрезков)


def shift(lst, d):
    """Сдвигает времена слов/плашек финала к началу обрезанного куска."""
    if isinstance(lst[0][0], tuple): return [[(w, ts - d) for w, ts in ln] for ln in lst]
    return [(a - d, b - d, rows, [x - d for x in ts]) for a, b, rows, ts in lst]


def clip_len(name):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                          str(CLIP_DIR / f"{name}.mp4")], capture_output=True, text=True).stdout
    return float(out)


class Clip:
    """Кадры исходника по порядку, без загрузки всего видео в память."""
    def __init__(self, name):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(CLIP_DIR / f"{name}.mp4"), "-vf", f"fps={FPS},scale={W}:{H}",
                                   "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
        self.i, self.last = -1, None

    def at(self, k):
        while self.i < k:
            b = self.p.stdout.read(W * H * 3)
            if len(b) < W * H * 3: break
            self.last = Image.frombuffer("RGB", (W, H), b); self.i += 1
        return self.last


def camera(im, z):
    x0 = clamp(FACE[0] - FACE_AT[0] / z, 0, W - W / z); y0 = clamp(FACE[1] - FACE_AT[1] / z, 0, H - H / z)
    return im.transform((W, H), Image.AFFINE, (1 / z, 0, x0, 0, 1 / z, y0), Image.BICUBIC)


@functools.lru_cache(None)
def sub_shade():   # затемнение под субтитрами: от 1150 px до низа, до 70 % (RULES §6)
    a = np.clip((np.arange(H)[:, None] - 1150) / (H - 1150), 0, 1) ** 1.2 * 0.7
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); im.putalpha(Image.fromarray((np.repeat(a, W, 1) * 255).astype(np.uint8)))
    return im


def subtitles(fr, lines, t):
    cur = None
    for k, ln in enumerate(lines):
        if t >= ln[0][1] - 0.05: cur = k
    if cur is None: return
    ln = lines[cur]; f = font("Bold", 46 * SS); gap = f.getlength(" ")
    ws = [f.getlength(w) for w, _ in ln]; tw = sum(ws) + gap * (len(ln) - 1)
    im = Image.new("RGBA", (int(tw) + 8, 80 * SS)); d = ImageDraw.Draw(im); x = 0
    for (w, ts), ww in zip(ln, ws):   # сказанные слова белые, следующие светло-серые
        d.text((x, 0), w, font=f, fill=(OFF if t >= ts - 0.05 else (185, 185, 185)) + (255,)); x += ww + gap
    im = down(im)
    if im.width > SUB_W + 40: im = im.resize((SUB_W + 40, int(im.height * (SUB_W + 40) / im.width)), Image.LANCZOS)
    put(fr, im, (W - im.width) / 2, SUB_Y)


def avatar_frame(src, t, dur, subs, pls, push_at=None):
    z = 1.10 + 0.04 * (1 - eout(prog(t, 0, 0.7))) + 0.02 * ss(prog(t, 0.7, dur))   # отъезд в начале, медленный наезд
    if push_at is not None: z += 0.08 * eout(prog(t, push_at, 0.5))
    fr = camera(src, z).convert("RGBA"); fr.alpha_composite(sub_shade())
    for a, b, rows, ts in pls:
        if a - 0.05 <= t < b + 0.3:
            o = ss(prog(t, b, 0.25))
            plates(fr, rows, 66, 356, lambda k: clamp(prog(t, ts[k], 0.32) - o))
    subtitles(fr, subs, t)
    return fr.convert("RGB")


def xfade(a, b, p): return Image.blend(a, b, ss(p))


COVER_T = 1.0
COVER = [("Клиент написал", OFF, GRAPH), ("на Авито в 23:40", OFF, GRAPH), ("Ответил ИИ-агент", BLUE, OFF)]


def make_cover():
    """Обложка по RULES §9 (как cover.py, но без cairo): кадр ролика, зум 1,4, лицо на 1190 px,
    заголовок внутри центрального квадрата y 470…1450."""
    src = Clip("intro").at(int(COVER_T * FPS)); z = 1.4
    x0 = clamp(FACE[0] - 540 / z, 0, W - W / z); y0 = clamp(FACE[1] - 1190 / z, 0, H - H / z)
    fr = src.transform((W, H), Image.AFFINE, (1 / z, 0, x0, 0, 1 / z, y0), Image.BICUBIC).convert("RGBA")
    plates(fr, COVER, 84, 500, lambda k: 1.0)
    fr.convert("RGB").save(OUT / "cover.jpg", quality=95)


def main(peek=None):
    OUT.mkdir(exist_ok=True)
    A, Bo = min(clip_len("intro"), 6.35), clip_len("outro") - OUTRO_START
    osub, opl = shift(OUTRO_SUB, OUTRO_START), shift(OUTRO_PL, OUTRO_START)
    CH = CHAT_B - CHAT_A; TOT = A + CH + Bo
    intro, outro = Clip("intro"), Clip("outro")

    def at(i):
        t = i / FPS
        if t < A:
            fr = avatar_frame(intro.at(i), t, A, INTRO_SUB, INTRO_PL)
            if t > A - XF: fr = xfade(fr, Image.fromarray(frame(CHAT_A)), (t - (A - XF)) / XF)
        elif t < A + CH:
            fr = Image.fromarray(frame(CHAT_A + t - A))
        else:
            tb = t - A - CH
            fr = avatar_frame(outro.at(int(round((tb + OUTRO_START) * FPS))), tb, Bo, osub, opl, T_PUSH_CTA - OUTRO_START)
            if tb < XF: fr = xfade(Image.fromarray(frame(CHAT_B)), fr, tb / XF)
        return fr

    if peek:   # кадры для проверки: work/r014/peek_<t>.png
        for i in range(int(max(peek) * FPS) + 1):
            fr = at(i)
            for s in peek:
                if int(s * FPS) == i: fr.save(K / "work" / "r014" / f"peek_{s}.png")
        return
    sfx = ([("sfx-click.mp3" if who == "me" else "sfx-pop.mp3", A + ta - CHAT_A, 0.2 if who == "me" else 0.16) for who, _, ta, _ in CHAT]
           + [("sfx-pop.mp3", A + T_NOTE_IN - CHAT_A, 0.2)])
    ins = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-t", f"{TOT:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
           "-i", str(CLIP_DIR / "intro.mp4"), "-i", str(CLIP_DIR / "outro.mp4")]
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
    cover = OUT / "cover.jpg"   # обложка первым кадром
    for i in range(int(round(TOT * FPS))):
        fr = Image.open(cover).convert("RGB").resize((W, H)) if i == 0 and cover.exists() else at(i)
        p.stdin.write(np.ascontiguousarray(np.asarray(fr.convert("RGB")), np.uint8).tobytes())
    p.stdin.close(); p.wait(); print("done", OUT / "final.mp4", f"{TOT:.2f} s")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "peek":   # python r014_avito.py peek 1 5.5 8 …
        main([float(s) for s in sys.argv[2:]])
    else:
        main()
