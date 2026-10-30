"""Ролик «КП через Claude» (сценарий R018).

Аватар HeyGen, поверх сыплются сообщения клиентов «пришлите КП» → «Так, где мой ИИ-агент?» →
экран Claude (как в R017): задача, файлы прайс / бриф / прошлое КП, отправка → листается готовое КП
(КП Ивана «Автоотчёты» для FenixSMM, показ согласован Иваном) → аватар: призыв «КП».

Исходники (не публикуются) — work/r018/:
    hook.mp4      — HeyGen «Так, где мой ИИ-агент?», id 6f52536d654d4a8fbbafa744ea230c16
    cta.mp4       — HeyGen «Напишите «КП» в комментариях — пришлю промпт» (пока нет — ролик без финала)
    claude-app.png, slide01…slide09.png (страницы KP-avtootchety-FenixSMM.pdf)

    python r018_kp.py              # -> example-r018-kp/final.mp4, cover.jpg
    python r018_kp.py peek 1 3 6   # кадры work/r018/peek_<t>.png
"""
import os, sys, pathlib, subprocess, functools
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r017_presentation as Q
R = Q.R
from r014_avito import (W, H, FPS, GRAPH, OFF, BLUE, SS, K, clamp, prog, eout, ss, eback, lerp,
                        put, plates, font, down, Clip, avatar_frame, xfade)

WORK = pathlib.Path(os.environ.get("R018_WORK", K / "work" / "r018"))
OUT = pathlib.Path(__file__).resolve().parent / "example-r018-kp"
Q.WORK = WORK; R.CLIP_DIR = WORK

# ── экран Claude: переопределяем содержимое R017 ─────────────────────────────
Q.PROMPT = ("Сделай КП для SMM-агентства по брифу: автоотчёты по рекламе каждое утро. "
            "Цены бери из прайса, оформление — как в прошлом КП")
Q.SLIDES = [1, 2, 3, 7, 8]; Q.TOTAL_SLIDES = 9
Q.CH = Q.T_VIEW + 0.1 + len(Q.SLIDES) * Q.T_SLIDE
Q.CAPS = [(0.3, 2.85, [("Пишу задачу", OFF, GRAPH)]),
          (2.95, 4.55, [("Прикладываю прайс", OFF, GRAPH), ("бриф и прошлое КП", BLUE, OFF)]),
          (4.75, Q.CH - 0.25, [("Claude собрал КП", OFF, GRAPH)])]
FILES = [("прайс", "XLSX", (33, 115, 70)), ("бриф клиента", "DOCX", (43, 87, 154)), ("КП прошлое", "PDF", (200, 60, 50))]


@functools.lru_cache(None)
def file_card(k):
    """Вложение-файл, как в Claude: имя, тип и цветная метка."""
    name, ext, col = FILES[k]; s = Q.TILE * SS
    im = Image.new("RGBA", (s, s)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, s - 1, s - 1], 18 * SS, fill=(250, 249, 247, 255), outline=Q.LINE + (255,), width=2 * SS)
    f = Q.ui_font(17); y = 16 * SS
    for ln in Q.wrap(name, f, Q.TILE - 30)[:2]:
        d.text((15 * SS, y), ln, font=f, fill=Q.TXT + (255,)); y += 24 * SS
    bf = Q.ui_font(14); bw = bf.getlength(ext) + 18 * SS
    d.rounded_rectangle([15 * SS, s - 40 * SS, 15 * SS + bw, s - 14 * SS], 7 * SS, fill=col + (255,))
    d.text((15 * SS + 9 * SS, s - 27 * SS), ext, font=bf, fill=(255, 255, 255, 255), anchor="lm")
    return down(im)


Q.tile = file_card
Q.BLUR_TEXT = True                 # промпт печатается, но размыт: его выдают по слову «КП» (решение Ивана)

