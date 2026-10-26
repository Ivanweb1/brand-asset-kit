#!/usr/bin/env python3
"""Подготовка ролика к монтажу.

    python3 prepare.py исходник.mov --start 5 --end 30 --work work
    python3 prepare.py heygen.mp4 --sharpen 0.5 --work work     # мягкий исходник (аватар 1080p/720p)

Делает в рабочей папке:
  src.mp4      — кусок исходника 1440×2560, 30 к/с, цвет приведён к SDR (HDR с iPhone тонмапится)
  audio48.wav  — весь звук, моно 48 кГц
  words.json   — расшифровка со временем слов (через _tools/transcribe)
  edit.json    — ЧЕРНОВИК монтаж-листа: речь без пауз ≥ 0.15 с и без слов-паразитов.
                 Его нужно проверить глазами: орфография, заглавные, знаки препинания, повторы и оговорки.
"""
import argparse, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FILLERS = {"а", "э", "ээ", "эээ", "м", "мм", "ммм", "ну", "вот", "как бы", "типа", "это самое"}


def is_hdr(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=color_transfer",
                          "-of", "csv=p=0", path], capture_output=True, text=True).stdout.strip()
    return out in ("arib-std-b67", "smpte2084")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("media"); ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=None); ap.add_argument("--work", default="work")
    ap.add_argument("--sharpen", type=float, default=0.0,
                    help="резкость для исходников ниже 4K: 0.5 для 1080p, 0.7 для 720p")
    a = ap.parse_args()
    os.makedirs(a.work, exist_ok=True)
    src0 = max(0.0, a.start - 0.3)
    dur = [] if a.end is None else ["-t", f"{a.end + 0.3 - src0:.3f}"]
    fit = "scale=1440:2560:force_original_aspect_ratio=increase:flags=lanczos,crop=1440:2560"
    sharp = f"unsharp=5:5:{a.sharpen}:5:5:0," if a.sharpen > 0 else ""
    tone = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,"
            "zscale=t=bt709:m=bt709:r=tv,format=yuv420p,") if is_hdr(a.media) else "format=yuv420p,"
    vf = f"{fit},{tone}{sharp}eq=contrast=1.05:saturation=1.06,fps=30,setsar=1"
    print("1/4 видео…", file=sys.stderr)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{src0:.3f}", *dur, "-i", a.media, "-map", "0:v:0", "-vf", vf,
                    "-c:v", "libx264", "-crf", "10", "-preset", "fast", "-pix_fmt", "yuv420p",
                    os.path.join(a.work, "src.mp4")], check=True)
    print("2/4 звук…", file=sys.stderr)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.media, "-map", "0:a:0", "-ac", "1", "-ar", "48000",
                    os.path.join(a.work, "audio48.wav")], check=True)
    print("3/4 расшифровка…", file=sys.stderr)
    wav = os.path.join(a.work, "speech.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.media, "-map", "0:a:0", "-c:a", "pcm_s16le", wav], check=True)
    subprocess.run([sys.executable, os.path.join(HERE, "..", "transcribe", "transcribe.py"), wav], check=True)
    tr = json.load(open(os.path.join(a.work, "speech.words.json")))
    print("4/4 черновик монтаж-листа…", file=sys.stderr)
    end = a.end if a.end is not None else 1e9
    segs, words = [], []
    for ph in tr["phrases"]:
        if ph["end"] < a.start or ph["start"] > end: continue
        if ph["text"].strip().lower() in FILLERS: continue          # фраза целиком из «а», «ну»…
        segs.append([round(ph["start"] - 0.05, 2), round(ph["end"] + 0.07, 2)])
    for w in tr["words"]:
        if a.start - 0.1 <= w["start"] <= end and w["word"].lower() not in FILLERS:
            words.append([w["word"], w["start"]])
    json.dump({"src0": src0, "segments": segs, "words": words,
               "note": "ЧЕРНОВИК: проверить орфографию/пунктуацию слов, вырезать оговорки и повторы"},
              open(os.path.join(a.work, "edit.json"), "w"), ensure_ascii=False, indent=1)
    print(open(os.path.join(a.work, "speech.txt")).read())
    print(f"Готово: {a.work}/edit.json — {len(segs)} кусков, {len(words)} слов")


if __name__ == "__main__":
    main()
