"""Ролик «Артём, с этим — к Харви» — ИИ-агент отвечает сотрудникам по регламентам (сценарий R023).

Аватар, сверху сыплются вопросы стажёра Артёма (как R018) → «Артём, с этим — к Харви.» →
на словах «ИИ-агент…» сразу чат Telegram Артёма с Харви (из r019_harvi.py), голос звучит поверх:
вопрос → ответ со ссылкой на пункт регламента → второй вопрос → ответ со ссылкой →
аватар: «Хотите такого агента? Напишите «РЕГЛАМЕНТ» в директ.»

Темп — RULES §1: всё параллельно, экран идёт под голос и кончается сразу после фразы.
Документы и пункты постановочные; портрет стажёра — ИИ-портрет из R018.

Исходники (не публикуются) — work/r023/: heygen-full.mp4 → hook.mp4, cta.mp4; clip.json — тайминги.

    python r023_regulations.py screen 1 2 3   # кадры экрана work/r023/screen_<t>.png
    python r023_regulations.py peek 1 5 9     # кадры ролика work/r023/peek_<t>.png
    python r023_regulations.py                # -> example-r023-regulations/final.mp4, cover.jpg
"""
import os, sys, json, pathlib, functools, subprocess
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r019_harvi as T
from r019_harvi import (SW, TXT, ui, wrap, checks, top_layer, bottom_layer, chat_bg, card_mask, card_shadow,
                        CX0, CY0, CW, CHH, SHW, MSG_Y0, MSG_Y1, INB, INMUTED, OUTB, OUTMUTED)
import r014_avito as R
from r014_avito import (W, H, FPS, GRAPH, OFF, BLUE, clamp, prog, eout, ss, eback, lerp,
                        put, plates, background, Clip, avatar_frame, xfade)
import r018_kp as P                          # поток сообщений над аватаром — как в R018

K = T.K
WORK = pathlib.Path(os.environ.get("R023_WORK", K / "work" / "r023"))
OUT = pathlib.Path(__file__).resolve().parent / "example-r023-regulations"
R.CLIP_DIR = WORK; P.WORK = K / "work" / "r018"      # портреты отправителей — из R018

# ── вопросы стажёра над аватаром ─────────────────────────────────────────────
P.PRE = 0.0
P.MSGS = [
    (0.05, "Артём · стажёр", "Где шаблон договора?", "igor"),
    (0.35, "Артём · стажёр", "Как оформить возврат клиенту?", "igor"),
    (0.65, "Артём · стажёр", "А скидку 15% можно дать?", "igor"),
    (0.95, "Артём · стажёр", "Кому отдать счёт на согласование?", "igor"),
]
P.COUNT = [(0.05, 1), (0.35, 2), (0.65, 3), (0.95, 4)]

# ── аватар (по расшифровке, work/r023/clip.json) ──────────────────────────────
P.HOOK_SUB = [[("Артём,", .35), ("с", .9), ("этим", 1.0)], [("—", 1.3), ("к", 1.3), ("Харви.", 1.4)],
              [("ИИ-агент", 2.2), ("отвечает", 2.8)], [("по", 3.3), ("вашим", 3.4), ("регламентам", 3.7)],
              [("и", 4.6), ("сразу", 4.7), ("даёт", 5.0)], [("ссылку", 5.3), ("на", 5.7), ("документ.", 5.8)]]
