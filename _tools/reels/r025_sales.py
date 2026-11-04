"""Ролик «ИИ-агент сам продаёт сайты» (сценарий R025), ~8,5 с, без голоса и без автора.

Список чатов Telegram: агент пишет компаниям, текст размыт, видно только «…Делаю такие сайты. Актуально?»
и превью сайта; счётчик «отправлено» растёт → чат с Ольгой: вопросы, ответы агента, КП →
«Куда оплатить?» → ссылка → уведомление плашка банка «Перевод по СБП · +25 000 ₽» → конец (призыв — в описании).

Чат и шапка — из r019_harvi/r024_site. Превью сайтов — первые экраны работ Ивана
(work/r025/s1…s5.png, work/r024/site-top.png), логотипы в шапке размыты.

    python r025_sales.py              # -> example-r025-sales/final.mp4, cover.jpg
    python r025_sales.py peek 1 3 6   # кадры work/r025/peek_<t>.png
"""
import os, sys, pathlib, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r019_harvi as T                    # чат Telegram
from r014_avito import (W, H, FPS, GRAPH, OFF, BLUE, K, SS, clamp, prog, eout, ss, eback, lerp,
                        put, plates, background, xfade, font, down)
import r014_avito as R

WORK = pathlib.Path(os.environ.get("R025_WORK", K / "work" / "r025"))
OUT = pathlib.Path(__file__).resolve().parent / "example-r025-sales"
SITES = [WORK / f"s{i}.png" for i in range(1, 6)] + [K / "work" / "r024" / "site-top.png"]
LINK = (110, 180, 255)


# ── превью сайтов: размыты целиком ──────────────────────────────────
@functools.lru_cache(None)
def site(i):
    im = Image.open(SITES[i % len(SITES)]).convert("RGB").resize((1440, 900), Image.LANCZOS)
    return im.filter(ImageFilter.GaussianBlur(16))             # первый экран размыт целиком (Иван, 04.11)


@functools.lru_cache(None)
def thumb(i, w, h, r, blur=0.0):
    im = site(i).copy(); s = max(w / im.width, h / im.height)
    im = im.resize((int(im.width * s + 1), int(im.height * s + 1)), Image.LANCZOS).crop((0, 0, w, h))
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    im = im.convert("RGBA"); im.putalpha(T.rr_mask(w, h, r)); return im


# ── сцена 1: список чатов — агент пишет компаниям ────────────────────────────
A = 2.5                                   # длительность списка
COMP = ["{Строймонтаж}", "{Кровля Плюс}", "{Автосервис 24}", "{Клининг Профи}", "{Окна-Мастер}",
        "{Стоматология Дент}", "{Фитнес Лайн}", "{Мебель на заказ}", "{Грузоперевозки}",
        "{Салон Лаванда}", "{Школа английского}"]
ACOL = [(229, 115, 115), (100, 181, 246), (129, 199, 132), (255, 183, 77), (186, 104, 200), (77, 182, 172)]
N0 = 3                                    # строк в списке до начала ролика
T_ROWS = [0.05 + 0.27 * k for k in range(len(COMP) - N0)]   # новые сообщения: по одному каждые 0,27 с
SENT0 = 29
LIST_Y0, RH = 330, 200
LBG = (16, 20, 26)
HOOK = [(0.0, A - 0.25, [("ИИ-агент сам", OFF, GRAPH), ("продаёт сайты", BLUE, OFF)])]


