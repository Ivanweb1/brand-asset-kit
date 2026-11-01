"""R014 v8 — «ИИ-агент на Авито ночью» в новом темпе (RULES §1: параллельно, без тишины).

Аватар ~2,5 с («Клиент написал на Авито в 23:40») → сразу чат Авито, фраза «ИИ-агент проконсультировал его
и поставил бронь» звучит поверх переписки; события чата идут под слова → уведомление хозяину → призыв.
Рисование чата — r014_avito.py, здесь только новый таймлайн и сборка.

Исходник — запись HeyGen Avatar 6 `0633c7c018ec455eb732e20191bc2b48` (work/r014v2/src.mp4), нарезка в work/r014v3/:
    intro.mp4 = 0,25–2,6 + 2,97–5,0 + 5,15–6,05 (паузы подрезаны), outro.mp4 = с 6,32 с.

    python r014_avito_v3.py              # -> example-r014-avito/final.mp4, cover.jpg
    python r014_avito_v3.py peek 1 3 5   # кадры work/r014v3/peek_<t>.png
"""
import os, sys, pathlib, subprocess
import numpy as np
from PIL import Image

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r014_avito as M
from r014_avito import W, H, FPS, OFF, GRAPH, BLUE, Clip, avatar_frame, xfade

M.CLIP_DIR = M.K / "work" / "r014v3"
D = 0.25                                    # срезано начало записи до первого слова (тишина 0,34 с)
OUT = M.OUT

# ── аватар: слова после нарезки ───────────────────────────────────────────────
A = 2.45 - D                                    # конец «23:40» — дальше экран
INTRO_SUB = [[(w, ts - D) for w, ts in ln] for ln in [[("Клиент", .34), ("написал", .59), ("на", .95), ("Авито", 1.11)], [("в", 1.47), ("23:40.", 1.63)]]]
OUTRO_SUB = [[("Напишите", .05), ("в", .38), ("директ", .5)], [("«ЗАЯВКА» —", .9), ("покажу,", 1.6)],
             [("как", 1.85), ("настроить", 2.09), ("такой", 2.61), ("у", 2.81), ("вас.", 2.93)]]
OUTRO_PL = [(.05, 99, [("Напишите в директ", OFF, GRAPH), ("«ЗАЯВКА»", BLUE, OFF)], [.05, .9])]
T_PUSH_CTA = .9

# ── чат: время = время ролика; события под слова «ИИ-агент» (2,64) … «бронь» (5,08) ─
M.CHAT = [
    ("me", M.CHAT[0][1], 2.6 - D, "23:40"),
    ("ai", M.CHAT[1][1], 3.1 - D, "23:40"),
    ("me", M.CHAT[2][1], 4.2 - D, "23:41"),
    ("ai", M.CHAT[3][1], 4.8 - D, "23:41"),
]
M.TYPE = [(2.25 - D, 2.55 - D, 0), (3.85 - D, 4.15 - D, 2)]
M.WRITING = [(2.7 - D, 3.05 - D), (4.3 - D, 4.75 - D)]
M.T_MIN41 = 3.7 - D
M.T_WIN = 2.2 - D
M.T_NOTE_IN, M.T_NOTE_OUT = 5.0 - D, 99
M.CAPS = [(2.45 - D, 3.55 - D, [("23:40. Пишет клиент", OFF, GRAPH)]),
          (3.65 - D, 99, [("Отвечает и бронирует", OFF, GRAPH), ("ИИ-агент", BLUE, OFF)])]
CH_END = 5.62 - D                               # конец чата — сразу призыв (голос вступления кончается на 5,39)


def clen(name):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 str(M.CLIP_DIR / f"{name}.mp4")], capture_output=True, text=True).stdout)


def main(peek=None):
    OUT.mkdir(exist_ok=True)
    Bo = clen("outro") + 0.3; TOT = CH_END + Bo; XF = M.XF
    intro, outro = Clip("intro"), Clip("outro"); last = int(clen("outro") * FPS) - 1

    def at(i):
        t = i / FPS
        if t < A:
            fr = avatar_frame(intro.at(i), t, A, INTRO_SUB, [])
            if t > A - XF: fr = xfade(fr, Image.fromarray(M.frame(A)), (t - (A - XF)) / XF)
        elif t < CH_END:
            fr = Image.fromarray(M.frame(t))
        else:
            tb = t - CH_END
            fr = avatar_frame(outro.at(min(int(tb * FPS), last)), tb, Bo, OUTRO_SUB, OUTRO_PL, T_PUSH_CTA)
            if tb < XF: fr = xfade(Image.fromarray(M.frame(CH_END)), fr, tb / XF)
        return fr

    if peek:
        for i in range(int(max(peek) * FPS) + 1):
            fr = at(i)
            for s in peek:
                if int(s * FPS) == i: fr.save(M.CLIP_DIR / f"peek_{s}.png")
        return
    sfx = [("sfx-click.mp3" if who == "me" else "sfx-pop.mp3", ta, 0.2 if who == "me" else 0.16) for who, _, ta, _ in M.CHAT]
    sfx += [("sfx-pop.mp3", M.T_NOTE_IN, 0.2)]
    ins = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-t", f"{TOT:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
           "-i", str(M.CLIP_DIR / "intro.mp4"), "-i", str(M.CLIP_DIR / "outro.mp4")]
    oms = int(CH_END * 1000)
    fl = ["[2:a]loudnorm=I=-14:TP=-1.5,aformat=sample_rates=48000:channel_layouts=stereo[v0]",
          f"[3:a]loudnorm=I=-14:TP=-1.5,aformat=sample_rates=48000:channel_layouts=stereo,adelay={oms}|{oms}[v1]"]
    labs = ["[v0]", "[v1]"]
    for j, (f, t, v) in enumerate(sfx):
        ins += ["-i", str(M.K / "11_MOTION" / f)]; ms = int(t * 1000)
        fl.append(f"[{j + 4}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={v},adelay={ms}|{ms}[s{j}]")
        labs.append(f"[s{j}]")
    fl.append(f"[1:a]{''.join(labs)}amix=inputs={1 + len(labs)}:normalize=0:duration=first,alimiter=limit=0.95[a]")
    cmd = ["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fl), "-map", "0:v", "-map", "[a]",
           "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-profile:v", "high", "-pix_fmt", "yuv420p",
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(OUT / "final.mp4")]
    cover = OUT / "cover.jpg"                # обложка прежняя (утверждена в v7)
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(round(TOT * FPS))):
        fr = Image.open(cover).convert("RGB").resize((W, H)) if i == 0 and cover.exists() else at(i)
        p.stdin.write(np.ascontiguousarray(np.asarray(fr.convert("RGB")), np.uint8).tobytes())
    p.stdin.close(); p.wait(); print("done", OUT / "final.mp4", f"{TOT:.2f} s")


if __name__ == "__main__":
    if sys.argv[1:2] == ["peek"]:
        main([float(s) for s in sys.argv[2:]])
    else:
        main()
