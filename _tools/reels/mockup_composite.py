"""Вставка записи экрана в мокап с зелёным экраном (#00FF00).

Углы экрана находятся автоматически по зелёному цвету, кадры записи
натягиваются на них с учётом перспективы, края зелёного прячутся под видео.

    python mockup_composite.py MOCKUP.png FRAMES_DIR OUT.mp4 [--size 1080x1920] [--fps 30]
"""
import argparse, pathlib, subprocess
import cv2, numpy as np


def screen_quad(im):
    b, g, r = [im[..., i].astype(int) for i in range(3)]
    m = ((g > 180) & (r < 120) & (b < 120))
    ys, xs = np.nonzero(m)
    pts = np.stack([xs, ys], 1); s = pts.sum(1); d = pts[:, 0] - pts[:, 1]
    quad = np.float32([pts[s.argmin()], pts[d.argmax()], pts[s.argmax()], pts[d.argmin()]])  # TL TR BR BL
    # мягкая маска: зелёный + полоса 3 px вокруг, чтобы не осталось зелёной каймы
    greenness = np.clip((g - np.maximum(r, b) - 40) / 120, 0, 1).astype(np.float32)
    mask = cv2.dilate(greenness, np.ones((7, 7), np.uint8))
    mask = cv2.GaussianBlur(mask, (3, 3), 0)
    return quad, mask[..., None]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mockup"); ap.add_argument("frames"); ap.add_argument("out")
    ap.add_argument("--size", default="1080x1920"); ap.add_argument("--fps", type=int, default=30)
    a = ap.parse_args()
    W, H = map(int, a.size.split("x"))
    bg = cv2.imread(a.mockup)
    quad, mask = screen_quad(bg)
    # раздвигаем углы на 2 px наружу — видео заходит под рамку монитора
    c = quad.mean(0); quad = c + (quad - c) * (1 + 2 / np.linalg.norm(quad - c, axis=1, keepdims=True))
    bgf = bg.astype(np.float32)
    frames = sorted(pathlib.Path(a.frames).glob("f*.jpg"))
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24",
                           "-s", f"{W}x{H}", "-r", str(a.fps), "-i", "-", "-c:v", "libx264", "-crf", "15",
                           "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart", a.out],
                          stdin=subprocess.PIPE)
    M = None
    for f in frames:
        fr = cv2.imread(str(f))
        if M is None:
            h, w = fr.shape[:2]
            M = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), quad)
        warped = cv2.warpPerspective(fr, M, (bg.shape[1], bg.shape[0]), flags=cv2.INTER_LANCZOS4)
        out = bgf * (1 - mask) + warped.astype(np.float32) * mask
        out = cv2.resize(out.clip(0, 255).astype(np.uint8), (W, H), interpolation=cv2.INTER_AREA)
        ff.stdin.write(out.tobytes())
    ff.stdin.close(); ff.wait()
    print("quad", quad.round(1).tolist(), "frames", len(frames))


if __name__ == "__main__":
    main()
