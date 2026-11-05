"""Ролик «Claude + 2ГИС = деньги» (сценарий R031), ~9,5 с, без голоса и без автора.

Формула: [Claude] + [2ГИС] = уведомление «+ 40 000 ₽» → парсинг: экраны бота AuditLeadBot —
«собрано 548» → «Найдено 7 компаний без сайта» + CSV → список чатов: агент пишет компаниям (как R025) →
переписка с Дмитрием: цена, КП, «Куда платить?» → то же уведомление «+ 40 000 ₽» → конец.
Призыв — только в описании (правило R025). Сообщения агента выглядят обычными (правило R030).

Логотипы прислал Иван (work/r031/logo-*-src.png), приведены к одной плитке с одинаковым скруглением.
Экран парсинга — настоящие кадры бота Ивана AuditLeadBot (work/r031/bot/, из видео IMG_7762).

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


# ── сцена 2: парсинг — настоящие экраны бота Ивана AuditLeadBot (видео IMG_7762, 05.11) ──────
P_LEN = 2.3
BOT = [WORK / "bot" / "full_19.5.png",              # «Стоматология · Казань: в 2ГИС ~550, собрано 548»
       WORK / "bot" / "full_52.0.png"]              # «Найдено 7 компаний без сайта» + CSV с лидами
P_SWITCH = 1.15


# какой кусок кадра показать (y в px исходника 888×1920): сообщение «собрано 548» и кнопки / «Найдено 7» и CSV
BOT_Y = [(800, 1640), (1050, 1920)]


@functools.lru_cache(None)
def bot_shot(k):
    """Кадр бота в размере экрана Telegram (1170 px), красная метка записи экрана закрашена."""
    im = Image.open(BOT[k]).convert("RGB"); sc = T.SW / im.width
    im = im.resize((T.SW, round(im.height * sc)), Image.LANCZOS); d = ImageDraw.Draw(im)
    box = [int(70 * sc), int(14 * sc), int(232 * sc), int(84 * sc)]
    col = tuple(int(c) for c in np.asarray(im.crop((box[2] + 30, box[1], box[2] + 70, box[3]))).reshape(-1, 3).mean(0))
    d.rounded_rectangle(box, 20, fill=col)
    d.text(((box[0] + box[2]) / 2, (box[1] + box[3]) / 2 + 2), "13:27" if k == 0 else "13:28", font=T.ui(int(31 * sc)), fill=(255, 255, 255), anchor="mm")
    return im.convert("RGBA"), sc


def bot_screen(k, t, dur):
    """Шапка бота сверху + нужный кусок переписки, вписанный по высоте; лёгкий подъезд снизу — без статики."""
    im, sc = bot_shot(k); top = int(T.TOP_H * 0.86); body_h = T.SHW - top
    lift = 70 * (1 - eout(prog(t, 0, dur)))
    ya, yb = (v * sc for v in BOT_Y[k]); ya += lift; yb = min(yb + lift, im.height)
    reg = im.crop((0, int(ya), T.SW, int(yb)))
    f = min(1.0, body_h / reg.height); rw, rh = int(T.SW * f), int(reg.height * f)
    back = reg.resize((T.SW, body_h), Image.BILINEAR).filter(ImageFilter.GaussianBlur(30))   # поля по бокам — тот же фон
    scr = Image.new("RGBA", (T.SW, T.SHW)); scr.alpha_composite(back, (0, top))
    scr.alpha_composite(reg.resize((rw, rh), Image.LANCZOS), ((T.SW - rw) // 2, top + body_h - rh))
    scr.alpha_composite(im.crop((0, 0, T.SW, top)), (0, 0))
    return scr


def phone_frame(screen, t, cap_list):
    fr = background().copy()
    put(fr, T.card_shadow(), T.CX0 - 80, T.CY0 - 100); put(fr, S.card(screen), T.CX0, T.CY0)
    S.caps(fr, t, cap_list); return fr


P_CAPS = [(0.0, 99, [("Нашёл компании", OFF, GRAPH), ("без сайта", BLUE, OFF)])]


def parse_frame(t):
    if t < P_SWITCH:
        fr = phone_frame(bot_screen(0, t, P_SWITCH), t, P_CAPS)
        XF = R.XF
        if t > P_SWITCH - XF:
            fr = xfade(fr.convert("RGB"), phone_frame(bot_screen(1, 0, P_LEN - P_SWITCH), t, P_CAPS).convert("RGB"),
                       (t - (P_SWITCH - XF)) / XF)
        return fr
    return phone_frame(bot_screen(1, t - P_SWITCH, P_LEN - P_SWITCH), t, P_CAPS)


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
    sfx += [("sfx-click.mp3", F_LEN + P_SWITCH, 0.25)]
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
