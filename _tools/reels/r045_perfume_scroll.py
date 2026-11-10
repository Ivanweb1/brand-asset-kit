"""Ролик «Claude + мой промпт = живой сайт за 100 000 ₽» (сценарий R045), 10,5 с, без голоса и без автора.

Устройство как у R044: вау-хук (сборка экрана) → 2 шага → готовый сайт и призыв в кадре.
Отличие: сайт показан на мониторе в мокапе «стол креативного директора», шаги — на размытом мокапе.

Исходники:
  work-perfume/frames   — perfume_record.py, Desktop/perfume-wow-demo/?demo=1, 13,5 с, 1770×1060
                          (вход 0–5,1 с, скролл к нотам 6,1–9,1, к покупке 9,75–12,25)
  work/r045/kit, claude — r045/*.html через r044_record.py, 2160×1350
  мокап                 — Desktop/perfume-wow-demo/mockup/creative-director-desk-green-screen-2160x3840.png

    python r045_perfume_scroll.py              # -> example-r045-perfume-scroll/final.mp4, cover.jpg
    python r045_perfume_scroll.py peek 0.5 4   # кадры work/r045/peek_<t>.png
"""
import sys, pathlib, subprocess, functools
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r044_wow_screen as r44
from mockup_composite import screen_quad

W, H, FPS = 1080, 1920, 30
K = HERE.parents[1]
WORK = K / "work" / "r045"
SITE = HERE / "work-perfume" / "frames"
OUT = HERE / "example-r045-perfume-scroll"
MOCKUP = pathlib.Path(r"C:\Users\panki\Desktop\perfume-wow-demo\mockup\creative-director-desk-green-screen-2160x3840.png")
SRC_W, SRC_H = 2160, 1350                                # кадры kit / claude

HOOK = ["{C} + мой промпт =", "живой сайт за 100 000 ₽"]
CTA = ["Напишите «СКРОЛЛ» —", "отдам промпт и скилл"]
CAP_Y = 250                                              # над монитором, ниже интерфейса Instagram

# t — начало в ролике, d — длительность, s0 — секунда исходника в начале, v — скорость
SCENES = [
    dict(t=0.0, d=4.0, kind="site", s0=0.0, v=1.25, caps=[(HOOK, 0, 9)]),
    dict(t=4.0, d=1.5, kind="kit", s0=0.3, v=1.0, crop=(0.40, 0.0, 1.0, 0.72),
         caps=[(["Забираете", "промпт и скилл"], 0, 9)]),
    dict(t=5.5, d=1.5, kind="claude", s0=0.45, v=1.0, crop=(0.06, 0.08, 0.94, 0.86),
         caps=[(["Вставляете в {C}"], 0, 9)]),
    dict(t=7.0, d=3.5, kind="site", s0=6.0, v=1.8, caps=[(["Сайт готов"], 0, 1.0), (CTA, 1.0, 9)]),
]
TOT = SCENES[-1]["t"] + SCENES[-1]["d"]
T_NOTE = 8.5                                             # уведомление об оплате (правило 06.11)
CLICKS = [4.0 + 0.7, 5.5 + 1.15]                         # копирование, отправка
COVER_S = 5.6                                            # обложка: готовый первый экран, а не капля


