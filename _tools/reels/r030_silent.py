"""Ролик «Молчал после КП — а потом оплатил» (сценарий R030), ~8 с, без голоса и без автора.

Один чат с Анной: КП на 35 000 ₽ «падает» в чат с первого кадра → разделители дат Вторник / Среда / Четверг
(«3 дня тишины») → ИИ-агент сам пишет напоминание (метка «ИИ-агент» над сообщением) → «печатает…» →
«Куда платить?» → ссылка (размыта) → уведомление Тинькофф + 35 000 ₽ → конец через 1,5 с.
Призыв — только в описании (правило R025).

По аналитике 05.11: телефон крупнее, чем в R024–R029 (980 px вместо 860), движение с нулевой секунды,
длина ~8 с, последний кадр близок к первому (зацикливание).

Части — из r025_sales (карточка, плашки, уведомление — work/r025/payment.png с суммой 35 000 ₽ через payment_note.py) и r019_harvi (чат).

    python r030_silent.py              # -> example-r030-silent/final.mp4, cover.jpg
    python r030_silent.py peek 0.5 2.4 # кадры work/r030/peek_<t>.png
"""
import os, sys, pathlib, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r019_harvi as T
import r025_sales as S
import payment_note
from r014_avito import (W, H, FPS, GRAPH, OFF, BLUE, K, clamp, prog, eout, eback, lerp, ss, put, plates, background)

WORK = pathlib.Path(os.environ.get("R030_WORK", K / "work" / "r030"))
OUT = pathlib.Path(__file__).resolve().parent / "example-r030-silent"

# ── телефон крупнее: 980×1060 вместо 860×1000 (гипотеза из аналитики 05.11) ──
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


T.NAME = "Анна"; T.harvi_avatar = lambda d=128: face(K / "work" / "r019" / "av_anna.jpg", d)
SUBS = ["была недавно", "была 3 дня назад", "печатает…", "в сети"]
for s in SUBS: T.empty_chat(s); T.top_layer(s)

# ── сообщения: (время, кто: in / out / sep, текст, вложение, время в чате, метка) ──
AMOUNT = 35000                                       # своя сумма, чтобы плашки оплаты в роликах были разные
KP = ("file", "КП — сайт для {Студия Лофт}.pdf", "35 000 ₽ · PDF")
AGENT = "ИИ-агент"
T_NOTE = 6.1
TOT = T_NOTE + 1.5                                   # конец через 1,5 с после оплаты
MSGS = [
    (-1.0, "sep", "Понедельник", None, "", None),
    (-1.0, "in", "Пришлите КП, посмотрим.", None, "18:20", None),
    (0.05, "out", None, KP, "18:42", None),               # движение с нулевой секунды
    (1.60, "sep", "Вторник", None, "", None),
    (1.95, "sep", "Среда", None, "", None),
    (2.30, "sep", "Четверг", None, "", None),
    (3.10, "out", "Анна, добрый день! По КП остались вопросы? Если начнём на этой неделе — первый экран покажу в понедельник.",
     None, "11:05", AGENT),
    (4.90, "in", "Ой, совсем закрутилась. Давайте начнём. Куда платить?", None, "11:17", None),
    (5.45, "out", "{Ссылка на оплату:}\n{pay.example.ru/i/48213}", None, "11:18", None),
]
CAPS = [(0.0, 1.45, [("Молчал после КП —", OFF, GRAPH), ("а потом оплатил", BLUE, OFF)]),
        (1.55, 2.95, [("3 дня тишины", OFF, GRAPH)]),
        (3.05, T_NOTE - 0.15, [("ИИ-агент напомнил сам", BLUE, OFF)]),
        (T_NOTE, 99, [("Клиент оплатил", BLUE, OFF)])]


def sub_at(t):
    if t < 1.5: return SUBS[0]
    if t < 4.25: return SUBS[1]
    if t < 4.9: return SUBS[2]
    return SUBS[3]


@functools.lru_cache(None)
def sep(text):
    f = T.ui(34); w = int(f.getlength(text) + 56); h = 60
    im = Image.new("RGBA", (T.SW, h + 12)); d = ImageDraw.Draw(im)
    x0 = (T.SW - w) // 2
    d.rounded_rectangle([x0, 6, x0 + w, 6 + h], 30, fill=(20, 28, 38, 200))
    d.text((T.SW / 2, 6 + h / 2), text, font=f, fill=(225, 232, 240), anchor="mm")
    return im


