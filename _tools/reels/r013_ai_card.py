"""Ролик-шпаргалка «Когда нужен ИИ в бизнесе» (сценарий R013, вариант-карточка).

Без речи, как R015: заголовок + две колонки «ИИ не нужен» / «ИИ нужен», пункты появляются по очереди,
смысл и призыв — в подписи (слоган убран по решению Ивана).

    python r013_ai_card.py         # -> example-r013-ai-card/final.mp4, card.png
"""
import pathlib, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw

import r015_card as C
from r015_card import (W, H, FPS, K, GRAPH, OFF, BLUE, SURF, LINE, MUTED, BLUE_TXT, SS,
                       clamp, prog, eout, ss, eback, lerp, font, down, plate, background, put, ring)

OUT = pathlib.Path(__file__).resolve().parent / "example-r013-ai-card"
TITLE = [("Когда нужен ИИ", OFF, GRAPH), ("в бизнесе", BLUE, OFF)]
NO = ["Перенести заявку в таблицу", "Поменять статус сделки", "Напомнить об оплате",
      "Выставить счёт по шаблону", "Собрать отчёт из цифр"]
YES = ["Ответить клиенту в чате", "Разобрать голосовое", "Найти пункт в документах",
       "Ответить на отзыв", "Понять, что хочет клиент"]
X0, X_MAX, GAP = 96, 820, 24          # справа ниже 920 px — кнопки Reels (RULES §3)
CW = (X_MAX - X0 - GAP) // 2
XL, XR = X0, X0 + CW + GAP
TITLE_Y = 360
PY, HEAD_H, ROW_H, PADX = 740, 132, 110, 22   # колонки — панели: шапка + 5 строк с разделителями
PH = HEAD_H + 5 * ROW_H + 12

T_TITLE = [0.08, 0.2]
T_HEAD = [0.42, 0.52]
T_ROW = [0.85 + 0.38 * k for k in range(len(NO))]       # левый пункт; правый — через 0,14 с
DUR = round(T_ROW[-1] + 0.14 + 0.4, 2)                  # ролик кончается, как только появилось всё (Иван)


def wrap(s, f, w):
    """Перенос по словам; короткие предлоги не висят в конце строки."""
    ws, buf = [], ""
    for wd in s.split(" "):
        if buf: wd = buf + " " + wd; buf = ""
        if len(wd) <= 2 and wd.isalpha(): buf = wd; continue
        ws.append(wd)
    if buf: ws.append(buf)
    out, cur = [], ""
    for wd in ws:
        c = (cur + " " + wd).strip()
        if f.getlength(c) <= w or not cur: cur = c
        else: out.append(cur); cur = wd
    return out + [cur]


@functools.lru_cache(None)
def item(s, yes):
    """Пункт колонки: значок ✕ / ✓ и текст в 1–2 строки."""
    f = font("SemiBold", 30 * SS); r = 20; w = CW - 2 * PADX
    lines = wrap(s, f, (w - 2 * r - 16) * SS)
    im = Image.new("RGBA", (w * SS, ROW_H * SS)); d = ImageDraw.Draw(im)
    th = len(lines[:2]) * 38; ty = (ROW_H - th) / 2; cy = ROW_H / 2
    if yes:
        d.ellipse([0, (cy - r) * SS, 2 * r * SS, (cy + r) * SS], fill=BLUE + (255,))
        d.line([(9 * SS, cy * SS), (16 * SS, (cy + 7) * SS), (31 * SS, (cy - 8) * SS)], fill=OFF + (255,), width=5 * SS, joint="curve")
    else:
        d.ellipse([0, (cy - r) * SS, 2 * r * SS, (cy + r) * SS], fill=SURF + (255,), outline=(90, 95, 102, 255), width=3 * SS)
        for a, b in (((13, cy - 7), (27, cy + 7)), ((27, cy - 7), (13, cy + 7))):
            d.line([(a[0] * SS, a[1] * SS), (b[0] * SS, b[1] * SS)], fill=MUTED + (255,), width=4 * SS)
    for j, l in enumerate(lines[:2]):
        d.text(((2 * r + 16) * SS, (ty + j * 38) * SS), l, font=f, fill=(OFF if yes else (200, 203, 208)) + (255,))
    return down(im)