# ── вступление: поток сообщений над аватаром ─────────────────────────────────
PRE = 1.4                          # до начала речи: стоп-кадр с наездом, сообщения уже сыплются
HOOK_SUB = [[("Так,", .13)], [("где", .58), ("мой", .74), ("ИИ-агент?", 1.0)]]
MSGS = [  # (время, отправитель, текст)
    (0.10, "Ольга · Стройдвор", "Здравствуйте! Пришлите, пожалуйста, КП"),
    (0.45, "Андрей", "Можно коммерческое на 3 позиции?"),
    (0.80, "Марина, салон", "Ждём КП до завтра!"),
    (1.10, "Денис · логистика", "Добрый день, КП готово?"),
    (1.40, "Ирина", "И нам КП, пожалуйста"),
]
COUNT = [(0.10, 3), (0.45, 5), (0.80, 7), (1.10, 9), (1.40, 12)]
AV_COL = [(229, 115, 115), (100, 181, 246), (129, 199, 132), (255, 183, 77), (186, 104, 200)]
NW, NH, NX, NY = 800, 118, 140, 430


@functools.lru_cache(None)
def notif(k):
    _, who, text = MSGS[k]; w, h = NW * SS, NH * SS
    im = Image.new("RGBA", (w, h)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], 32 * SS, fill=(36, 37, 41, 255), outline=(255, 255, 255, 30), width=2 * SS)
    r = 30 * SS; cx, cy = 28 * SS + r, h / 2
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=AV_COL[k] + (255,))
    d.text((cx, cy + 2 * SS), who[0], font=font("Bold", 28 * SS), fill=(255, 255, 255, 255), anchor="mm")
    tx = cx + r + 22 * SS
    d.text((tx, 32 * SS), who, font=font("Bold", 28 * SS), fill=(250, 250, 250, 255), anchor="lm")
    d.text((w - 28 * SS, 32 * SS), "сейчас", font=font("Medium", 22 * SS), fill=(150, 150, 155, 255), anchor="rm")
    d.text((tx, 78 * SS), text, font=font("Medium", 28 * SS), fill=(225, 225, 228, 255), anchor="lm")
    return down(im)


@functools.lru_cache(None)
def _counter(n):
    s = f"{n} новых сообщений"; f = font("ExtraBold", 34 * SS); tw = f.getlength(s)
    w, h = int(tw + 70 * SS), 64 * SS; im = Image.new("RGBA", (w, h)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], h // 2, fill=BLUE + (255,))
    d.text((w / 2, h / 2), s, font=f, fill=OFF + (255,), anchor="mm")
    return down(im)


def messages(fr, t, fade=1.0):
    shown = [k for k, (ta, _, _) in enumerate(MSGS) if t >= ta]
    if not shown: return
    n = max(c for ta, c in COUNT if t >= ta); cp = _counter(n)
    put(fr, cp, (W - cp.width) / 2, NY - 82, fade)
    for slot, k in enumerate(reversed(shown)):       # новое сверху, старые сдвигаются вниз
        if slot > 3: break
        p = eback(prog(t, MSGS[k][0], 0.35))
        # позиция слота плавно следует за появлением нового сверху
        newer = [j for j in shown if j > k]
        y = NY + sum(eout(prog(t, MSGS[j][0], 0.3)) for j in newer) * (NH + 14)
        a = clamp(p * 1.5) * fade
        if slot == 3: a *= 1 - prog(t, MSGS[shown[-1]][0], 0.12)   # четвёртое быстро уходит
        if slot == 0:
            sc = lerp(0.85, 1.0, p); sp = notif(k).resize((int(NW * sc), int(NH * sc)), Image.LANCZOS)
            put(fr, sp, NX + (NW - sp.width) / 2, NY - 40 * (1 - eout(p)), a)
        else:
            put(fr, notif(k), NX, y, a)


def hook_frame(clip, t, dur):
    """t — время от начала ролика; до PRE — стоп-кадр с лёгким наездом."""
    tc = max(0.0, t - PRE); src = clip.at(int(tc * FPS))
    R.FACE_AT = (540, 1010)                     # лицо ниже: верх кадра под сообщения
    fr = avatar_frame(src, t, dur, [[(w, ts + PRE) for w, ts in ln] for ln in HOOK_SUB], [])
    R.FACE_AT = (540, 870)
    fr = fr.convert("RGBA"); messages(fr, t, 1 - ss(prog(t, dur - 0.35, 0.3)))
    return fr.convert("RGB")


