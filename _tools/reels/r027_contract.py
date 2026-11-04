"""Ролик «Договор собирает ИИ-агент» (сценарий R027), ~11,6 с, без голоса и без автора.

Список рассылки → чат с Анной: «Сколько?» → «50 000 ₽» → «Согласна. Сделайте договор» → реквизиты (размыты) →
чат с Харви: пересланы просьба и реквизиты, агент отдаёт готовый договор → превью договора, данные клиента
подсвечены и размыты → снова Анна: договор → «Подписала, оплачиваю предоплату» → уведомление Тинькофф + 25 000 ₽ → конец.

Части — из r026_kp (список, чаты, сборка), r025_sales (уведомление) и r019_harvi (страница договора).

    python r027_contract.py              # -> example-r027-contract/final.mp4, cover.jpg
    python r027_contract.py peek 1 3 6   # кадры work/r027/peek_<t>.png
"""
import os, sys, pathlib, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r019_harvi as T
import r025_sales as S
import r026_kp as P
from r014_avito import (W, H, FPS, GRAPH, OFF, BLUE, K, clamp, prog, eout, ss, put, plates, background, xfade)
import r014_avito as R

WORK = pathlib.Path(os.environ.get("R027_WORK", K / "work" / "r027"))
OUT = pathlib.Path(__file__).resolve().parent / "example-r027-contract"

# ── шапка чата с Анной (кэш empty_chat — по подписи) ─────────────────────────
SUB_C, SUB_H = "в сети", P.SUB_H
T.NAME = "Анна"; T.harvi_avatar = lambda d=128: P.face(K / "work" / "r019" / "av_anna.jpg", d)
T.empty_chat(SUB_C); T.top_layer(SUB_C)

# ── сцена 1: рассылка ────────────────────────────────────────────────────────
L = 1.5
P.HOOK = [(-9, 1.35, [("Клиент просит договор —", OFF, GRAPH), ("его собирает ИИ-агент", BLUE, OFF)])]

DOCX = ("file", "Договор №28 — {Вектор}.docx", "48 КБ · DOCX")
REQ = "Реквизиты:\n{ООО «Вектор»}\nИНН {7700000000}\nОГРН {1027700000000}\nДиректор: {Иванова О. С.}"
C1 = [(-1.0, "out", "{Здравствуйте! Посмотрел вашу компанию на картах — сайта у вас пока нет.}\nДелаю такие сайты. Актуально?",
       ("img", 2), "18:21", None),
      (0.40, "in", "Да, нужен сайт. Сколько стоит?", None, "18:28", None),
      (0.90, "out", "50 000 ₽, срок — 2 недели.", None, "18:29", None),
      (1.45, "in", "Согласна. Сделайте договор", None, "18:31", None),
      (1.95, "in", REQ, None, "18:31", None)]
C1_LEN = 3.3
C1_CAPS = P.HOOK + [(1.45, 99, [("Клиент просит договор", OFF, GRAPH)])]

# ── сцена 2: Харви собирает договор, превью ───────────────────────────────────
H1 = [(0.05, "fwd", "Согласна. Сделайте договор", None, "18:33", "Анна"),
      (0.20, "fwd", REQ, None, "18:33", "Анна"),
      (0.95, "in", "Договор готов: реквизиты подставил, сайт под ключ — 50 000 ₽, предоплата 50 %.", None, "18:34", None),
      (1.40, "in", None, DOCX, "18:34", None)]
T_VIEW = 1.9                               # открывается договор
T_SCROLL = (2.35, 4.0)
H1_LEN = 4.5
H1_CAPS = [(0.0, 0.85, [("Пересылаю переписку", OFF, GRAPH), ("ИИ-агенту", BLUE, OFF)]),
           (0.95, 1.8, [("Договор готов", OFF, GRAPH)]),
           (1.95, 99, [("Реквизиты и сумма —", OFF, GRAPH), ("уже на месте", BLUE, OFF)])]

T.DOC = [   # вымышленный клиент; подсвеченное — то, что подставил агент, размыто (правило R019)
    ("T", "ДОГОВОР № 28"), ("C", "на оказание услуг по разработке сайта"), ("R", None),
    ("P", [("ООО «Вектор»", 1), ("(ИНН", 0), ("7700000000),", 1), ("именуемое в дальнейшем «Заказчик», в лице генерального директора", 0),
           ("Ивановой Ольги Сергеевны,", 1), ("действующей на основании Устава, с одной стороны, и Исполнитель, с другой стороны, заключили настоящий договор о нижеследующем.", 0)]),
    ("H", "1. ПРЕДМЕТ ДОГОВОРА"),
    ("P", [("1.1. Исполнитель обязуется выполнить работы:", 0), ("разработка сайта под ключ,", 1),
           ("а Заказчик — принять и оплатить их.", 0)]),
    ("H", "2. СТОИМОСТЬ И ПОРЯДОК ОПЛАТЫ"),
    ("P", [("2.1. Стоимость работ составляет", 0), ("50 000 (пятьдесят тысяч) рублей,", 1), ("НДС не облагается.", 0)]),
    ("P", [("2.2. Предоплата 50 % —", 0), ("25 000 рублей —", 1), ("в течение 3 банковских дней после подписания договора, остаток — после подписания акта.", 0)]),
    ("H", "3. СРОКИ"),
    ("P", [("3.1. Срок выполнения работ —", 0), ("10 рабочих дней", 1), ("с даты поступления предоплаты.", 0)]),
    ("H", "4. РЕКВИЗИТЫ СТОРОН"),
    ("P", [("Заказчик:", 0), ("ООО «Вектор», ИНН 7700000000, ОГРН 1027700000000, г. Москва, ул. Примерная, д. 1", 1)]),
]