def ss(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


# ── мокап ────────────────────────────────────────────────────────────────────
@functools.lru_cache(None)
def mockup():
    bg = cv2.imread(str(MOCKUP))
    quad, mask = screen_quad(bg)
    c = quad.mean(0); quad = c + (quad - c) * (1 + 2 / np.linalg.norm(quad - c, axis=1, keepdims=True))
    sx, sy = W / bg.shape[1], H / bg.shape[0]
    bg = cv2.resize(bg, (W, H), interpolation=cv2.INTER_AREA)
    mask = cv2.resize(mask[..., 0], (W, H), interpolation=cv2.INTER_AREA)[..., None]
    q = quad * [sx, sy]
    return bg.astype(np.float32), mask, q.astype(np.float32)


@functools.lru_cache(None)
def blurred_bg():
    im = site_on_monitor(int(COVER_S * FPS)).filter(ImageFilter.GaussianBlur(36))   # без зелёного экрана
    return Image.eval(im, lambda v: int(v * 0.72))


N_SITE = len(list(SITE.glob("f*.jpg")))


@functools.lru_cache(maxsize=8)
def site_on_monitor(k):
    bg, mask, q = mockup()
    fr = cv2.imread(str(SITE / f"f{min(k, N_SITE - 1):04d}.jpg"))
    w = int(np.linalg.norm(q[1] - q[0])) + 2; h = int(np.linalg.norm(q[3] - q[0])) + 2
    fr = cv2.resize(fr, (w, h), interpolation=cv2.INTER_AREA)       # уменьшение без мерцания
    M = cv2.getPerspectiveTransform(np.float32([[0, 0], [w, 0], [w, h], [0, h]]), q)
    warped = cv2.warpPerspective(fr, M, (W, H), flags=cv2.INTER_CUBIC).astype(np.float32)
    out = (bg * (1 - mask) + warped * mask).clip(0, 255).astype(np.uint8)
    return Image.fromarray(cv2.cvtColor(out, cv2.COLOR_BGR2RGB))


# ── шаги: карточка на размытом мокапе ────────────────────────────────────────
@functools.lru_cache(maxsize=64)
def step_frame(kind, i):
    d = WORK / kind; n = len(list(d.glob("f*.jpg")))
    return Image.open(d / f"f{min(i, n - 1):04d}.jpg").convert("RGB")


def step_quad(sc, p):
    x0, y0, x1, y1 = sc["crop"]
    aspect = ((y1 - y0) * SRC_H) / ((x1 - x0) * SRC_W)
    z = 1 + 0.045 * ss(p); w = 1000 * z; h = w * aspect
    cx = W / 2 - 18 * ss(p); cy = 1000
    hl, hr = h * 1.05, h * 0.95
    lx, rx = cx - w / 2, cx + w / 2 - w * 0.015
    return [(lx, cy - hl / 2), (rx, cy - hr / 2), (rx, cy + hr / 2), (lx, cy + hl / 2)]


def step(fr, sc, p, i):
    x0, y0, x1, y1 = sc["crop"]
    src = step_frame(sc["kind"], i).crop((int(x0 * SRC_W), int(y0 * SRC_H), int(x1 * SRC_W), int(y1 * SRC_H)))
    cw, ch = src.size; q = step_quad(sc, p)
    c = r44.coeffs(q, [(0, 0), (cw, 0), (cw, ch), (0, ch)])
    sh = Image.new("L", (W, H), 0); ImageDraw.Draw(sh).polygon([(x, y + 26) for x, y in q], fill=150)
    fr.paste(Image.new("RGB", (W, H), (30, 20, 12)), (0, 0), sh.filter(ImageFilter.GaussianBlur(34)))
    img = src.transform((W, H), Image.PERSPECTIVE, c, Image.BICUBIC)
    m = r44.rmask(cw, ch, int(cw * 0.022)).transform((W, H), Image.PERSPECTIVE, c, Image.BILINEAR)
    fr.paste(img, (0, 0), m)


# ── кадр ─────────────────────────────────────────────────────────────────────
def at(i, cover=False):
    t = i / FPS
    sc = next(s for s in reversed(SCENES) if t >= s["t"] - 1e-6)
    lt = t - sc["t"]; p = lt / sc["d"]
    if sc["kind"] == "site":
        s = COVER_S if cover else sc["s0"] + lt * sc["v"]
        fr = site_on_monitor(int(round(s * FPS))).copy()
    else:
        fr = blurred_bg().copy()
        step(fr, sc, p, int(round((sc["s0"] + lt) * FPS)))
    for lines, a0, a1 in sc["caps"]:
        if a0 <= lt < a1:
            a = 1.0 if sc["t"] == 0 else r44.eout((lt - a0) / 0.22)   # хук виден с первого кадра
            r44.put_caption(fr, lines, a, y=CAP_Y)
    if t >= T_NOTE:
        n = r44.note(); k = r44.eout((t - T_NOTE) / 0.35)
        y = int(1330 + (1 - k) * 160)
        im = n.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * k)))
        fr.paste(im, ((W - n.width) // 2, y), im)
    return fr


def main(peek=None):
    OUT.mkdir(exist_ok=True); WORK.mkdir(parents=True, exist_ok=True)
    if peek:
        for s in peek: at(int(round(s * FPS))).save(WORK / f"peek_{s}.png")
        at(0, cover=True).save(WORK / "peek_cover.png")
        return
    ins = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-t", f"{TOT:.3f}", "-i", "anullsrc=r=48000:cl=stereo"]
    sfx = [("sfx-click.mp3", t, 0.25) for t in CLICKS] + [("sfx-pop.mp3", T_NOTE, 0.25)]
    fl, labs = [], []
    for j, (f, t, v) in enumerate(sfx):
        ins += ["-i", str(K / "11_MOTION" / f)]; ms = int(t * 1000)
        fl.append(f"[{j + 2}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={v},adelay={ms}|{ms}[s{j}]")
        labs.append(f"[s{j}]")
    fl.append(f"[1:a]{''.join(labs)}amix=inputs={1 + len(labs)}:normalize=0:duration=first,alimiter=limit=0.95[a]")
    cmd = ["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fl), "-map", "0:v", "-map", "[a]",
           "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-profile:v", "high", "-pix_fmt", "yuv420p",
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(OUT / "final.mp4")]
    at(0, cover=True).save(OUT / "cover.jpg", quality=95)
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(round(TOT * FPS))):
        p.stdin.write(np.asarray(at(i, cover=(i == 0)).convert("RGB"), np.uint8).tobytes())
    p.stdin.close(); p.wait(); print("done", OUT / "final.mp4", f"{TOT:.2f} s")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "peek":
        main([float(x) for x in sys.argv[2:]])
    else:
        main()
