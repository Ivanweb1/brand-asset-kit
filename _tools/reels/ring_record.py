"""Запись сайта «Грань» (jewelry-portal-demo) для R055: загрузка-портал + лента вправо.

Портал играет настоящие <video> и ждёт их 'ended', поэтому покадровая запись с остановленными
часами (r044_record.py) для него не годится: портал пишется в реальном времени через CDP screencast
в Chrome (в Chromium Playwright нет H.264) и выравнивается по меткам времени до 30 к/с.
Лента вправо пишется покадрово: scrollY задаётся по плавной кривой, scrub-твины GSAP доводятся
до конца, затем снимок — без рывков от нагрузки.

    python ring_record.py OUT_DIR --dir C:/Users/panki/Desktop/jewelry-portal-demo [--w 1920 --h 1080]
"""
import argparse, base64, pathlib, time, io, math
from PIL import Image
from playwright.sync_api import sync_playwright

FPS = 30
HOLD_HERO = 0.6           # с — первый экран стоит после портала
SCROLL_S = 2.6            # с — лента едет до панели с дугой кольца
HOLD_END = 0.8            # с — стоит на дуге

SETTLE_JS = """(y) => {
  window.scrollTo(0, y);
  ScrollTrigger.update();
  for (const st of ScrollTrigger.getAll()) { const tw = st.getTween && st.getTween(); if (tw) tw.progress(1); }
  return new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
}"""


def ease(p):  # плавный старт и плавная остановка
    return 0.5 - 0.5 * math.cos(math.pi * min(max(p, 0), 1))


def record(url, out, w=1920, h=1080):
    out = pathlib.Path(out); out.mkdir(parents=True, exist_ok=True)
    for f in out.glob("f*.jpg"): f.unlink()
    raw = []
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome", args=["--autoplay-policy=no-user-gesture-required", "--hide-scrollbars"])
        pg = b.new_page(viewport={"width": w, "height": h})
        cdp = pg.context.new_cdp_session(pg)

        def on_frame(e):
            raw.append((e["metadata"]["timestamp"], e["data"]))
            try: cdp.send("Page.screencastFrameAck", {"sessionId": e["sessionId"]})
            except Exception: pass

        cdp.on("Page.screencastFrame", on_frame)
        cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 95, "maxWidth": w, "maxHeight": h, "everyNthFrame": 1})
        pg.goto(url, wait_until="commit")
        pg.wait_for_function("document.documentElement.dataset.portal === 'finished'", timeout=40000, polling=50)
        pg.wait_for_timeout(int(HOLD_HERO * 1000))
        cdp.send("Page.stopScreencast"); pg.wait_for_timeout(200)
        # портал → ровные 30 к/с
        ts0 = raw[0][0]; n = int((raw[-1][0] - ts0) * FPS); k = 0
        for i in range(n):
            t = ts0 + i / FPS
            while k + 1 < len(raw) and raw[k + 1][0] <= t: k += 1
            im = Image.open(io.BytesIO(base64.b64decode(raw[k][1]))).convert("RGB")
            if im.size != (w, h): im = im.resize((w, h), Image.LANCZOS)
            im.save(out / f"f{i:04d}.jpg", quality=94)
        big = [(round(a[0] - ts0, 2), round(c[0] - a[0], 3)) for a, c in zip(raw, raw[1:]) if c[0] - a[0] > 0.07]
        print(f"портал: {n} кадров; провалы > 70 мс (t, gap): {big}")
        # лента: покадрово
        y_end = pg.evaluate("""() => { const st = ScrollTrigger.getAll().find(s => s.pin);
            return st.start + document.querySelector('.arch').offsetLeft; }""")
        m = int((SCROLL_S + HOLD_END) * FPS)
        for j in range(m):
            pg.evaluate(SETTLE_JS, y_end * ease(j / (SCROLL_S * FPS)))
            pg.screenshot(path=str(out / f"f{n + j:04d}.jpg"), type="jpeg", quality=94)
        b.close()
    print(f"лента: {m} кадров до y={y_end}; всего {n + m} кадров {FPS} к/с")
    return n + m, n


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("--url", default="http://127.0.0.1:8765/")
    ap.add_argument("--w", type=int, default=1920); ap.add_argument("--h", type=int, default=1080)
    ap.add_argument("--dir", help="раздать эту папку локально и писать с неё")
    a = ap.parse_args()
    if a.dir:
        import functools, threading, http.server
        hd = functools.partial(http.server.SimpleHTTPRequestHandler, directory=a.dir)
        hd.log_message = lambda *x: None
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), hd)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        a.url = f"http://127.0.0.1:{srv.server_address[1]}/"
    record(a.url, a.out, a.w, a.h)