COVER = [("Клиенты ждут КП", OFF, GRAPH), ("Где мой ИИ-агент?", BLUE, OFF)]


def make_cover():
    src = Clip("hook").at(int(1.9 * FPS)); z = 1.4
    x0 = clamp(R.FACE[0] - 540 / z, 0, W - W / z); y0 = clamp(R.FACE[1] - 1190 / z, 0, H - H / z)
    fr = src.transform((W, H), Image.AFFINE, (1 / z, 0, x0, 0, 1 / z, y0), Image.BICUBIC).convert("RGBA")
    plates(fr, COVER, 84, 560, lambda k: 1.0)
    fr.convert("RGB").save(OUT / "cover.jpg", quality=95)


def clen(name):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 str(WORK / f"{name}.mp4")], capture_output=True, text=True).stdout)


def main(peek=None):
    OUT.mkdir(exist_ok=True)
    has_cta = (WORK / "cta.mp4").exists()
    A = PRE + clen("hook"); CH = Q.CH
    cta = None
    if has_cta:
        import json
        cj = json.load(open(WORK / "cta.json", encoding="utf-8"))   # тайминги слов призыва
        Bo = clen("cta") + 0.4; cta = Clip("cta")
    else:
        Bo = 0.0
    TOT = A + CH + Bo
    hook = Clip("hook"); XF = R.XF

    def at(i):
        t = i / FPS
        if t < A:
            fr = hook_frame(hook, t, A)
            if t > A - XF: fr = xfade(fr, Q.frame(0), (t - (A - XF)) / XF)
        elif t < A + CH or not has_cta:
            fr = Q.frame(min(t - A, CH))
        else:
            tb = t - A - CH
            subs = [[tuple(w) for w in ln] for ln in cj["sub"]]
            pl = [(cj["pl"][0], 99, [("Напишите в комментариях", OFF, GRAPH), ("«КП»", BLUE, OFF)], cj["pl"])]
            fr = avatar_frame(cta.at(int(tb * FPS)), tb, Bo, subs, pl, cj["pl"][1])
            if tb < XF: fr = xfade(Q.frame(CH), fr, tb / XF)
        return fr

    if peek:
        for i in range(int(max(peek) * FPS) + 1):
            fr = at(i)
            for s in peek:
                if int(s * FPS) == i: fr.save(WORK / f"peek_{s}.png")
        return
    sfx = [("sfx-pop.mp3", ta, 0.22) for ta, _, _ in MSGS]
    sfx += [("sfx-click.mp3", A + Q.T_CLICK_PLUS, 0.25), ("sfx-click.mp3", A + Q.T_SEND, 0.25)]
    sfx += [("sfx-pop.mp3", A + ta, 0.12) for ta in Q.T_REFS]
    sfx += [("sfx-pop.mp3", A + Q.T_VIEW + 0.1 + k * Q.T_SLIDE, 0.1) for k in range(1, len(Q.SLIDES))]
    ins = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-t", f"{TOT:.3f}", "-i", "anullsrc=r=48000:cl=stereo", "-i", str(WORK / "hook.mp4")]
    pre = int(PRE * 1000)
    fl = [f"[2:a]loudnorm=I=-14:TP=-1.5,aformat=sample_rates=48000:channel_layouts=stereo,adelay={pre}|{pre}[v0]"]
    labs = ["[v0]"]; base = 3
    if has_cta:
        ins += ["-i", str(WORK / "cta.mp4")]; oms = int((A + CH) * 1000)
        fl.append(f"[3:a]loudnorm=I=-14:TP=-1.5,aformat=sample_rates=48000:channel_layouts=stereo,adelay={oms}|{oms}[v1]")
        labs.append("[v1]"); base = 4
    for j, (f, t, v) in enumerate(sfx):
        ins += ["-i", str(K / "11_MOTION" / f)]; ms = int(t * 1000)
        fl.append(f"[{j + base}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={v},adelay={ms}|{ms}[s{j}]")
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
    p.stdin.close(); p.wait(); print("done", OUT / "final.mp4", f"{TOT:.2f} s", "" if has_cta else "(без финала)")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "peek":
        main([float(s) for s in sys.argv[2:]])
    else:
        main()