def viewer(t):
    """Просмотрщик iOS, как в R019: светлая шторка, имя файла, страница листается."""
    im = Image.new("RGBA", (T.SW, T.SHW), (242, 242, 247, 255)); d = ImageDraw.Draw(im)
    pg = T.doc_page(); off = ss(prog(t, T_SCROLL[0], T_SCROLL[1] - T_SCROLL[0])) * max(0, pg.height - (T.SHW - 300))
    sh = Image.new("RGBA", (pg.width + 40, pg.height + 40)); ImageDraw.Draw(sh).rectangle([20, 24, pg.width + 20, pg.height + 24], fill=(0, 0, 0, 40))
    put(im, sh.filter(ImageFilter.GaussianBlur(10)), (T.SW - pg.width) / 2 - 20, 240 - off - 20)
    put(im, pg, (T.SW - pg.width) / 2, 240 - off)
    d.rectangle([0, 0, T.SW, 200], fill=(249, 249, 251, 255)); d.line([(0, 200), (T.SW, 200)], fill=(210, 210, 215), width=2)
    d.text((52, 120), "Готово", font=T.ui(42), fill=(10, 132, 255), anchor="lm")
    name = "Договор №28 — {Вектор}.docx"
    T.rich_text(im, d, T.SW / 2 - T.ui(38).getlength(T.plain(name)) / 2, 120, name, T.ui(38), (0, 0, 0))
    return im


def harvi_frame(t):
    fr = P.chat_frame(H1, SUB_H, t, [])
    vp = eout(prog(t, T_VIEW, 0.45))
    if vp > 0:                               # договор выезжает поверх чата
        scr = P.chat_screen(H1, t, SUB_H); v = viewer(t); v.putalpha(T.rr_mask(T.SW, T.SHW, 40))
        put(scr, v, 0, 110 + (T.SHW - 110) * (1 - vp))
        fr = background().copy(); put(fr, T.card_shadow(), T.CX0 - 80, T.CY0 - 100); put(fr, S.card(scr), T.CX0, T.CY0)
    S.caps(fr, t, H1_CAPS)
    return fr


# ── сцена 3: договор клиенту → оплата ─────────────────────────────────────────
C2 = [(-1.0,) + c[1:] for c in C1] + [
      (0.20, "out", None, DOCX, "18:35", None),
      (0.80, "in", "Подписала. Оплачиваю предоплату", None, "18:44", None)]
T_NOTE = 1.4
C2_LEN = T_NOTE + 1.5
C2_CAPS = [(0.0, T_NOTE - 0.15, [("Отправляю договор клиенту", OFF, GRAPH)]),
           (T_NOTE, 99, [("Клиент оплатил", BLUE, OFF)])]

SCENES = [
    (L, P.list_frame),
    (C1_LEN, lambda t: P.chat_frame(C1, SUB_C, t, C1_CAPS)),
    (H1_LEN, harvi_frame),
    (C2_LEN, lambda t: P.chat_frame(C2, SUB_C, t, C2_CAPS, note_at=T_NOTE, zoom_from=T_NOTE, dur=C2_LEN)),
]
TOT = sum(s[0] for s in SCENES)


def at(i):
    t = i / FPS; XF = R.XF; t0 = 0.0
    for j, (dur, fn) in enumerate(SCENES):
        if t < t0 + dur or j == len(SCENES) - 1:
            fr = fn(t - t0).convert("RGB")
            if j + 1 < len(SCENES) and t > t0 + dur - XF:
                fr = xfade(fr, SCENES[j + 1][1](0).convert("RGB"), (t - (t0 + dur - XF)) / XF)
            return fr
        t0 += dur


COVER = [("Клиент просит договор —", OFF, GRAPH), ("его собирает ИИ-агент", BLUE, OFF)]


def make_cover():
    fr = background().copy()                              # кадр превью договора без плашек
    scr = P.chat_screen(H1, 3.0, SUB_H); v = viewer(3.0); v.putalpha(T.rr_mask(T.SW, T.SHW, 40)); put(scr, v, 0, 110)
    put(fr, T.card_shadow(), T.CX0 - 80, T.CY0 - 100); put(fr, S.card(scr), T.CX0, T.CY0)
    n = S.note(); put(fr, n, (W - n.width) / 2, 790 - 40)
    plates(fr, COVER, 64, 430, lambda k: 1.0)
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
    sfx += [("sfx-click.mp3", L + C1_LEN + T_VIEW, 0.25), ("sfx-click.mp3", L + C1_LEN + H1_LEN + T_NOTE, 0.3)]
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
