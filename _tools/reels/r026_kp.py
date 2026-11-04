"""Ролик «Клиенту дорого — а он оплатил» (сценарий R026), ~10,8 с, без голоса и без автора.

Список рассылки (как R025, короче) → чат с Мариной: «Сколько стоит?» → «60 000 ₽» → «Нет, дорого.» →
чат с Харви: переписка переслана, агент собирает КП с двумя вариантами →
снова Марина: КП → «О, «Старт» подходит. Куда платить?» → ссылка (размыта) → уведомление Тинькофф + 25 000 ₽ → конец.
Призыв — только в описании (правило R025).

Части — из r025_sales (список, превью, уведомление work/r025/payment.png) и r019_harvi (чат, Харви).

    python r026_kp.py              # -> example-r026-kp/final.mp4, cover.jpg
    python r026_kp.py peek 1 3 6   # кадры work/r026/peek_<t>.png
"""
import os, sys, pathlib, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r019_harvi as T
import r025_sales as S
from r014_avito import (W, H, FPS, GRAPH, OFF, BLUE, K, clamp, prog, eout, eback, lerp, ss, put, plates, background, xfade)
import r014_avito as R

WORK = pathlib.Path(os.environ.get("R026_WORK", K / "work" / "r026"))
OUT = pathlib.Path(__file__).resolve().parent / "example-r026-kp"

