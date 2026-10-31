"""Ролик «Документы — это к Харви» (сценарий R019).

Чат Telegram с ботом «Харви»: пересылаю сообщения клиентов — бот отвечает, кто клиент и этап,
и присылает договор / акт / допсоглашение файлом.

Основа экрана — скриншот Telegram (iPhone 1170×2532, тёмная тема). Со скриншота берутся только
строка состояния и поле ввода; переписка стёрта, фон восстановлен градиентом обоев,
шапка («Харви · бот», аватар — голова HARVI с лендинга harvi-site) нарисована заново.
Скриншот не публикуется (в нём чужая переписка): work/r019/tg-chat.png.

Аватар HeyGen (Avatar 6, id dd0cd08dd0f347c2896f7fde8cddd01e, 5,16 с, сгенерирован Иваном) разрезан:
    work/r019/hook.mp4 — 0–2,12 с «Так, документы — это к Харви»
    work/r019/cta.mp4  — с 2,20 с «Напишите «ДОГОВОР» в комментариях — покажу, как это устроено»
Вступление — как R018: поверх аватара сыплются сообщения клиентов (портреты av_*.jpg из R018).

    python r019_harvi.py empty         # -> work/r019/tg-empty.png (пустой чат «Харви»)
    python r019_harvi.py peek 1 5 9    # кадры work/r019/peek_<t>.png
    python r019_harvi.py               # -> example-r019-harvi/final.mp4, cover.jpg
"""
import os, sys, pathlib, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

K = pathlib.Path(__file__).resolve().parents[2]
WORK = pathlib.Path(os.environ.get("R019_WORK", K / "work" / "r019"))
SHOT = WORK / "tg-chat.png"
HARVI_HEAD = pathlib.Path(os.environ.get("HARVI_HEAD", K.parent / "harvi-site" / "public" / "harvi" / "head-live.png"))
SW, SH = 1170, 2532
BOT_Y0 = 2262                    # поле ввода и полоска «домой» — со скриншота
GLASS = (32, 40, 50)             # «стекло» кнопок шапки
TXT = (255, 255, 255); MUTED = (140, 150, 162)
NAME = "Харви"


@functools.lru_cache(None)
def shot(): return Image.open(SHOT).convert("RGB")


@functools.lru_cache(None)
def ui(size, bold=True):
    return ImageFont.truetype("seguisb.ttf" if bold else "segoeui.ttf", size)


@functools.lru_cache(None)
def wallpaper():
    """Градиент обоев: квадратичная поверхность по чистым полоскам фона слева и справа."""
    a = np.asarray(shot(), np.float32)
    ys = np.arange(330, 2240, 6)
    pts = [(x, y) for y in ys for x in range(4, 28, 6)] + [(x, y) for y in ys for x in range(1062, 1166, 8)]
    P = np.array(pts, np.float32); x, y = P[:, 0] / SW, P[:, 1] / SH
    A = np.stack([np.ones_like(x), x, y, x * y, x * x, y * y], 1)
    cols = a[P[:, 1].astype(int), P[:, 0].astype(int)]
    coef = np.linalg.lstsq(A, cols, rcond=None)[0]
    yy, xx = np.mgrid[0:SH, 0:SW].astype(np.float32); xx /= SW; yy /= SH
    G = np.stack([np.ones_like(xx), xx, yy, xx * yy, xx * xx, yy * yy], -1) @ coef
    G += np.random.default_rng(7).normal(0, 0.8, G.shape)          # без полос на градиенте
    return Image.fromarray(np.clip(G, 0, 255).astype(np.uint8))


