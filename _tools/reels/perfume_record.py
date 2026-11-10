"""Покадровая запись вау-экрана MIRRA (perfume-wow-demo) по схеме R044.

Отличие от r044_record.py: сайт сначала грузит ~370 кадров скролл-видео,
поэтому часы страницы стоят, пока не спрячется лоадер, и только потом идёт запись.

    python perfume_record.py OUT_DIR [--url URL] [--seconds 13.5] [--w 1600 --h 900 --dpr 1.2]
"""
import time, pathlib, argparse
from playwright.sync_api import sync_playwright
from r044_record import STEP_JS

URL = "https://ivanweb1.github.io/perfume-wow-demo/?demo=1"


def record(url, out, seconds, fps=30, w=1600, h=900, dpr=1.2):
    out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("f*.jpg"): f.unlink()
    dt = 1000 / fps
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=dpr)
        t0 = 1_762_700_000_000
        pg.clock.install(time=t0)
        pg.clock.pause_at(t0 + 1000)
        pg.goto(url, wait_until="load")
        # картинки грузятся по сети и при остановленных часах — ждём лоадер в реальном времени
        for _ in range(240):
            if pg.evaluate("document.querySelector('.loader')?.classList.contains('is-hidden')"):
                break
            time.sleep(0.5)
        else:
            raise SystemExit("лоадер не спрятался за 2 минуты")
        pg.evaluate("document.fonts.ready")
        time.sleep(0.5)
        n = int(round(seconds * fps))
        for i in range(n):
            pg.screenshot(path=str(out / f"f{i:04d}.jpg"), type="jpeg", quality=93)
            ms = round((i + 1) * dt) - round(i * dt)
            pg.clock.run_for(ms)
            pg.evaluate(STEP_JS, ms)
        b.close()
    return n


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--url", default=URL)
    ap.add_argument("--seconds", type=float, default=13.5)
    ap.add_argument("--w", type=int, default=1600); ap.add_argument("--h", type=int, default=900)
    ap.add_argument("--dpr", type=float, default=1.2)
    a = ap.parse_args()
    print(record(a.url, a.out, a.seconds, w=a.w, h=a.h, dpr=a.dpr), "frames")
