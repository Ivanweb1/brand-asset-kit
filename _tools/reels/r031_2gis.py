"""Ролик «Claude + 2ГИС = деньги» (сценарий R031), ~9,5 с, без голоса и без автора.

Формула: [Claude] + [2ГИС] = уведомление «+ 40 000 ₽» → парсинг 2ГИС: карточки компаний листаются,
у кого нет сайта — метка «Нет сайта», счётчик растёт → список чатов: агент пишет компаниям (как R025) →
переписка с Дмитрием: цена, КП, «Куда платить?» → то же уведомление «+ 40 000 ₽» → конец.
Призыв — только в описании (правило R025). Сообщения агента выглядят обычными (правило R030).

Логотипы прислал Иван (work/r031/logo-*-src.png), приведены к одной плитке с одинаковым скруглением.
Экран 2ГИС нарисован: названия, адреса и телефоны размыты.

    python r031_2gis.py              # -> example-r031-2gis/final.mp4, cover.jpg
    python r031_2gis.py peek 0.5 2.5 # кадры work/r031/peek_<t>.png
"""
import os, sys, pathlib, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r019_harvi as T
import r025_sales as S
import payment_note
import r014_avito as R
from r014_avito import (W, H, FPS, GRAPH, OFF, BLUE, K, clamp, prog, eout, eback, lerp, ss, put, plates,
                        background, xfade, font)

WORK = pathlib.Path(os.environ.get("R031_WORK", K / "work" / "r031"))
OUT = pathlib.Path(__file__).resolve().parent / "example-r031-2gis"
AMOUNT = 40000

# ── телефон крупно, как в R030 ───────────────────────────────────────────────
T.CX0, T.CX1, T.CY0, T.CY1 = 50, 1030, 600, 1660
T.CW, T.CHH = T.CX1 - T.CX0, T.CY1 - T.CY0
T.SC = T.CW / T.SW; T.SHW = int(round(T.CHH / T.SC))
T.MSG_Y1 = T.SHW - (T.SH - T.BOT_Y0)


