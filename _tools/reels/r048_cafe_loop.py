"""Мокап «ноутбук в кофейне», в экране просто идёт экран «Ориентир. Окно» — без надписей, шагов и камеры.

Исходник — work/r048/site_loop: 14 с записи ?demo=1 (window_record.py). Берётся отрезок 2–14 с: это
полный демо-цикл (квартал → влёт в окно → гостиная → обратно), он начинается и кончается одним кадром
квартала, поэтому ролик зацикливается без шва.

    python r048_cafe_loop.py   # -> example-r048-window-cafe-loop/final.mp4, cover.jpg
"""
import pathlib, subprocess
import numpy as np
from PIL import Image
import r048_window_screen as base
import r048_cafe as cafe

FPS = base.FPS
SRC = base.WORK / "site_loop"
START, END = 2.0, 14.0
COVER_T = 7.6                                            # обложка: гостиная с видом на квартал
OUT = pathlib.Path(__file__).resolve().parent / "example-r048-window-cafe-loop"


def frame(k):
    src = Image.open(SRC / f"f{k:04d}.jpg").convert("RGB")
    cw, ch = src.size
    fr = cafe.mockup().copy()
    c = base.coeffs(cafe.screen_quad(), [(0, 0), (cw, 0), (cw, ch), (0, ch)])
    m = Image.new("L", (cw, ch), 255).transform((cafe.W, cafe.H), Image.PERSPECTIVE, c, Image.BILINEAR)
    fr.paste(src.transform((cafe.W, cafe.H), Image.PERSPECTIVE, c, Image.BICUBIC), (0, 0), m)
    fr.paste(Image.new("RGB", fr.size, (255, 255, 255)), (0, 0),
             Image.fromarray(np.minimum(np.asarray(cafe.glare()), np.asarray(m))))
    return fr


def main():
    OUT.mkdir(exist_ok=True)
    k0, k1 = int(START * FPS), int(END * FPS)
    frame(int(COVER_T * FPS)).save(OUT / "cover.jpg", quality=95)
    dur = (k1 - k0) / FPS
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{cafe.W}x{cafe.H}",
           "-r", str(FPS), "-i", "-", "-f", "lavfi", "-t", f"{dur:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
           "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-profile:v", "high",
           "-pix_fmt", "yuv420p", "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
           "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(OUT / "final.mp4")]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for k in range(k0, k1):
        p.stdin.write(np.asarray(frame(k), np.uint8).tobytes())
    p.stdin.close(); p.wait(); print("done", OUT / "final.mp4", f"{dur:.2f} s")


if __name__ == "__main__":
    main()
