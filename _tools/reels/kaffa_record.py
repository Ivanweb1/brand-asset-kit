"""Покадровая запись сайта KAFFA (kaffa-wow-demo) для R046 по схеме R044.

Сайт сначала грузит 363 кадра скролл-видео; в demo-режиме лоадер скрыт, поэтому ждём,
пока счётчик загрузки дойдёт до 100 %, и только потом двигаем часы страницы.

    python kaffa_record.py OUT_DIR [--url URL] [--seconds 18.5]
"""
import time, pathlib, argparse
from playwright.sync_api import sync_playwright
from r044_record import STEP_JS

URL = "https://ivanweb1.github.io/kaffa-wow-demo/?demo=1"


def record(url, out, seconds, fps=30, w=1440, h=900, dpr=1.5):
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
        for _ in range(240):
            if "100%" in (pg.evaluate("document.querySelector('#loader small')?.textContent") or ""):
                break
            time.sleep(0.5)
        else:
            raise SystemExit("кадры не загрузились за 2 минуты")
        pg.evaluate("document.fonts.ready")
        time.sleep(1.0)
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
    ap.add_argument("--seconds", type=float, default=18.5)
    a = ap.parse_args()
    print(record(a.url, a.out, a.seconds), "frames")