T_BRIDGE = 2.15
CTA_SUB = [[("Хотите", .1), ("такого", .4), ("агента?", .7)], [("Напишите", 1.3), ("«РЕГЛАМЕНТ»", 1.7)], [("в", 2.4), ("директ.", 2.5)]]
CTA_PL_AT = [.1, 1.7]; T_PUSH_CTA = 1.7; HOLD = 0.45
COVER_T = 0.6
COVER = [("Стажёр снова", OFF, GRAPH), ("с вопросами?", OFF, GRAPH), ("Это к Харви", BLUE, OFF)]
if (WORK / "clip.json").exists():
    _c = json.load(open(WORK / "clip.json", encoding="utf-8"))
    P.HOOK_SUB = [[tuple(w) for w in ln] for ln in _c["hook_sub"]]
    CTA_SUB = [[tuple(w) for w in ln] for ln in _c["cta_sub"]]
    T_BRIDGE = _c["bridge"]; CTA_PL_AT = _c["cta_pl"]; T_PUSH_CTA = _c.get("push_cta", CTA_PL_AT[1])
    COVER_T = _c.get("cover_t", COVER_T)
CTA_PL = [(CTA_PL_AT[0], 99, [("Хотите такого агента?", OFF, GRAPH), ("«РЕГЛАМЕНТ» в директ", BLUE, OFF)], CTA_PL_AT)]

# ── экран: чат Артёма с Харви ────────────────────────────────────────────────
CHAT = [  # (время, кто, текст, ссылка (документ, пункт) | None)
    (0.1, "me", "Как оформить возврат клиенту?", None),
    (0.85, "bot", "1. Заявление клиента по шаблону.\n2. Согласовать с руководителем отдела.\n3. Вернуть деньги в течение 10 дней.",
     ("Регламент возвратов", "п. 4.2")),
    (1.9, "me", "А скидку 15% можно?", None),
    (2.6, "bot", "Больше 10% — только с согласования руководителя продаж.", ("Положение о скидках", "п. 2.1")),
]
WRITING = [(0.35, 0.85), (2.15, 2.6)]
CH_MIN = 3.6
CAPS = [(0.1, 1.75, [("Отвечает по вашим", OFF, GRAPH), ("документам", BLUE, OFF)]),
        (1.85, 99, [("Со ссылкой", OFF, GRAPH), ("на пункт", BLUE, OFF)])]
PAD, RAD = 34, 38; LINKC = (110, 175, 255)


@functools.lru_cache(None)
def bubble(k):
    _, who, text, link = CHAT[k]
    f = ui(40, False); lines = [l for para in text.split("\n") for l in wrap(para, f, 760)]
    tw = max(f.getlength(l) for l in lines); lh = 54; lk = 0
    if link: lk = 118; tw = max(tw, 600)
    tw = max(tw, f.getlength(lines[-1]) + (130 if who == "me" else 100))
    bw, bh = int(tw + 2 * PAD), int(len(lines) * lh + lk + 2 * 22 + 30)
    im = Image.new("RGBA", (SW, bh)); d = ImageDraw.Draw(im)
    x0 = SW - 24 - bw if who == "me" else 24
    d.rounded_rectangle([x0, 0, x0 + bw, bh], RAD, fill=(OUTB if who == "me" else INB) + (255,))
    y = 22
    for l in lines: d.text((x0 + PAD, y + lh / 2), l, font=f, fill=TXT, anchor="lm"); y += lh
    if link:                                     # превью ссылки на документ, как в Telegram
        y += 10; d.rounded_rectangle([x0 + 18, y, x0 + bw - 18, y + 100], 16, fill=(44, 60, 82, 255))
        d.rectangle([x0 + 18, y, x0 + 25, y + 100], fill=LINKC)
        T.doc_icon(d, x0 + 70, y + 50, 30)
        d.text((x0 + 116, y + 32), link[0], font=ui(36), fill=LINKC, anchor="lm")
        d.text((x0 + 116, y + 72), link[1] + " · открыть документ", font=ui(30, False), fill=(200, 210, 222), anchor="lm")
    mut = OUTMUTED if who == "me" else INMUTED
    tx = x0 + bw - PAD - ui(30, False).getlength("10:24") - (44 if who == "me" else 0)
    d.text((tx, bh - 30), "10:24", font=ui(30, False), fill=mut, anchor="lm")
    if who == "me": checks(d, x0 + bw - PAD - 36, bh - 28, mut)
    return im


