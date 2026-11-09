"""Покадровая запись HTML-страницы для R044 без потери чёткости.

Время страницы управляется вручную: таймеры и requestAnimationFrame — через часы Playwright,
CSS-анимации и переходы — через Web Animations API (каждая ставится на паузу и двигается на 1/30 с).
Поэтому запись идёт ровно 30 к/с, сколько бы ни длился сам скриншот.

    python r044_record.py URL OUT_DIR SECONDS [--dpr 1.5]
"""
import sys, pathlib, argparse
from playwright.sync_api import sync_playwright

STEP_JS = """(dt) => {
  const m = window.__anims || (window.__anims = new Map());
  for (const a of document.getAnimations()) {
    if (!m.has(a)) { a.pause(); m.set(a, 0); }
    const t = m.get(a) + dt; m.set(a, t); a.currentTime = t;
  }
}"""


def record(url, out, seconds, fps=30, w=1440, h=900, dpr=1.5):
    out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("f*.jpg"): f.unlink()
    dt = 1000 / fps
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=dpr)
        t0 = 1_762_700_000_000
        pg.clock.install(time=t0)
        pg.clock.pause_at(t0 + 1000)        # время стоит, пока мы его не двигаем
        pg.goto(url, wait_until="load")
        pg.wait_for_timeout(300)            # реальное время: дать догрузиться шрифтам и картинкам
        pg.evaluate("document.fonts.ready")
        n = int(round(seconds * fps))
        for i in range(n):
            pg.screenshot(path=str(out / f"f{i:04d}.jpg"), type="jpeg", quality=93)
            ms = round((i + 1) * dt) - round(i * dt)      # 33/34 мс, без накопления ошибки
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