@functools.lru_cache(None)
def bubble(m):
    _, who, text, att, tm, tag = m
    if who == "sep": return sep(text)
    f = T.ui(T.BF, False); tf = T.ui(30, False); out = who == "out"
    lines = []
    for para in (text.split("\n") if text else []): lines += T.wrap(para, f, T.TEXT_W)
    tw = max([f.getlength(T.plain(l)) for l in lines] + [0]); ah = head = 0
    if tag: head = 52; tw = max(tw, T.ui(34).getlength(tag) + 60)
    if att and att[0] == "file": tw = max(tw, 122 + T.ui(40).getlength(T.plain(att[1]))); ah = 130
    if lines: tw = max(tw, f.getlength(T.plain(lines[-1])) + (160 if out else 110))
    bw = int(tw + 2 * T.PADX); bh = int(head + len(lines) * T.LH + ah + 2 * T.PADY + (8 if lines else 30))
    im = Image.new("RGBA", (T.SW, bh)); d = ImageDraw.Draw(im)
    x0 = T.SW - 24 - bw if out else 24
    d.rounded_rectangle([x0, 0, x0 + bw, bh], T.RAD, fill=(T.OUTB if out else T.INB) + (255,))
    mut = T.OUTMUTED if out else T.INMUTED; y = T.PADY
    if tag:                                            # метка «ИИ-агент»: точка + подпись
        d.ellipse([x0 + T.PADX, y + 10, x0 + T.PADX + 22, y + 32], fill=(120, 190, 255))
        d.text((x0 + T.PADX + 36, y + 21), tag, font=T.ui(34), fill=(150, 205, 255), anchor="lm"); y += head
    if att and att[0] == "file":
        r = 50; T.doc_icon(d, x0 + T.PADX + r, y + r + 4, r)
        T.rich_text(im, d, x0 + T.PADX + 2 * r + 22, y + 30, att[1], T.ui(40), T.TXT)
        d.text((x0 + T.PADX + 2 * r + 22, y + 80), att[2], font=T.ui(32, False), fill=mut, anchor="lm")
    for l in lines:
        T.rich_text(im, d, x0 + T.PADX, y + T.LH / 2, l, f, T.TXT); y += T.LH
    tx = x0 + bw - T.PADX - tf.getlength(tm) - (44 if out else 0)
    d.text((tx, bh - T.PADY - 14), tm, font=tf, fill=mut, anchor="lm")
    if out: T.checks(d, x0 + bw - T.PADX - 36, bh - T.PADY - 12, mut)
    return im


def chat_screen(t):
    sub = sub_at(t)
    im = T.empty_chat(sub).crop((0, 0, T.SW, T.SHW)).copy(); items, y = [], 30
    for k, c in enumerate(MSGS):
        if t < c[0]: break
        b = bubble(c); extra = 12 if k + 1 < len(MSGS) and MSGS[k + 1][1] != c[1] else 0
        items.append((b, y, prog(t, c[0], 0.32))); y += lerp(0, b.height + T.GAP + extra, eout(prog(t, c[0], 0.28)))
    shift = max(0, y - T.GAP - (T.MSG_Y1 - T.MSG_Y0 - 40))
    for spr, yy, p in items:
        yy -= shift
        if yy + spr.height < -40: continue
        if p >= 1: put(im, spr, 0, T.MSG_Y0 + yy)
        else:
            s = lerp(0.9, 1.0, eback(p)); sp = spr.resize((int(spr.width * s), max(1, int(spr.height * s))), Image.BICUBIC)
            put(im, sp, (T.SW - sp.width) / 2, T.MSG_Y0 + yy + (spr.height - sp.height) / 2 + 24 * (1 - eout(p)), eout(p * 1.6))
    im.alpha_composite(T.top_layer(sub), (0, 0))
    im.alpha_composite(T.bottom_layer(), (0, T.SHW - T.bottom_layer().height))
    return im


def frame(t, caps=True, note_y=600):
    fr = background().copy(); c = S.card(chat_screen(t))
    z = 1 + 0.03 * ss(prog(t, T_NOTE, TOT - T_NOTE))   # лёгкий наезд после оплаты
    if z > 1: c = c.resize((int(T.CW * z), int(T.CHH * z)), Image.LANCZOS)
    put(fr, T.card_shadow(), T.CX0 - 80, T.CY0 - 100)
    put(fr, c, T.CX0 - (c.width - T.CW) / 2, T.CY0 - (c.height - T.CHH) / 2)
    if t >= T_NOTE:
        p = eback(prog(t, T_NOTE, 0.45)); n = note()
        put(fr, n, (W - n.width) / 2, note_y - 40 - 200 * (1 - p), clamp(p * 1.5))
    if caps: S.caps(fr, t, CAPS)
    return fr


@functools.lru_cache(None)
def note():
    """Уведомление об оплате: картинка Ивана из R025 с суммой AMOUNT (payment_note.py)."""
    im = Image.open(payment_note.make(AMOUNT, WORK / "payment.png")).convert("RGBA"); w = 880
    im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    sh = Image.new("RGBA", (w + 80, im.height + 80)); ImageDraw.Draw(sh).rounded_rectangle([40, 50, 40 + w, 50 + im.height], 40, fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(18)); sh.alpha_composite(im, (40, 40)); return sh


def at(i): return frame(i / FPS).convert("RGB")


COVER = [("Молчал после КП —", OFF, GRAPH), ("а потом оплатил", BLUE, OFF)]


def make_cover():
    T.CY0 += 110                                      # на обложке телефон ниже, чтобы хук не закрывал шапку чата
    fr = frame(TOT, caps=False, note_y=860)
    T.CY0 -= 110
    plates(fr, COVER, 76, 450, lambda k: 1.0)
    fr.convert("RGB").save(OUT / "cover.jpg", quality=95)


def main(peek=None):
    OUT.mkdir(exist_ok=True); WORK.mkdir(parents=True, exist_ok=True)
    if peek:
        for s in peek: at(int(s * FPS)).save(WORK / f"peek_{s}.png")
        return
    sfx = [("sfx-pop.mp3", m[0], 0.2) for m in MSGS if m[0] >= 0 and m[1] != "sep"]
    sfx += [("sfx-click.mp3", m[0], 0.12) for m in MSGS if m[0] >= 0 and m[1] == "sep"]
    sfx += [("sfx-click.mp3", T_NOTE, 0.3)]
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
