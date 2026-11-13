"""Покадровая запись экрана «Ориентир. Окно» (R048) — как r044_record.py, но старт после загрузки кадров видео.

Экран сначала декодирует 121 кадр ролика и только потом ставит body.is-ready и запускает сборку и демо.
Декодирование идёт в реальном времени, поэтому ждём is-ready до того, как двигать часы страницы.

    python window_record.py URL OUT_DIR SECONDS [--dpr 1.5]
"""
import pathlib, argparse
from playwright.sync_api import sync_playwright
from r044_record import STEP_JS


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
        pg.evaluate("document.fonts.ready")
        for _ in range(600):                               # до 60 с реального времени
            if pg.evaluate("document.body.classList.contains('is-ready')"): break
            pg.wait_for_timeout(100)
        else:
            raise SystemExit("экран не дошёл до is-ready")
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
    ap.add_argument("url"); ap.add_argument("out"); ap.add_argument("seconds", type=float)
    ap.add_argument("--dpr", type=float, default=1.5)
    a = ap.parse_args()
    print(record(a.url, a.out, a.seconds, dpr=a.dpr), "frames")