@functools.lru_cache(None)
def face(path, d=128):
    ph = Image.open(path).convert("RGB")
    s = ph.width * 0.62; ph = ph.crop(((ph.width - s) / 2, ph.height * 0.02, (ph.width + s) / 2, ph.height * 0.02 + s))
    ph = ph.resize((d, d), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", (d * 4, d * 4), 0); ImageDraw.Draw(m).ellipse([0, 0, d * 4 - 1, d * 4 - 1], fill=255)
    ph.putalpha(m.resize((d, d), Image.LANCZOS)); return ph


T.NAME = "Дмитрий"; T.harvi_avatar = lambda d=128: face(K / "work" / "r019" / "av_dmitry.jpg", d)
SUB = "в сети"
T.empty_chat(SUB); T.top_layer(SUB)


@functools.lru_cache(None)
def note():
    """Уведомление об оплате: картинка Ивана из R025 с суммой AMOUNT (payment_note.py)."""
    im = Image.open(payment_note.make(AMOUNT, WORK / "payment.png")).convert("RGBA"); w = 880
    im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    sh = Image.new("RGBA", (w + 80, im.height + 80)); ImageDraw.Draw(sh).rounded_rectangle([40, 50, 40 + w, 50 + im.height], 40, fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(18)); sh.alpha_composite(im, (40, 40)); return sh


# ── сцена 1: формула ─────────────────────────────────────────────────────────
F_LEN = 1.6
TILE = 300; TR = 0.23                                # плитка логотипа и радиус скругления (доля стороны)


@functools.lru_cache(None)
def logo(name):
    im = Image.open(WORK / f"logo-{name}-src.png").convert("RGBA").resize((TILE, TILE), Image.LANCZOS)
    m = T.rr_mask(TILE, TILE, int(TILE * TR))
    im.putalpha(Image.fromarray(np.minimum(np.asarray(im.getchannel("A")), np.asarray(m))))
    sh = Image.new("RGBA", (TILE + 80, TILE + 80)); ImageDraw.Draw(sh).rounded_rectangle([40, 52, 40 + TILE, 52 + TILE], int(TILE * TR), fill=(0, 0, 0, 160))
    sh = sh.filter(ImageFilter.GaussianBlur(20)); sh.alpha_composite(im, (40, 40)); return sh


@functools.lru_cache(None)
def sign(ch, size=150):
    f = font("ExtraBold", size); w = int(f.getlength(ch)) + 20
    im = Image.new("RGBA", (w, size + 40)); ImageDraw.Draw(im).text((w / 2, (size + 40) / 2), ch, font=f, fill=OFF, anchor="mm")
    return im


def pop(fr, spr, cx, cy, t, a):
    p = prog(t, a, 0.4)
    if p <= 0: return
    s = lerp(0.6, 1.0, eback(p)); sp = spr.resize((max(1, int(spr.width * s)), max(1, int(spr.height * s))), Image.BICUBIC)
    put(fr, sp, cx - sp.width / 2, cy - sp.height / 2, clamp(p * 2))


HOOK = [("Где брать клиентов", OFF, GRAPH), ("на сайты", BLUE, OFF)]


def formula_frame(t, caps=True, dy=0):
    fr = background().copy(); y1 = 840 + dy
    pop(fr, logo("claude"), 250, y1, t, 0.0)
    pop(fr, sign("+"), 540, y1 - 6, t, 0.22)
    pop(fr, logo("2gis"), 830, y1, t, 0.30)
    pop(fr, sign("="), 540, 1130 + dy, t, 0.60)
    if t >= 0.72:
        p = eback(prog(t, 0.72, 0.45)); n = note()
        put(fr, n, (W - n.width) / 2, 1230 + dy + 120 * (1 - p), clamp(p * 1.6))
    if caps: S.caps(fr, t, [(0.0, 99, HOOK)])
    return fr


# ── сцена 2: парсинг 2ГИС (рисованный экран, светлая тема) ────────────────────
P_LEN = 2.3
G_BG, G_CARD, G_TXT, G_MUT, G_GREEN = (240, 241, 243), (255, 255, 255), (30, 32, 36), (128, 134, 142), (26, 170, 32)
NAMES = ["{Автосервис Мотор}", "{Шиномонтаж 24}", "{Кузовной центр}", "{Автомойка Блеск}", "{СТО на Лесной}",
         "{Авто-Профи}", "{Ремонт АКПП}", "{Детейлинг Pro}", "{Шины-Диски}", "{Автоэлектрик}", "{Развал-схождение}",
         "{Тонировка Люкс}", "{Масло-Сервис}", "{Кузовной ремонт}"]
HAS_SITE = [1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1]
CH = 250; LY0 = 470
T_FILTER = 0.35                                      # загорается фильтр «Без сайта»


@functools.lru_cache(None)
def gcard(k, dim):
    im = Image.new("RGBA", (T.SW, CH), G_BG + (255,)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([28, 12, T.SW - 28, CH - 12], 30, fill=G_CARD)
    x = 70
    T.rich_text(im, d, x, 62, NAMES[k], T.ui(44), G_TXT)
    d.text((x, 112), "Автосервис · рейтинг 4," + str(5 + k % 4), font=T.ui(34, False), fill=G_MUT, anchor="lm")
    T.rich_text(im, d, x, 160, "{ул. Лесная, 12 · +7 916 123-45-67}", T.ui(34, False), G_MUT, r=9)
    if HAS_SITE[k]:
        T.rich_text(im, d, x, 206, "{www.site-avto.ru}", T.ui(34, False), (60, 130, 220), r=9)
    else:
        f = T.ui(32); w = f.getlength("Нет сайта") + 44
        d.rounded_rectangle([x, 182, x + w, 230], 24, fill=BLUE)
        d.text((x + w / 2, 206), "Нет сайта", font=f, fill=OFF, anchor="mm")
    if dim:                                                     # с сайтом — гаснет
        a = np.asarray(im).copy(); a[..., 3] = (a[..., 3] * 0.32).astype(np.uint8)
        bg = Image.new("RGBA", im.size, G_BG + (255,)); bg.alpha_composite(Image.fromarray(a)); im = bg
    return im


@functools.lru_cache(None)
def g_head():
    im = Image.new("RGBA", (T.SW, LY0), G_BG + (255,)); d = ImageDraw.Draw(im)
    sb = T.empty_chat(SUB).crop((0, 0, T.SW, 125)).convert("L")          # строка состояния — тёмная на светлом
    dark = Image.new("RGBA", (T.SW, 125), (20, 20, 22, 255)); im.paste(dark, (0, 0), sb.point(lambda v: 255 if v > 150 else 0))
    lg = Image.open(WORK / "logo-2gis-src.png").convert("RGBA").resize((92, 92), Image.LANCZOS); im.alpha_composite(lg, (50, 150))
    d.rounded_rectangle([166, 150, T.SW - 50, 242], 46, fill=(255, 255, 255))
    d.text((210, 196), "Автосервисы · Москва", font=T.ui(40, False), fill=G_TXT, anchor="lm")
    return im


def g_chips(im, t):
    d = ImageDraw.Draw(im); x = 50; on = t >= T_FILTER
    for txt, active in [("Открыто", False), ("Рейтинг 4+", False), ("Без сайта", on)]:
        f = T.ui(34); w = f.getlength(txt) + 56
        d.rounded_rectangle([x, 290, x + w, 360], 35, fill=BLUE if active else (255, 255, 255))
        d.text((x + w / 2, 325), txt, font=f, fill=OFF if active else G_TXT, anchor="mm"); x += w + 18
    n = int(148 * ss(prog(t, T_FILTER, P_LEN - T_FILTER - 0.2))) if on else 0
    d.text((T.SW - 50, 420), f"Без сайта: {n}", font=T.ui(38), fill=BLUE if on else G_MUT, anchor="rm")
    d.text((50, 420), "1 240 компаний", font=T.ui(34, False), fill=G_MUT, anchor="lm")


def g_screen(t):
    im = Image.new("RGBA", (T.SW, T.SHW), G_BG + (255,))
    off = 900 * ss(prog(t, 0.15, P_LEN)) + 260 * t           # список быстро листается
    on = t >= T_FILTER
    for k in range(len(NAMES)):
        y = LY0 + k * CH - off
        if y > T.SHW or y + CH < LY0 - CH: continue
        put(im, gcard(k, bool(HAS_SITE[k] and on)), 0, y)
    im.alpha_composite(g_head(), (0, 0)); g_chips(im, t)
    return im


def phone_frame(screen, t, cap_list):
    fr = background().copy()
    put(fr, T.card_shadow(), T.CX0 - 80, T.CY0 - 100); put(fr, S.card(screen), T.CX0, T.CY0)
    S.caps(fr, t, cap_list); return fr


P_CAPS = [(0.0, 99, [("Нашёл компании", OFF, GRAPH), ("без сайта", BLUE, OFF)])]
parse_frame = lambda t: phone_frame(g_screen(t), t, P_CAPS)

# ── сцена 3: агент пишет компаниям (список чатов из R025, короче) ─────────────
L_LEN = 1.4
S.T_ROWS = [0.05 + 0.2 * k for k in range(6)]
L_CAPS = [(0.0, 99, [("ИИ-агент пишет сам", BLUE, OFF)])]
list_frame = lambda t: phone_frame(S.list_screen(t), t, L_CAPS)

# ── сцена 4: переписка → оплата ──────────────────────────────────────────────
KP = ("file", "КП — сайт для {Авто-Профи}.pdf", "40 000 ₽ · PDF")
MSGS = [
    (-1.0, "out", "{Здравствуйте! Посмотрел вашу компанию на картах — сайта у вас пока нет.}\nДелаю такие сайты. Актуально?",
     ("img", 4), "18:21"),
    (0.25, "in", "Здравствуйте. А сколько стоит?", None, "18:30"),
    (0.70, "out", "Сайт-визитка — от 40 000 ₽. Пришлю КП с примерами?", None, "18:31"),
    (1.15, "in", "Да.", None, "18:33"),
    (1.45, "out", None, KP, "18:33"),
    (1.95, "in", "Подходит. Куда платить?", None, "18:40"),
    (2.35, "out", "{Ссылка на оплату:}\n{pay.example.ru/i/48213}", None, "18:40"),
]
T_NOTE = 2.8
C_LEN = T_NOTE + 1.5
C_CAPS = [(0.0, T_NOTE - 0.15, [("и продаёт", BLUE, OFF)]), (T_NOTE, 99, [("Клиент оплатил", BLUE, OFF)])]


@functools.lru_cache(None)
def bubble(k):
    _, who, text, att, tm = MSGS[k]
    f = T.ui(T.BF, False); tf = T.ui(30, False); out = who == "out"
    lines = []
    for para in (text.split("\n") if text else []): lines += T.wrap(para, f, T.TEXT_W)
    tw = max([f.getlength(T.plain(l)) for l in lines] + [0]); ah = 0
    if att and att[0] == "img": tw = max(tw, S.IMGW); ah = S.IMGW * 900 // 1440 + 16
    if att and att[0] == "file": tw = max(tw, 122 + T.ui(40).getlength(T.plain(att[1]))); ah = 130
    if lines: tw = max(tw, f.getlength(T.plain(lines[-1])) + (160 if out else 110))
    bw = int(tw + 2 * T.PADX); bh = int(len(lines) * T.LH + ah + 2 * T.PADY + (8 if lines else 30))
    im = Image.new("RGBA", (T.SW, bh)); d = ImageDraw.Draw(im)
    x0 = T.SW - 24 - bw if out else 24
    d.rounded_rectangle([x0, 0, x0 + bw, bh], T.RAD, fill=(T.OUTB if out else T.INB) + (255,))
    mut = T.OUTMUTED if out else T.INMUTED; y = T.PADY
    if att and att[0] == "img":
        th = S.thumb(att[1], bw - 2 * 14, S.IMGW * 900 // 1440, 26); im.alpha_composite(th, (x0 + 14, 14)); y = ah + 6
    if att and att[0] == "file":
        r = 50; T.doc_icon(d, x0 + T.PADX + r, y + r + 4, r)
        T.rich_text(im, d, x0 + T.PADX + 2 * r + 22, y + 30, att[1], T.ui(40), T.TXT)
        d.text((x0 + T.PADX + 2 * r + 22, y + 80), att[2], font=T.ui(32, False), fill=mut, anchor="lm")
    for l in lines:
        T.rich_text(im, d, x0 + T.PADX, y + T.LH / 2, l, f, S.LINK if "pay." in l else T.TXT); y += T.LH
    tx = x0 + bw - T.PADX - tf.getlength(tm) - (44 if out else 0)
    d.text((tx, bh - T.PADY - 14), tm, font=tf, fill=mut, anchor="lm")
    if out: T.checks(d, x0 + bw - T.PADX - 36, bh - T.PADY - 12, mut)
    return im


def chat_screen(t):
    im = T.empty_chat(SUB).crop((0, 0, T.SW, T.SHW)).copy(); items, y = [], 30
    for k, c in enumerate(MSGS):
        if t < c[0]: break
        b = bubble(k); extra = 12 if k + 1 < len(MSGS) and MSGS[k + 1][1] != c[1] else 0
        items.append((b, y, prog(t, c[0], 0.32))); y += lerp(0, b.height + T.GAP + extra, eout(prog(t, c[0], 0.28)))
    shift = max(0, y - T.GAP - (T.MSG_Y1 - T.MSG_Y0 - 40))
    for spr, yy, p in items:
        yy -= shift
        if yy + spr.height < -40: continue
        if p >= 1: put(im, spr, 0, T.MSG_Y0 + yy)
        else:
            s = lerp(0.9, 1.0, eback(p)); sp = spr.resize((int(spr.width * s), max(1, int(spr.height * s))), Image.BICUBIC)
            put(im, sp, (T.SW - sp.width) / 2, T.MSG_Y0 + yy + (spr.height - sp.height) / 2 + 24 * (1 - eout(p)), eout(p * 1.6))
    im.alpha_composite(T.top_layer(SUB), (0, 0))
    im.alpha_composite(T.bottom_layer(), (0, T.SHW - T.bottom_layer().height))
    return im


def chat_frame(t, caps=True, note_y=600):
    fr = background().copy(); c = S.card(chat_screen(t))
    z = 1 + 0.03 * ss(prog(t, T_NOTE, C_LEN - T_NOTE))
    if z > 1: c = c.resize((int(T.CW * z), int(T.CHH * z)), Image.LANCZOS)
    put(fr, T.card_shadow(), T.CX0 - 80, T.CY0 - 100)
    put(fr, c, T.CX0 - (c.width - T.CW) / 2, T.CY0 - (c.height - T.CHH) / 2)
    if t >= T_NOTE:
        p = eback(prog(t, T_NOTE, 0.45)); n = note()
        put(fr, n, (W - n.width) / 2, note_y - 40 - 200 * (1 - p), clamp(p * 1.5))
    if caps: S.caps(fr, t, C_CAPS)
    return fr


SCENES = [(F_LEN, formula_frame), (P_LEN, parse_frame), (L_LEN, list_frame), (C_LEN, chat_frame)]
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
    fr = formula_frame(F_LEN, caps=False, dy=70)          # на обложке формула ниже хука
    plates(fr, HOOK, 76, 450, lambda k: 1.0)
    fr.convert("RGB").save(OUT / "cover.jpg", quality=95)


def main(peek=None):
    OUT.mkdir(exist_ok=True); WORK.mkdir(parents=True, exist_ok=True)
    if peek:
        for s in peek: at(int(s * FPS)).save(WORK / f"peek_{s}.png")
        return
    sfx = [("sfx-pop.mp3", a, 0.25) for a in (0.0, 0.30, 0.72)]
    sfx += [("sfx-click.mp3", F_LEN + T_FILTER, 0.25)]
    sfx += [("sfx-pop.mp3", F_LEN + P_LEN + a, 0.12) for a in S.T_ROWS]
    t0 = F_LEN + P_LEN + L_LEN
    sfx += [("sfx-pop.mp3", t0 + m[0], 0.2) for m in MSGS if m[0] >= 0]
    sfx += [("sfx-click.mp3", t0 + T_NOTE, 0.3)]
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