# ── шапки двух чатов: кэш empty_chat — по подписи, поэтому прогреваем по очереди ──
@functools.lru_cache(None)
def face(path, d=128):
    ph = Image.open(path).convert("RGB")
    s = ph.width * 0.62; ph = ph.crop(((ph.width - s) / 2, ph.height * 0.02, (ph.width + s) / 2, ph.height * 0.02 + s))
    ph = ph.resize((d, d), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", (d * 4, d * 4), 0); ImageDraw.Draw(m).ellipse([0, 0, d * 4 - 1, d * 4 - 1], fill=255)
    ph.putalpha(m.resize((d, d), Image.LANCZOS)); return ph


def harvi_face(d=128):
    """Аватар Харви — как в R019 (голова с лендинга HARVI в синем круге)."""
    k = 4; im = Image.new("RGBA", (d * k, d * k)); dr = ImageDraw.Draw(im)
    dr.ellipse([0, 0, d * k - 1, d * k - 1], fill=(23, 105, 255, 255))
    head = Image.open(T.HARVI_HEAD).convert("RGBA"); head = head.crop(head.getbbox())
    s = d * k * 0.92 / max(head.size); head = head.resize((int(head.width * s), int(head.height * s)), Image.LANCZOS)
    im.alpha_composite(head, ((d * k - head.width) // 2, int(d * k * 0.12)))
    m = Image.new("L", im.size, 0); ImageDraw.Draw(m).ellipse([0, 0, d * k - 1, d * k - 1], fill=255)
    im.putalpha(Image.fromarray(np.minimum(np.asarray(m), np.asarray(im.getchannel("A")))))
    return im.resize((d, d), Image.LANCZOS)


SUB_C, SUB_H = "был(а) недавно", "ИИ-агент"
T.empty_chat()                                       # строка состояния для списка (имя не видно)
T.NAME = "Марина"; T.harvi_avatar = lambda d=128: face(K / "work" / "r019" / "av_marina.jpg", d)
T.empty_chat(SUB_C); T.top_layer(SUB_C)
T.NAME = "Харви"; T.harvi_avatar = harvi_face
T.empty_chat(SUB_H); T.top_layer(SUB_H)

# ── сцена 1: список рассылки, коротко ─────────────────────────────────────────
L = 1.5
S.T_ROWS = [0.05 + 0.25 * k for k in range(5)]
HOOK = [(-9, 1.35, [("Клиенту дорого —", OFF, GRAPH), ("а он оплатил", BLUE, OFF)])]

# ── сообщения: (время, кто: in / out / fwd, текст, вложение, время в чате, переслано от) ──
FIRST = (-1.0, "out", "{Здравствуйте! Посмотрел вашу компанию на картах — сайта у вас пока нет.}\nДелаю такие сайты. Актуально?",
         ("img", 1), "18:21", None)
C1 = [FIRST,
      (0.45, "in", "Да, интересно. Сколько стоит?", None, "18:30", None),
      (0.95, "out", "60 000 ₽", None, "18:31", None),
      (1.50, "in", "Нет, дорого.", None, "18:33", None)]
C1_LEN = 3.0
C1_CAPS = HOOK + [(1.55, 99, [("Клиент отказался", OFF, GRAPH)])]

H1 = [(0.05, "fwd", "Да, интересно. Сколько стоит?", None, "18:38", "Марина"),
      (0.20, "fwd", "60 000 ₽", None, "18:38", "Иван"),
      (0.35, "fwd", "Нет, дорого.", None, "18:38", "Марина"),
      (1.05, "in", "Клиенту дорого. Собрал КП с двумя вариантами:\n«Под ключ» — 60 000 ₽\n«Старт» — 25 000 ₽", None, "18:39", None),
      (1.60, "in", None, ("file", "КП — сайт для {Кровля Плюс}.pdf", "1,4 МБ · PDF"), "18:39", None)]
H1_LEN = 3.0
H1_CAPS = [(0.0, 0.95, [("Пересылаю переписку", OFF, GRAPH), ("ИИ-агенту", BLUE, OFF)]),
           (1.05, 99, [("Агент собрал КП", OFF, GRAPH)])]

C2 = [(-1.0,) + c[1:] for c in C1] + [          # прежняя переписка уже на месте
      (0.20, "out", None, ("file", "КП — сайт для {Кровля Плюс}.pdf", "1,4 МБ · PDF"), "18:40", None),
      (0.80, "in", "О, «Старт» подходит. Куда платить?", None, "18:44", None),
      (1.30, "out", "{Ссылка на оплату:}\n{pay.example.ru/i/48213}", None, "18:44", None)]
T_NOTE = 1.8
C2_LEN = T_NOTE + 1.5                      # конец через 1,5 с после оплаты
C2_CAPS = [(0.0, T_NOTE - 0.15, [("Отправляю КП клиенту", OFF, GRAPH)]),
           (T_NOTE, 99, [("Клиент оплатил", BLUE, OFF)])]
TOT = L + C1_LEN + H1_LEN + C2_LEN


@functools.lru_cache(None)
def bubble(m):
    _, who, text, att, tm, fwd = m
    f = T.ui(T.BF, False); tf = T.ui(30, False); out = who in ("out", "fwd")
    lines = []
    for para in (text.split("\n") if text else []): lines += T.wrap(para, f, T.TEXT_W)
    tw = max([f.getlength(T.plain(l)) for l in lines] + [0]); ah = head = 0
    if fwd: head = 84; tw = max(tw, T.ui(32, False).getlength("Переслано от") + 20, T.ui(36).getlength(fwd))
    if att and att[0] == "img": tw = max(tw, S.IMGW); ah = S.IMGW * 900 // 1440 + 16
    if att and att[0] == "file": tw = max(tw, 122 + T.ui(40).getlength(T.plain(att[1]))); ah = 130
    if lines: tw = max(tw, f.getlength(T.plain(lines[-1])) + (160 if out else 110))
    bw = int(tw + 2 * T.PADX); bh = int(head + len(lines) * T.LH + ah + 2 * T.PADY + (8 if lines else 30))
    im = Image.new("RGBA", (T.SW, bh)); d = ImageDraw.Draw(im)
    x0 = T.SW - 24 - bw if out else 24
    d.rounded_rectangle([x0, 0, x0 + bw, bh], T.RAD, fill=(T.OUTB if out else T.INB) + (255,))
    mut = T.OUTMUTED if out else T.INMUTED; y = T.PADY
    if fwd:
        d.text((x0 + T.PADX, y + 2), "Переслано от", font=T.ui(32, False), fill=mut); y += 40
        d.text((x0 + T.PADX, y + 22), fwd, font=T.ui(36), fill=mut, anchor="lm"); y += 44
    if att and att[0] == "img":
        th = S.thumb(att[1], bw - 2 * 14, S.IMGW * 900 // 1440, 26); im.alpha_composite(th, (x0 + 14, 14)); y = ah + 6
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


def chat_screen(msgs, t, sub):
    im = T.empty_chat(sub).crop((0, 0, T.SW, T.SHW)).copy(); items, y = [], 30
    for k, c in enumerate(msgs):
        if t < c[0]: break
        b = bubble(c); extra = 12 if k + 1 < len(msgs) and msgs[k + 1][1] != c[1] else 0
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


def chat_frame(msgs, sub, t, caps_list, note_at=None, note_y=640, zoom_from=None, dur=None):
    fr = background().copy(); c = S.card(chat_screen(msgs, t, sub))
    if zoom_from is not None:
        z = 1 + 0.03 * ss(prog(t, zoom_from, dur - zoom_from))
        if z > 1: c = c.resize((int(T.CW * z), int(T.CHH * z)), Image.LANCZOS)
    put(fr, T.card_shadow(), T.CX0 - 80, T.CY0 - 100)
    put(fr, c, T.CX0 - (c.width - T.CW) / 2, T.CY0 - (c.height - T.CHH) / 2)
    if note_at is not None and t >= note_at:
        p = eback(prog(t, note_at, 0.45)); n = S.note()
        put(fr, n, (W - n.width) / 2, note_y - 40 - 200 * (1 - p), clamp(p * 1.5))
    if caps_list: S.caps(fr, t, caps_list)
    return fr


def list_frame(t):
    fr = background().copy()
    put(fr, T.card_shadow(), T.CX0 - 80, T.CY0 - 100); put(fr, S.card(S.list_screen(t)), T.CX0, T.CY0)
    S.caps(fr, t, [(0.0, 99, HOOK[0][2])]); return fr


SCENES = [  # (длительность, кадр(t))
    (L, list_frame),
    (C1_LEN, lambda t: chat_frame(C1, SUB_C, t, C1_CAPS)),
    (H1_LEN, lambda t: chat_frame(H1, SUB_H, t, H1_CAPS)),
    (C2_LEN, lambda t: chat_frame(C2, SUB_C, t, C2_CAPS, note_at=T_NOTE, zoom_from=T_NOTE, dur=C2_LEN)),
]


def at(i):
    t = i / FPS; XF = R.XF; t0 = 0.0
    for j, (dur, fn) in enumerate(SCENES):
        if t < t0 + dur or j == len(SCENES) - 1:
            fr = fn(t - t0).convert("RGB")
            if j + 1 < len(SCENES) and t > t0 + dur - XF:
                fr = xfade(fr, SCENES[j + 1][1](0).convert("RGB"), (t - (t0 + dur - XF)) / XF)
            return fr
        t0 += dur


COVER = [("Клиенту дорого —", OFF, GRAPH), ("а он оплатил", BLUE, OFF)]


def make_cover():
    fr = chat_frame(C2, SUB_C, C2_LEN, [], note_at=T_NOTE, note_y=790)
    plates(fr, COVER, 76, 430, lambda k: 1.0)
    fr.convert("RGB").save(OUT / "cover.jpg", quality=95)


def main(peek=None):
    OUT.mkdir(exist_ok=True); WORK.mkdir(exist_ok=True)
    if peek:
        for s in peek: at(int(s * FPS)).save(WORK / f"peek_{s}.png")
        return
    sfx = [("sfx-pop.mp3", a, 0.12) for a in S.T_ROWS]
    t0 = L
    for msgs, dur in [(C1, C1_LEN), (H1, H1_LEN), (C2, C2_LEN)]:
        sfx += [("sfx-pop.mp3", t0 + m[0], 0.2) for m in msgs if m[0] >= 0]; t0 += dur
    sfx += [("sfx-click.mp3", L + C1_LEN + H1_LEN + T_NOTE, 0.3)]
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