def screen(t):
    sub = "бот"
    for a, b in WRITING:
        if a <= t < b: sub = "печатает" + "." * (int((t - a) * 4) % 4)
    im = chat_bg().copy(); items, y, gap = [], 30, 16
    for k, c in enumerate(CHAT):
        if t < c[0]: break
        b = bubble(k); items.append((b, y, prog(t, c[0], 0.3))); y += lerp(0, b.height + gap, eout(prog(t, c[0], 0.26)))
    shift = max(0, y - gap - (MSG_Y1 - MSG_Y0 - 10))
    for spr, yy, p in items:
        if p >= 1: put(im, spr, 0, MSG_Y0 + yy - shift)
        else:
            s = lerp(0.9, 1.0, eback(p)); sp = spr.resize((int(spr.width * s), max(1, int(spr.height * s))), Image.BICUBIC)
            put(im, sp, (SW - sp.width) / 2, MSG_Y0 + yy - shift + (spr.height - sp.height) / 2 + 24 * (1 - eout(p)), eout(p * 1.6))
    im.alpha_composite(top_layer(sub), (0, 0))
    im.alpha_composite(bottom_layer(), (0, SHW - bottom_layer().height))
    return im


def screen_frame(t, ch):
    fr = background().copy()
    wp = eout(prog(t, 0, 0.4)); y = CY0 + 520 * (1 - wp)
    c = screen(t).resize((CW, CHH), Image.LANCZOS); c.putalpha(card_mask())
    ImageDraw.Draw(c).rounded_rectangle([0, 0, CW - 1, CHH - 1], 44, outline=(255, 255, 255, 40), width=2)
    put(fr, card_shadow(), CX0 - 80, y - 100, wp); put(fr, c, CX0, y, wp)
    for a, b, rows in CAPS:
        b = min(b, ch - 0.15)
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
    plates(fr, COVER, 84, 520, lambda k: 1.0)
    fr.convert("RGB").save(OUT / "cover.jpg", quality=95)


def main(peek=None, screen_only=None):
    WORK.mkdir(parents=True, exist_ok=True)
    if screen_only:
        for s in screen_only: screen_frame(s, CH_MIN).save(WORK / f"screen_{s}.png")
        return
    OUT.mkdir(exist_ok=True)
    A = T_BRIDGE; CH = max(CH_MIN, clen("hook") - A + 0.05)      # экран — ровно под фразу про агента
    Bo = clen("cta") + HOLD; TOT = A + CH + Bo; XF = R.XF
    hook, cta = Clip("hook"), Clip("cta"); last = int((Bo - HOLD) * FPS) - 1

    def at(i):
        t = i / FPS
        if t < A:
            fr = P.hook_frame(hook, t, A)
            if t > A - XF: fr = xfade(fr, screen_frame(0, CH), (t - (A - XF)) / XF)
        elif t < A + CH:
            fr = screen_frame(t - A, CH)
        else:
            tb = t - A - CH
            fr = avatar_frame(cta.at(min(int(tb * FPS), last)), tb, Bo, CTA_SUB, CTA_PL, T_PUSH_CTA)
            if tb < XF: fr = xfade(screen_frame(CH, CH), fr, tb / XF)
        return fr

    if peek:
        for i in range(int(max(peek) * FPS) + 1):
            fr = at(i)
            for s in peek:
                if int(s * FPS) == i: fr.save(WORK / f"peek_{s}.png")
        return
    sfx = [("sfx-pop.mp3", m[0], 0.2) for m in P.MSGS] + [("sfx-pop.mp3", A + c[0], 0.14) for c in CHAT]
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
    if sys.argv[1:2] == ["screen"]:
        main(screen_only=[float(s) for s in sys.argv[2:]])
    elif sys.argv[1:2] == ["peek"]:
        main([float(s) for s in sys.argv[2:]])
    else:
        main()