def light_mask(im, lo=90, hi=200):
    """Маска светлых элементов (цифры, значки) — чтобы перенести их без фона под ними."""
    L = np.asarray(im.convert("L"), np.float32)
    return Image.fromarray((np.clip((L - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8))


def rr_mask(w, h, r, k=4):
    m = Image.new("L", (w * k, h * k), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, w * k - 1, h * k - 1], r * k, fill=255)
    return m.resize((w, h), Image.LANCZOS)


def glass(im, box, r):
    x0, y0, x1, y1 = box; w, h = x1 - x0, y1 - y0
    layer = Image.new("RGBA", (w, h), GLASS + (235,)); d = ImageDraw.Draw(layer)
    d.rounded_rectangle([0, 0, w - 1, h - 1], r, outline=(255, 255, 255, 22), width=2)
    layer.putalpha(Image.fromarray(np.minimum(np.asarray(rr_mask(w, h, r)), np.asarray(layer.getchannel("A")))))
    im.alpha_composite(layer, (x0, y0))


@functools.lru_cache(None)
def harvi_avatar(d=128):
    k = 4; im = Image.new("RGBA", (d * k, d * k)); dr = ImageDraw.Draw(im)
    dr.ellipse([0, 0, d * k - 1, d * k - 1], fill=(23, 105, 255, 255))
    head = Image.open(HARVI_HEAD).convert("RGBA")
    head = head.crop(head.getbbox()); s = d * k * 0.92 / max(head.size)
    head = head.resize((int(head.width * s), int(head.height * s)), Image.LANCZOS)
    im.alpha_composite(head, ((d * k - head.width) // 2, int(d * k * 0.12)))
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).ellipse([0, 0, d * k - 1, d * k - 1], fill=255)
    im.putalpha(Image.fromarray(np.minimum(np.asarray(m), np.asarray(im.getchannel("A")))))
    return im.resize((d, d), Image.LANCZOS)


@functools.lru_cache(None)
def empty_chat(subtitle="бот"):
    im = wallpaper().convert("RGBA"); s = shot()
    # верх: лёгкое затемнение под строкой состояния, как у Telegram
    fade = np.clip(np.linspace(1, 0, 330), 0, 1) ** 1.6 * 120
    top = Image.new("RGBA", (SW, 330), (12, 16, 22, 0)); top.putalpha(Image.fromarray(np.repeat(fade[:, None], SW, 1).astype(np.uint8)))
    im.alpha_composite(top)
    # строка состояния: часы и значки — светлые пиксели, плашка TELEGRAM — целиком
    for box, lo in [((110, 40, 280, 115), 90), ((840, 40, 1100, 115), 45)]:   # у значка сети тусклые деления
        c = s.crop(box); im.paste(c, box[:2], light_mask(c, lo))
    tg = (444, 13, 724, 84); c = s.crop(tg); im.paste(c, tg[:2], rr_mask(tg[2] - tg[0], tg[3] - tg[1], 35))
    # шапка: «назад», имя бота, аватар
    glass(im, (48, 172, 224, 304), 66); d = ImageDraw.Draw(im)
    d.line([(118, 210), (96, 238), (118, 266)], fill=TXT, width=7, joint="curve")
    d.ellipse([136, 214, 184, 262], fill=TXT); d.text((160, 238), "3", font=ui(32), fill=(20, 26, 34), anchor="mm")
    nw = max(ui(46).getlength(NAME), ui(32, False).getlength(subtitle)) + 130
    x0 = int(SW / 2 - nw / 2); glass(im, (x0, 172, int(x0 + nw), 304), 66)
    d.text((SW / 2, 216), NAME, font=ui(46), fill=TXT, anchor="mm")
    d.text((SW / 2, 268), subtitle, font=ui(32, False), fill=MUTED, anchor="mm")
    im.alpha_composite(harvi_avatar(), (996, 174))
    # низ: со скриншота только кнопки, поле ввода и полоска «домой» (узор обоев под ними не берём)
    for box, r in [((22, 2286, 145, 2408), 61), ((160, 2286, 1009, 2408), 61), ((1023, 2286, 1148, 2408), 62),
                   ((372, 2484, 798, 2512), 14)]:
        c = s.crop(box); im.paste(c, box[:2], rr_mask(box[2] - box[0], box[3] - box[1], r))
    return im


# ═════════════════════════════════════════════════════════════════════════════
# Анимация
import subprocess
import r014_avito as R
from r014_avito import (W, H, FPS, GRAPH, OFF, BLUE, clamp, prog, eout, ss, eback, lerp,
                        put, plates, background, Clip, avatar_frame, xfade)
import r018_kp as P                       # поток сообщений над аватаром — как в R018

OUT = pathlib.Path(__file__).resolve().parent / "example-r019-harvi"
R.CLIP_DIR = WORK; P.WORK = WORK

# ── вступление ───────────────────────────────────────────────────────────────
P.PRE = 0.0
P.HOOK_SUB = [[("Так,", .33), ("документы", .54)], [("это", 1.22), ("к", 1.38), ("Харви.", 1.54)]]
P.MSGS = [
    (0.05, "Ольга", "Мы согласны, присылайте договор", "olga"),          # только имена — без компаний
    (0.40, "Анна", "Первый этап приняли, пришлите акт", "anna"),
    (0.75, "Ольга", "И допсоглашение на второй этап", "olga"),
    (1.05, "Игорь", "Договор на нас готов?", "igor"),
    (1.35, "Марина", "Пришлите договор и счёт", "marina"),
]
P.COUNT = [(0.05, 2), (0.40, 4), (0.75, 6), (1.05, 8), (1.35, 11)]

# ── финал ────────────────────────────────────────────────────────────────────
CTA_SUB = [[("Напишите", .17), ("«ДОГОВОР»", .50)], [("в", .86), ("комментариях —", .98)],
           [("покажу,", 1.58), ("как", 1.94), ("это", 2.14), ("устроено", 2.34)]]
CTA_PL = [(.17, 99, [("Напишите в комментариях", OFF, GRAPH), ("«ДОГОВОР»", BLUE, OFF)], [.17, .50])]
T_PUSH_CTA = 0.50; HOLD = 0.45
COVER_T = 1.0
COVER = [("Документы —", OFF, GRAPH), ("это к Харви", BLUE, OFF)]

# ── экран Telegram: таймлайн от начала экранного куска ───────────────────────
OUTB = (45, 92, 140); INB = (33, 45, 60); OUTMUTED = (165, 200, 235); INMUTED = (128, 145, 162)
FILEB = (64, 145, 235)
CHAT = [  # (время, кто, переслано от, текст, файл (имя, размер) | None); {…} — размыть (решение Ивана)
    (0.55, "fwd", "{Ольга · ООО «Вектор»}", "Добрый день! Мы согласны, присылайте договор", None),
    (1.85, "bot", None, "Это {ООО «Вектор»}, сайт под ключ, этап 1 — 120 000 ₽. Договор по вашему шаблону:",
     ("Договор №27 — {Вектор}.docx", "38 КБ")),
    (2.95, "fwd", "{Анна · ИП Соколова}", "Первый этап приняли, пришлите акт", None),
    (3.25, "fwd", "{Ольга · ООО «Вектор»}", "И допсоглашение на второй этап, пожалуйста", None),
    (4.25, "bot", None, "{ИП Соколова}, этап 1 — акт:", ("Акт №14 — {Соколова}.docx", "22 КБ")),
    (4.95, "bot", None, "{ООО «Вектор»}, этап 2 — 80 000 ₽, 20 рабочих дней. Допсоглашение:",
     ("Допсоглашение №1 — {Вектор}.docx", "25 КБ")),
]
BLUR = 11                         # радиус размытия данных клиента (координаты экрана 1170 px)


def plain(s): return s.replace("{", "").replace("}", "")


def secret_runs(s):
    """Отрезки [a, b) скрытого текста в строке без скобок."""
    out, i, a = [], 0, None
    for ch in s:
        if ch == "{": a = i
        elif ch == "}": out.append((a, i))
        else: i += 1
    return out


def blur_box(im, box, r=BLUR):
    box = tuple(int(round(v)) for v in box); c = im.crop(box).filter(ImageFilter.GaussianBlur(r))
    im.paste(c, box[:2])


def rich_text(im, d, x, y, s, f, fill, anchor="lm", pad=6):
    """Строка с размытыми кусками {…}."""
    p = plain(s); d.text((x, y), p, font=f, fill=fill, anchor=anchor)
    asc, desc = f.getmetrics(); top = y - (asc + desc) / 2 if anchor[1] == "m" else y
    for a, b in secret_runs(s):
        x0 = x + f.getlength(p[:a]); x1 = x + f.getlength(p[:b])
        blur_box(im, (x0 - pad, top - pad, x1 + pad, top + asc + desc + pad))
WRITING = [(1.0, 1.8), (3.55, 4.2), (4.45, 4.9)]
T_VIEW = 5.95                     # открывается готовый договор
T_SCROLL = (6.4, 8.7)
CH = 9.0
CAPS = [(0.25, 2.75, [("Пересылаю", OFF, GRAPH), ("сообщение клиента", OFF, GRAPH)]),
        (2.85, 5.7, [("Харви сам понимает,", OFF, GRAPH), ("кто клиент и какой этап", BLUE, OFF)]),
        (5.8, CH - 0.2, [("Документ — по вашему", OFF, GRAPH), ("шаблону", BLUE, OFF)])]

# карточка с экраном в кадре 1080×1920
CX0, CX1, CY0, CY1 = 110, 970, 600, 1600
CW, CHH = CX1 - CX0, CY1 - CY0
SC = CW / SW; SHW = int(round(CHH / SC))
TOP_H = 330; MSG_Y0, MSG_Y1 = TOP_H, SHW - (SH - BOT_Y0)
BF = 44; LH = 58; PADX = 34; PADY = 22; TEXT_W = 740; RAD = 38; GAP = 16


def wrap(s, f, w):
    out, cur = [], ""
    for wd in s.split(" "):
        c = (cur + " " + wd).strip()
        if f.getlength(c.replace("{", "").replace("}", "")) <= w or not cur: cur = c
        else: out.append(cur); cur = wd
    out.append(cur)
    for i in range(len(out) - 1):                  # скрытый кусок перенесён — закрыть и открыть заново
        if out[i].count("{") > out[i].count("}"): out[i] += "}"; out[i + 1] = "{" + out[i + 1]
    return out


def doc_icon(d, cx, cy, r):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=FILEB)
    w, h, k = r * 0.62, r * 0.82, r * 0.24; x0, y0 = cx - w / 2, cy - h / 2
    d.polygon([(x0, y0), (x0 + w - k, y0), (x0 + w, y0 + k), (x0 + w, y0 + h), (x0, y0 + h)], fill=(255, 255, 255))
    d.polygon([(x0 + w - k, y0), (x0 + w - k, y0 + k), (x0 + w, y0 + k)], fill=(190, 215, 245))
    for j in range(3):
        yy = y0 + h * (0.42 + 0.17 * j); d.line([(x0 + w * 0.18, yy), (x0 + w * 0.82, yy)], fill=FILEB, width=max(2, int(r * 0.07)))


def checks(d, x, y, col):
    for dx in (0, 14):
        d.line([(x + dx, y), (x + dx + 9, y + 10), (x + dx + 26, y - 10)], fill=col, width=4, joint="curve")


@functools.lru_cache(None)
def bubble(k):
    _, who, fwd, text, file = CHAT[k]
    f = ui(BF, False); fb = ui(36); tf = ui(30, False)
    lines = wrap(text, f, TEXT_W)                    # скобки {…} держатся внутри слов, ширину считаем без них
    tw = max(f.getlength(plain(l)) for l in lines); head = fh = 0
    if fwd:
        head = 84; tw = max(tw, fb.getlength(plain(fwd)))
    if file:
        fh = 130; tw = max(tw, 122 + ui(40).getlength(plain(file[0])))
    tw = max(tw, f.getlength(plain(lines[-1])) + 110)            # место под время
    bw, bh = int(tw + 2 * PADX), int(head + len(lines) * LH + fh + 2 * PADY + 8)
    im = Image.new("RGBA", (SW, bh)); d = ImageDraw.Draw(im)
    x0 = SW - 24 - bw if who == "fwd" else 24
    d.rounded_rectangle([x0, 0, x0 + bw, bh], RAD, fill=(OUTB if who == "fwd" else INB) + (255,))
    mut = OUTMUTED if who == "fwd" else INMUTED
    y = PADY
    if fwd:
        d.text((x0 + PADX, y + 2), "Переслано от", font=ui(32, False), fill=mut); y += 40
        rich_text(im, d, x0 + PADX, y + 22, fwd, fb, mut); y += 44
    for l in lines:
        rich_text(im, d, x0 + PADX, y + LH / 2, l, f, TXT); y += LH
    if file:
        y += 12; r = 50; doc_icon(d, x0 + PADX + r, y + r + 4, r)
        rich_text(im, d, x0 + PADX + 2 * r + 22, y + 30, file[0], ui(40), TXT)
        d.text((x0 + PADX + 2 * r + 22, y + 80), file[1] + " · DOCX", font=ui(32, False), fill=INMUTED, anchor="lm")
    tm = "18:45"; tx = x0 + bw - PADX - tf.getlength(tm) - (44 if who == "fwd" else 0)
    d.text((tx, bh - PADY - 14), tm, font=tf, fill=mut, anchor="lm")
    if who == "fwd": checks(d, x0 + bw - PADX - 36, bh - PADY - 12, mut)
    return im


@functools.lru_cache(None)
def top_layer(sub):
    """Шапка поверх ленты: снизу растушёвана, чтобы сообщения уходили под неё."""
    im = empty_chat(sub).crop((0, 0, SW, TOP_H + 30)).copy()
    a = np.full((TOP_H + 30, SW), 255, np.float32); a[250:] = np.linspace(255, 0, TOP_H + 30 - 250)[:, None]
    im.putalpha(Image.fromarray(a.astype(np.uint8))); return im


@functools.lru_cache(None)
def bottom_layer():
    im = empty_chat().crop((0, BOT_Y0 - 30, SW, SH)).copy()
    a = np.full((im.height, SW), 255, np.float32); a[:30] = np.linspace(0, 255, 30)[:, None]
    im.putalpha(Image.fromarray(a.astype(np.uint8))); return im


@functools.lru_cache(None)
def chat_bg(): return empty_chat().crop((0, 0, SW, SHW)).copy()


# ── договор в просмотрщике (вымышленный клиент и реквизиты) ──────────────────
HL = (255, 233, 130)
DOC = [
    ("T", "ДОГОВОР № 27"), ("C", "на оказание услуг по разработке сайта"), ("R", None),
    ("P", [("ООО «Вектор»", 1), ("(ИНН", 0), ("7700000000),", 1), ("именуемое в дальнейшем «Заказчик», в лице генерального директора", 0),
           ("Ивановой Ольги Сергеевны,", 1), ("действующей на основании Устава, с одной стороны, и Исполнитель, с другой стороны, заключили настоящий договор о нижеследующем.", 0)]),
    ("H", "1. ПРЕДМЕТ ДОГОВОРА"),
    ("P", [("1.1. Исполнитель обязуется выполнить работы:", 0), ("разработка сайта под ключ, этап 1,", 1),
           ("а Заказчик — принять и оплатить их.", 0)]),
    ("P", [("1.2. Состав работ и требования приведены в техническом задании (Приложение № 1).", 0)]),
    ("H", "2. СТОИМОСТЬ И ПОРЯДОК ОПЛАТЫ"),
    ("P", [("2.1. Стоимость работ составляет", 0), ("120 000 (сто двадцать тысяч) рублей,", 1), ("НДС не облагается.", 0)]),
    ("P", [("2.2. Оплата: 50 % предоплата в течение 3 банковских дней после подписания договора, 50 % — после подписания акта.", 0)]),
    ("H", "3. СРОКИ"),
    ("P", [("3.1. Срок выполнения работ —", 0), ("30 рабочих дней", 1), ("с даты поступления предоплаты.", 0)]),
    ("H", "4. ПОРЯДОК СДАЧИ И ПРИЁМКИ"),
    ("P", [("4.1. По завершении работ Исполнитель направляет Заказчику акт. Заказчик в течение 5 рабочих дней подписывает акт или направляет мотивированный отказ.", 0)]),
    ("H", "5. РЕКВИЗИТЫ СТОРОН"),
    ("P", [("Заказчик:", 0), ("ООО «Вектор», ИНН 7700000000, ОГРН 1027700000000, г. Москва, ул. Примерная, д. 1", 1)]),
]


@functools.lru_cache(None)
def doc_page():
    PW, M, L = 1060, 80, 50
    f = ImageFont.truetype("times.ttf", 34); fb = ImageFont.truetype("timesbd.ttf", 36)
    im = Image.new("RGBA", (PW, 2600), (255, 255, 255, 255)); d = ImageDraw.Draw(im); y = 90; sp = f.getlength(" ")
    for kind, body in DOC:
        if kind == "T": d.text((PW / 2, y), body, font=ImageFont.truetype("timesbd.ttf", 44), fill=(0, 0, 0), anchor="mt"); y += 60
        elif kind == "C": d.text((PW / 2, y), body, font=f, fill=(0, 0, 0), anchor="mt"); y += 80
        elif kind == "H": y += 18; d.text((PW / 2, y), body, font=fb, fill=(0, 0, 0), anchor="mt"); y += 62
        elif kind == "R":
            d.text((M, y), "г. Москва", font=f, fill=(0, 0, 0)); s = "31 октября 2026 г."; w = f.getlength(s)
            d.rectangle([PW - M - w - 4, y - 2, PW - M + 4, y + 40], fill=HL); d.text((PW - M - w, y), s, font=f, fill=(0, 0, 0))
            blur_box(im, (PW - M - w - 8, y - 6, PW - M + 8, y + 44), 9); y += L + 20
        else:
            x = M + 40
            for txt, hl in body:
                for w in txt.split(" "):
                    ww = f.getlength(w)
                    if x + ww > PW - M: x = M; y += L
                    if hl: d.rectangle([x - 4, y - 2, x + ww + 4, y + 40], fill=HL)
                    d.text((x, y), w, font=f, fill=(0, 0, 0))
                    if hl: blur_box(im, (x - 8, y - 6, x + ww + 8, y + 44), 9)   # данные клиента размыты (решение Ивана)
                    x += ww + sp
            y += L + 14
    return im.crop((0, 0, PW, y + 60))


def viewer(t):
    """Просмотрщик iOS: светлая шторка, название файла, страница листается."""
    im = Image.new("RGBA", (SW, SHW), (242, 242, 247, 255)); d = ImageDraw.Draw(im)
    pg = doc_page(); off = ss(prog(t, T_SCROLL[0], T_SCROLL[1] - T_SCROLL[0])) * max(0, pg.height - (SHW - 300))
    sh = Image.new("RGBA", (pg.width + 40, pg.height + 40)); ImageDraw.Draw(sh).rectangle([20, 24, pg.width + 20, pg.height + 24], fill=(0, 0, 0, 40))
    put(im, sh.filter(ImageFilter.GaussianBlur(10)), (SW - pg.width) / 2 - 20, 240 - off - 20)
    put(im, pg, (SW - pg.width) / 2, 240 - off)
    d.rectangle([0, 0, SW, 200], fill=(249, 249, 251, 255)); d.line([(0, 200), (SW, 200)], fill=(210, 210, 215), width=2)
    d.text((52, 120), "Готово", font=ui(42), fill=(10, 132, 255), anchor="lm")
    rich_text(im, d, SW / 2 - ui(38).getlength("Договор №27 — Вектор.docx") / 2, 120, "Договор №27 — {Вектор}.docx", ui(38), (0, 0, 0))
    return im


def screen(t):
    sub = "бот"
    for a, b in WRITING:
        if a <= t < b: sub = "печатает" + "." * (int((t - a) * 4) % 4)
    im = chat_bg().copy(); items, y = [], 30
    for k, c in enumerate(CHAT):
        if t < c[0]: break
        b = bubble(k); extra = 12 if k + 1 < len(CHAT) and CHAT[k + 1][1] != c[1] else 0
        items.append((b, y, prog(t, c[0], 0.32))); y += lerp(0, b.height + GAP + extra, eout(prog(t, c[0], 0.28)))
    shift = max(0, y - GAP - (MSG_Y1 - MSG_Y0 - 40))
    for spr, yy, p in items:
        if p >= 1: put(im, spr, 0, MSG_Y0 + yy - shift)
        else:
            s = lerp(0.9, 1.0, eback(p)); sp = spr.resize((int(spr.width * s), max(1, int(spr.height * s))), Image.BICUBIC)
            put(im, sp, (SW - sp.width) / 2, MSG_Y0 + yy - shift + (spr.height - sp.height) / 2 + 24 * (1 - eout(p)), eout(p * 1.6))
    im.alpha_composite(top_layer(sub), (0, 0))
    im.alpha_composite(bottom_layer(), (0, SHW - bottom_layer().height))
    vp = eout(prog(t, T_VIEW, 0.45))
    if vp > 0:
        v = viewer(t); v.putalpha(rr_mask(SW, SHW, 40)); put(im, v, 0, 110 + (SHW - 110) * (1 - vp))
    return im


@functools.lru_cache(None)
def card_mask(): return rr_mask(CW, CHH, 44)


@functools.lru_cache(None)
def card_shadow():
    im = Image.new("RGBA", (CW + 160, CHH + 160)); ImageDraw.Draw(im).rounded_rectangle([80, 100, 80 + CW, 100 + CHH], 44, fill=(0, 0, 0, 170))
    return im.filter(ImageFilter.GaussianBlur(30))


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
            fr = P.hook_frame(hook, t, A)
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
    sfx = [("sfx-pop.mp3", m[0], 0.22) for m in P.MSGS]
    sfx += [("sfx-pop.mp3", A + c[0], 0.16) for c in CHAT] + [("sfx-click.mp3", A + T_VIEW, 0.22)]
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
    if sys.argv[1:2] == ["empty"]:
        empty_chat().convert("RGB").save(WORK / "tg-empty.png"); print(WORK / "tg-empty.png")
    elif sys.argv[1:2] == ["peek"]:
        main([float(s) for s in sys.argv[2:]])
    else:
        main()