@functools.lru_cache(None)
def panel(yes):
    """Панель колонки: фон, шапка «ИИ НУЖЕН / НЕ НУЖЕН» с подписью, разделители строк."""
    im = Image.new("RGBA", (CW * SS, PH * SS)); d = ImageDraw.Draw(im)
    bg = (18, 38, 78) if yes else (24, 27, 31); ln = (40, 72, 130) if yes else LINE
    d.rounded_rectangle([0, 0, CW * SS - 1, PH * SS - 1], 26 * SS, fill=bg + (255,), outline=ln + (255,), width=2 * SS)
    d.rounded_rectangle([PADX * SS, 22 * SS, (CW - PADX) * SS, 78 * SS], 14 * SS, fill=(BLUE if yes else SURF) + (255,))
    d.text((CW * SS / 2, 50 * SS), "ИИ НУЖЕН" if yes else "ИИ НЕ НУЖЕН", font=font("ExtraBold", 28 * SS),
           fill=(OFF if yes else (200, 203, 208)) + (255,), anchor="mm")
    d.text((CW * SS / 2, 106 * SS), "нужно понять смысл" if yes else "хватит автоматизации",
           font=font("Medium", 24 * SS), fill=(BLUE_TXT if yes else MUTED) + (255,), anchor="mm")
    for k in range(5):
        y = (HEAD_H + k * ROW_H) * SS
        d.line([(PADX * SS, y), ((CW - PADX) * SS, y)], fill=ln + (255,), width=2 * SS)
    return down(im)


def frame(t, push=True):
    fr = background().copy()
    y = TITLE_Y
    for k, (s, bg, fg) in enumerate(TITLE):
        p = eout(prog(t, T_TITLE[k], 0.38)); sp = plate(s, 80, fg, bg)
        put(fr, sp, (X0 + X_MAX) / 2 - sp.width / 2, y + 34 * (1 - p), p); y += sp.height + 12   # по центру колонок
    for k, yes in enumerate((False, True)):
        p = eout(prog(t, T_HEAD[k], 0.35)); put(fr, panel(yes), XR if yes else XL, PY + 30 * (1 - p), p)
    for k in range(len(NO)):
        ry = PY + HEAD_H + k * ROW_H
        for yes, ta, s in ((False, T_ROW[k], NO[k]), (True, T_ROW[k] + 0.14, YES[k])):
            p = eback(prog(t, ta, 0.3)); a = clamp(prog(t, ta, 0.18))
            x = (XR if yes else XL) + PADX
            put(fr, item(s, yes), x + 22 * (1 - clamp(p)) * (1 if yes else -1), ry, a)
            if yes:
                r = prog(t, ta, 0.4)
                if 0 < r < 1:
                    rg = ring(16 + 28 * eout(r), 1 - r); put(fr, rg, x + 20 - rg.width / 2, ry + ROW_H / 2 - rg.height / 2)
    return np.asarray(fr.convert("RGB"))


def main():
    OUT.mkdir(exist_ok=True)
    card = Image.fromarray(frame(DUR, push=False)); card.save(OUT / "card.png")
    sfx = [("sfx-pop.mp3", T_TITLE[0], 0.14)] + [("sfx-pop.mp3", t, 0.1) for t in T_ROW] + \
          [("sfx-click.mp3", t + 0.14, 0.2) for t in T_ROW]
    ins = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-t", str(DUR), "-i", "anullsrc=r=48000:cl=stereo"]
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
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    cover = np.asarray(card.convert("RGB"))
    for i in range(int(DUR * FPS)):
        fr = cover if i == 0 else frame(i / FPS)
        p.stdin.write(np.ascontiguousarray(fr, np.uint8).tobytes())
    p.stdin.close(); p.wait(); print("done", OUT / "final.mp4")


if __name__ == "__main__":
    main()