@functools.lru_cache(None)
def row(k):
    im = Image.new("RGBA", (T.SW, RH), LBG + (255,)); d = ImageDraw.Draw(im)
    r = 59; cx, cy = 36 + r, RH / 2
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ACOL[k % len(ACOL)])
    d.text((cx, cy), T.plain(COMP[k])[0], font=T.ui(52), fill=(255, 255, 255), anchor="mm")
    T.blur_box(im, (cx - r, cy - r, cx + r, cy + r), 6)          # аватар компании тоже размыт
    x = 190
    T.rich_text(im, d, x, 52, COMP[k], T.ui(40), T.TXT)
    tm = f"18:{35 + k:02d}"; tf = T.ui(30, False)
    d.text((T.SW - 36, 52), tm, font=tf, fill=T.MUTED, anchor="rm")
    T.checks(d, T.SW - 36 - tf.getlength(tm) - 44, 54, LINK)
    th = thumb(k, 112, 92, 12, 1.2); im.alpha_composite(th, (x, 88))
    tx = x + 112 + 20; f = T.ui(35, False)
    T.rich_text(im, d, tx, 112, "{Здравствуйте! Посмотрел вашу компанию}", f, T.MUTED, r=8)
    d.text((tx, 160), "…Делаю такие сайты. Актуально?", font=f, fill=(206, 212, 220), anchor="lm")
    d.line([(x, RH - 1), (T.SW, RH - 1)], fill=(36, 42, 50), width=2)
    return im


@functools.lru_cache(None)
def list_bg():
    im = Image.new("RGBA", (T.SW, T.SHW), LBG + (255,))
    im.alpha_composite(T.empty_chat().crop((0, 0, T.SW, 125)), (0, 0))    # строка состояния
    d = ImageDraw.Draw(im)
    d.text((T.SW / 2, 214), "Чаты", font=T.ui(48), fill=T.TXT, anchor="mm")
    d.text((60, 214), "Изм.", font=T.ui(40, False), fill=LINK, anchor="lm")
    d.line([(0, LIST_Y0 - 2), (T.SW, LIST_Y0 - 2)], fill=(36, 42, 50), width=2)
    return im


def list_screen(t):
    im = list_bg().copy(); d = ImageDraw.Draw(im)
    n = sum(1 for a in T_ROWS if t >= a)
    sent = SENT0 + n
    d.text((T.SW / 2, 270), f"отправлено: {sent}", font=T.ui(32, False), fill=LINK, anchor="mm")
    # новые сверху: последняя появившаяся строка — индекс N0 + n - 1
    p = eout(prog(t, T_ROWS[n - 1], 0.26)) if n else 1.0
    ks = list(range(N0 + n - 1, -1, -1))
    for j, k in enumerate(ks):
        y = LIST_Y0 + (j - (1 - p)) * RH if j else LIST_Y0
        if j == 0 and n:
            put(im, row(k), 0, LIST_Y0 - 30 * (1 - p), clamp(p * 1.4))
            continue
        y = LIST_Y0 + (j - 1 + p) * RH if n else LIST_Y0 + j * RH
        if y > T.SHW: break
        put(im, row(k), 0, y)
    return im


def card(screen):
    c = screen.resize((T.CW, T.CHH), Image.LANCZOS); c.putalpha(T.card_mask())
    ImageDraw.Draw(c).rounded_rectangle([0, 0, T.CW - 1, T.CHH - 1], 44, outline=(255, 255, 255, 40), width=2)
    return c


def caps(fr, t, lst, size=60, y=356):
    for a, b, rows in lst:
        if a <= t < b + 0.3:
            o = ss(prog(t, b, 0.25))
            plates(fr, rows, size, y, lambda k: clamp(prog(t, a + 0.1 * k, 0.35) - o))


def list_frame(t, with_caps=True):
    fr = background().copy()
    put(fr, T.card_shadow(), T.CX0 - 80, T.CY0 - 100); put(fr, card(list_screen(t)), T.CX0, T.CY0)
    if with_caps: caps(fr, t, HOOK)
    return fr


# ── сцена 2: чат с Ольгой ────────────────────────────────────────────────────
T.NAME = "Ольга"
SUB = "в сети"


