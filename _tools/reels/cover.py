#!/usr/bin/env python3
"""Обложка Reels: кадр из видео + хук ленточными плашками (каждая строка на своей плашке, ключевая синяя).

    python3 cover.py исходник.mp4 --t 0.8 --line "Платите за заявки," --line "а клиенты уходят" \
        --line "*к конкурентам?" --out cover.jpg

- `--t` — секунда исходника. Выбирать кадр с открытыми глазами и взглядом в камеру.
- Строка со `*` в начале — синяя плашка (ключевая мысль). Обычно одна, последняя.
- Заголовок целиком стоит в центральном квадрате 1080×1080 (y 420…1500): так ролик показывается в ленте,
  а квадрат входит и в обрезки 4:5 и 3:4. Лицо — сразу под заголовком, тоже внутри квадрата.
- `--face X Y` — где в исходнике 1080×1920 центр лица; `--zoom` — во сколько раз приблизить кадр.
"""
import argparse, subprocess, io
import numpy as np, cv2
from PIL import Image
from reel import W, H, GRAPH, OFF, BLUE, plate, blit

SQ0, SQ1 = (H - W) // 2, (H + W) // 2      # центральный квадрат 1080×1080 — превью в ленте
PAD = 50                                    # отступ заголовка от верха квадрата


def frame(path, t):
    png = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1",
                          "-vf", "unsharp=5:5:0.5:5:5:0,eq=contrast=1.05:saturation=1.06", "-f", "image2pipe",
                          "-vcodec", "png", "-"], capture_output=True, check=True).stdout
    return np.array(Image.open(io.BytesIO(png)).convert("RGB"))


def camera(src, zoom, face, at):
    sx = W / src.shape[1] * zoom
    x0 = at[0] - sx * face[0]; y0 = at[1] - sx * face[1]
    x0 = min(0, max(W - sx * src.shape[1], x0)); y0 = min(0, max(H - sx * src.shape[0], y0))
    M = np.float32([[sx, 0, x0], [0, sx, y0]])
    return cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REPLICATE)


def bar(text, blue, size):
    while True:                                   # не шире кадра минус поля
        b = plate(text, size, "ExtraBold", OFF if blue else GRAPH, BLUE if blue else OFF, 34, 18, 18)
        if b.shape[1] <= W - 2 * 70 or size <= 40: return b
        size -= 2


def render(src, lines, size=84, zoom=1.4, face=(550, 950), at=(540, 1190)):
    fr = camera(src, zoom, face, at)
    y = SQ0 + PAD
    for ln in lines:
        blue = ln.startswith("*")
        b = bar(ln.lstrip("*"), blue, size)
        blit(fr, b, W / 2 - b.shape[1] / 2, y)
        y += b.shape[0] + 16
    assert y - 16 <= SQ1 - PAD, "заголовок не влезает в квадрат — сократите текст или уменьшите --size"
    return fr


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("media"); ap.add_argument("--t", type=float, required=True)
    ap.add_argument("--line", action="append", required=True)
    ap.add_argument("--size", type=int, default=84); ap.add_argument("--zoom", type=float, default=1.4)
    ap.add_argument("--face", type=float, nargs=2, default=(550, 950))
    ap.add_argument("--out", default="cover.jpg")
    a = ap.parse_args()
    img = render(frame(a.media, a.t), a.line, a.size, a.zoom, tuple(a.face))
    Image.fromarray(img).save(a.out, quality=95)
    print(a.out)
