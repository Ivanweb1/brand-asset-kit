"""Монтаж-лист ролика: куски исходника без пауз и слов-паразитов + слова для субтитров и синхронизации графики.

Данные лежат в $REEL_WORK/edit.json (пример — example/edit.json):
  src0      — с какой секунды оригинала начинается work/src.mp4
  segments  — [начало, конец] в секундах оригинала, только чистая речь
  words     — [слово как в субтитрах, время начала в оригинале]
"""
import json, os, subprocess, numpy as np, soundfile as sf
from reel import WORK

FPS = 30
_D = json.load(open(os.path.join(WORK, "edit.json")))
SRC0 = float(_D["src0"])
SEGS = [tuple(s) for s in _D["segments"]]

FR = [(round((a - SRC0) * FPS), round((b - SRC0) * FPS)) for a, b in SEGS]
OUT_START = np.cumsum([0] + [b - a for a, b in FR]).tolist()
NFRAMES = OUT_START[-1]
DUR = NFRAMES / FPS


def seg_of(i):
    for k in range(len(FR)):
        if OUT_START[k] <= i < OUT_START[k + 1]: return k
    return len(FR) - 1


def src_frame(i):
    k = seg_of(i); return FR[k][0] + (i - OUT_START[k]), k


def out_time(t_src):
    """Время оригинала -> время в смонтированном ролике (None, если вырезано)."""
    for k, (a, b) in enumerate(FR):
        fa, fb = a / FPS + SRC0, b / FPS + SRC0
        if fa - 0.05 <= t_src < fb: return OUT_START[k] / FPS + max(0, t_src - fa)
    return None


def seg_t(k): return OUT_START[k] / FPS


WORDS = []
for w, ts in _D["words"]:
    t = out_time(ts + 0.02)
    if t is None: t = out_time(ts + 0.1)
    WORDS.append((w, t))
_missing = [w for w, t in WORDS if t is None]
assert not _missing, f"слова попали в вырезанные паузы: {_missing}"


def wt(i): return WORDS[i][1]


def build_audio(path=None):
    path = path or os.path.join(WORK, "edit_audio.wav")
    a, sr = sf.read(os.path.join(WORK, "audio48.wav"), dtype="float32")
    parts = []
    for fa, fb in FR:
        s, e = int((fa / FPS + SRC0) * sr), int((fb / FPS + SRC0) * sr)
        p = a[s:e].copy(); n = int(0.006 * sr)
        p[:n] *= np.linspace(0, 1, n); p[-n:] *= np.linspace(1, 0, n)
        parts.append(p)
    raw = os.path.join(WORK, "edit_audio_raw.wav")
    sf.write(raw, np.concatenate(parts), sr)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af",
                    "highpass=f=70,loudnorm=I=-14:LRA=7:TP=-1.5,aresample=48000", "-ac", "2", path], check=True)
    return path


if __name__ == "__main__":
    print(f"кадров {NFRAMES}, длительность {DUR:.2f} с")
    for i, (w, t) in enumerate(WORDS): print(f"{i:3d} {t:6.2f} {w}")