@functools.lru_cache(None)
def olga_avatar(d=128):
    ph = Image.open(K / "work" / "r019" / "av_olga.jpg").convert("RGB")
    s = ph.width * 0.62; ph = ph.crop(((ph.width - s) / 2, ph.height * 0.02, (ph.width + s) / 2, ph.height * 0.02 + s))
    ph = ph.resize((d, d), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", (d * 4, d * 4), 0); ImageDraw.Draw(m).ellipse([0, 0, d * 4 - 1, d * 4 - 1], fill=255)
    ph.putalpha(m.resize((d, d), Image.LANCZOS)); return ph


T.harvi_avatar = olga_avatar
IMGW = 560
IMG_SITE = 4                              # СЭЙВ — в первом сообщении крупно
CHAT = [  # (время, кто: in — Ольга / out — агент от вашего аккаунта, текст, вложение, время в чате)
    (-1.0, "out", "{Здравствуйте! Посмотрел вашу компанию на картах — сайта у вас пока нет.}\nДелаю такие сайты. Актуально?",
     ("img", IMG_SITE), "18:21"),
    (0.45, "in", "Здравствуйте. А по срокам сколько?", None, "18:32"),
    (0.90, "out", "Около двух недель. Тексты и фото возьмём с ваших карт.", None, "18:32"),
    (1.25, "in", "А заявки с сайта куда будут приходить?", None, "18:34"),
    (1.75, "out", "В Telegram или на почту — как вам удобнее.", None, "18:34"),
    (2.30, "in", "Пришлите КП, посмотрим.", None, "18:36"),
    (2.75, "out", None, ("file", "КП — сайт для {Строймонтаж}.pdf", "1,2 МБ · PDF"), "18:36"),
    (3.60, "in", "Всё подходит. Куда оплатить?", None, "18:44"),
    (4.05, "out", "{Ссылка на оплату:}\n{pay.example.ru/i/48213}", None, "18:44"),
]
T_NOTE = 4.5
CL = T_NOTE + 1.5                          # ролик кончается сразу после оплаты; призыв — в описании (Иван, 04.11)
CAPS = [(0.0, 2.2, [("Отвечает на вопросы", OFF, GRAPH)]),
        (2.3, 3.85, [("Отправляет КП", OFF, GRAPH)]),
        (T_NOTE, 99, [("Клиент оплатил", BLUE, OFF)])]
TOT = A + CL


@functools.lru_cache(None)
def bubble(k):
    _, who, text, att, tm = CHAT[k]
    f = T.ui(T.BF, False); tf = T.ui(30, False); out = who == "out"
    lines = []
    for para in (text.split("\n") if text else []): lines += T.wrap(para, f, T.TEXT_W)
    tw = max([f.getlength(T.plain(l)) for l in lines] + [0]); ah = 0
    if att and att[0] == "img": tw = max(tw, IMGW); ah = IMGW * 900 // 1440 + 16
    if att and att[0] == "file": tw = max(tw, 122 + T.ui(40).getlength(T.plain(att[1]))); ah = 130
    if lines: tw = max(tw, f.getlength(T.plain(lines[-1])) + (160 if out else 110))
    bw = int(tw + 2 * T.PADX); bh = int(len(lines) * T.LH + ah + 2 * T.PADY + (8 if lines else 30))
    im = Image.new("RGBA", (T.SW, bh)); d = ImageDraw.Draw(im)
    x0 = T.SW - 24 - bw if out else 24
    d.rounded_rectangle([x0, 0, x0 + bw, bh], T.RAD, fill=(T.OUTB if out else T.INB) + (255,))
    mut = T.OUTMUTED if out else T.INMUTED; y = T.PADY
    if att and att[0] == "img":
        th = thumb(att[1], bw - 2 * 14, IMGW * 900 // 1440, 26); im.alpha_composite(th, (x0 + 14, 14)); y = ah + 6
    if att and att[0] == "file":
        r = 50; T.doc_icon(d, x0 + T.PADX + r, y + r + 4, r)
        T.rich_text(im, d, x0 + T.PADX + 2 * r + 22, y + 30, att[1], T.ui(40), T.TXT)
        d.text((x0 + T.PADX + 2 * r + 22, y + 80), att[2], font=T.ui(32, False), fill=mut, anchor="lm")
    for l in lines:
        col = LINK if "pay." in l else T.TXT
        T.rich_text(im, d, x0 + T.PADX, y + T.LH / 2, l, f, col); y += T.LH
    tx = x0 + bw - T.PADX - tf.getlength(tm) - (44 if out else 0)
    d.text((tx, bh - T.PADY - 14), tm, font=tf, fill=mut, anchor="lm")
    if out: T.checks(d, x0 + bw - T.PADX - 36, bh - T.PADY - 12, mut)
    return im


def chat_screen(t):
    im = T.empty_chat(SUB).crop((0, 0, T.SW, T.SHW)).copy(); items, y = [], 30
    for k, c in enumerate(CHAT):
        if t < c[0]: break
        b = bubble(k); extra = 12 if k + 1 < len(CHAT) and CHAT[k + 1][1] != c[1] else 0
        items.append((b, y, prog(t, c[0], 0.32))); y += lerp(0, b.height + T.GAP + extra, eout(prog(t, c[0], 0.28)))
    shift = max(0, y - T.GAP - (T.MSG_Y1 - T.MSG_Y0 - 40))   # лента поднимается, как в Telegram
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


@functools.lru_cache(None)
def note():
    """Уведомление об оплате — картинка Ивана (Тинькофф, перевод по СБП, +25 000 ₽), work/r025/payment.png."""
    im = Image.open(WORK / "payment.png").convert("RGBA"); w = 880
    im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    sh = Image.new("RGBA", (w + 80, im.height + 80)); ImageDraw.Draw(sh).rounded_rectangle([40, 50, 40 + w, 50 + im.height], 40, fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(18)); sh.alpha_composite(im, (40, 40)); return sh


def chat_frame(t, with_caps=True, note_y=640):
    fr = background().copy()
    zoom = 1 + 0.03 * ss(prog(t, T_NOTE, CL - T_NOTE))             # лёгкий наезд после оплаты — без статики
    c = card(chat_screen(t))
    if zoom > 1: c = c.resize((int(T.CW * zoom), int(T.CHH * zoom)), Image.LANCZOS)
    x, y = T.CX0 - (c.width - T.CW) / 2, T.CY0 - (c.height - T.CHH) / 2
    put(fr, T.card_shadow(), T.CX0 - 80, T.CY0 - 100); put(fr, c, x, y)
    p = eback(prog(t, T_NOTE, 0.45))
    if t >= T_NOTE:
        n = note(); put(fr, n, (W - n.width) / 2, note_y - 40 - 200 * (1 - p), clamp(p * 1.5))
    if with_caps: caps(fr, t, CAPS)
    return fr


# ── сборка ───────────────────────────────────────────────────────────────────
COVER = [("ИИ-агент", OFF, GRAPH), ("сам продаёт сайты", BLUE, OFF)]


def make_cover():
    fr = chat_frame(5.3, with_caps=False, note_y=790)               # видны «Пришлите КП», КП и уведомление об оплате
    plates(fr, COVER, 76, 430, lambda k: 1.0)
    fr.convert("RGB").save(OUT / "cover.jpg", quality=95)


def at(i):
    t = i / FPS; XF = R.XF
    if t < A:
        fr = list_frame(t).convert("RGB")
        if t > A - XF: fr = xfade(fr, chat_frame(0).convert("RGB"), (t - (A - XF)) / XF)
    else:
        fr = chat_frame(t - A).convert("RGB")
    return fr


def main(peek=None):
    OUT.mkdir(exist_ok=True); WORK.mkdir(exist_ok=True)
    if peek:
        for s in peek: at(int(s * FPS)).save(WORK / f"peek_{s}.png")
        return
    sfx = [("sfx-pop.mp3", a, 0.12) for a in T_ROWS]
    sfx += [("sfx-pop.mp3", A + c[0], 0.2) for c in CHAT if c[0] >= 0]
    sfx += [("sfx-click.mp3", A + T_NOTE, 0.3)]
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
