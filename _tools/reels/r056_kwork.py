"""Ролик R056 «Заказ с Kwork → сайт KAFFA → оплата» (~11 с, без голоса, без плашек).

Иван за компьютером (IMG_2869, с 18 с — work-ring/bg_sdr.mp4) → поверх выезжает карточка заказа с Kwork
(«Создание сайта-визитки продуктового бренда», до 150 000 ₽) → монитор (IMG_7839, work-ring/mon_sdr.mp4)
с сайтом KAFFA: первый экран ×1,5 → скролл в «Помол» в реальном темпе → уведомление «+ 150 000 ₽» под экраном.
Ролик заканчивается на сайте и зацикливается.

Исходники:
  work-r056/site/f*.jpg      — запись KAFFA 1920×1080, 30 к/с (kaffa_record.record(..., w=1280, h=720, dpr=1.5))
  work-r056/kwork-order.png  — карточка заказа из ленты Kwork, 1456×330 (без данных покупателя)
  work-ring/bg_sdr.mp4, mon_sdr.mp4, mon_audio.m4a — из R055

    python r056_kwork.py              # -> example-r056-kwork/final.mp4, cover.jpg
    python r056_kwork.py peek 1 3 6   # кадры work-r056/peek_<t>.png
"""
import sys, pathlib, functools, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from r014_avito import W, H, FPS, K, clamp, prog, eout, ss, eback, put
import r055_ring as R

WORK = HERE / "work-r056"
OUT = HERE / "example-r056-kwork"
SITE = sorted((WORK / "site").glob("f*.jpg"))

# ── монтажный лист ───────────────────────────────────────────────────────────
T_ORDER = 0.25                                 # карточка заказа выезжает почти сразу
S_MON = 2.0                                    # v1.1: заказ на экране ~2 с («2 сек хватит»)
# v1.1: сайт сразу с вау-участка, без статичного первого экрана: помол → пролив → всплеск → глоток ×1,2,
# затем глоток стоит в реальном темпе под оплату
SRC = [250 + i for i in range(387 - 250)]     # с пролива: пар и струя с первого кадра
# v1.3: финал на «Глотке» с выехавшей карточкой «Эфиопия Иргачеффе» (Иван: «давай на этом кадре завершим»)
SRC += [386] * 12
MON_D = len(SRC) / FPS
E_MON = S_MON + MON_D
T_NOTE = E_MON - 1.5                          # оплата — в конце, поверх сцены с сайтом
TOT = E_MON
XF = 0.15


# ── карточка заказа ──────────────────────────────────────────────────────────
@functools.lru_cache(None)
def order_card():
    src = Image.open(WORK / "kwork-order.png").convert("RGBA")
    w = 960; im = src.resize((w, round(src.height * w / src.width)), Image.LANCZOS)
    m = Image.new("L", (w * 2, im.height * 2), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w * 2 - 1, im.height * 2 - 1], 44, fill=255)
    im.putalpha(m.resize(im.size, Image.LANCZOS))
    sh = Image.new("RGBA", (w + 80, im.height + 80))
    ImageDraw.Draw(sh).rounded_rectangle([40, 52, 40 + w, 52 + im.height], 22, fill=(0, 0, 0, 160))
    sh = sh.filter(ImageFilter.GaussianBlur(20)); sh.alpha_composite(im, (40, 40))
    return sh


CARD_Y = 1110                                  # под подбородком Ивана, выше нижней зоны интерфейса


def card_layer(fr, t):
    if t < T_ORDER: return fr
    p = eback(prog(t, T_ORDER, 0.45)); c = order_card()
    # лёгкий наезд на карточку, пока она на экране (без статики)
    z = 1 + 0.06 * ss(prog(t, T_ORDER + 0.4, S_MON - T_ORDER - 0.4))
    if z > 1.0005:
        c = c.resize((round(c.width * z), round(c.height * z)), Image.LANCZOS)
    x = (W - c.width) / 2; y = CARD_Y - 40 - (c.height - order_card().height) / 2 + 160 * (1 - p)
    put(fr, c, x, y, clamp(p * 1.5))
    return fr


# ── монитор с сайтом ─────────────────────────────────────────────────────────
@functools.lru_cache(maxsize=4)
def site_img(i):
    return cv2.imread(str(SITE[min(i, len(SITE) - 1)])).astype(np.float32)


def site_at(src):
    a = int(src); w = src - a
    return site_img(a) if w < 1e-3 else site_img(a) * (1 - w) + site_img(a + 1) * w


RNG = np.random.default_rng(56)


def monitor_frame(t):
    i = int(round(t * FPS)); src = SRC[min(i, len(SRC) - 1)]
    bg = R.MON.at(i).astype(np.float32)
    Hm, mask, fall = R.screen_geom()
    s = 10 + site_at(src) * fall * 0.93
    s = cv2.GaussianBlur(s, (0, 0), 0.9)
    warped = cv2.warpPerspective(s, Hm, (W, H), flags=cv2.INTER_LINEAR)
    warped += RNG.normal(0, 2.2, warped.shape).astype(np.float32)
    out = bg * (1 - mask) + warped * mask
    z = 1 + 0.07 * ss(prog(t, 0, MON_D)); cx, cy = 540, 980
    M = np.float32([[z, 0, cx - z * cx], [0, z, cy - z * cy]])
    out = cv2.warpAffine(out, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return Image.fromarray(cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_BGR2RGB)).convert("RGBA")


@functools.lru_cache(None)
def note():
    p = WORK / "payment-150000.png"
    if not p.exists():
        import payment_note
        payment_note.make(150000, p)
    im = Image.open(p).convert("RGBA"); w = 880
    im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    sh = Image.new("RGBA", (w + 80, im.height + 80))
    ImageDraw.Draw(sh).rounded_rectangle([40, 50, 40 + w, 50 + im.height], 40, fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(18)); sh.alpha_composite(im, (40, 40)); return sh


def scene(t):
    if t >= S_MON:
        fr = monitor_frame(t - S_MON)
        if t >= T_NOTE:
            p = eback(prog(t, T_NOTE, 0.45)); n = note()
            put(fr, n, (W - n.width) / 2, 1390 + 140 * (1 - p), clamp(p * 1.5))   # под экраном монитора
        return fr
    fr = R.bg_frame(t); fr.alpha_composite(R.top_shade())
    return card_layer(fr, t)


def at(i):
    t = i / FPS
    fr = scene(t).convert("RGB")
    if S_MON - XF < t < S_MON:
        fr = Image.blend(fr, scene(S_MON).convert("RGB"), (t - (S_MON - XF)) / XF)
    return fr


def make_cover():
    """Первый экран KAFFA на мониторе, без надписей — как обложка R055."""
    k = next(i for i, s in enumerate(SRC) if s >= 318)            # всплеск кофе
    monitor_frame(k / FPS).convert("RGB").save(OUT / "cover.jpg", quality=95)


def main(peek=None):
    OUT.mkdir(exist_ok=True)
    if peek:
        for s in peek: at(int(s * FPS)).save(WORK / f"peek_{s}.png")
        return
    make_cover()
    sfx = [("sfx-pop.mp3", T_ORDER, 0.22), ("sfx-pop.mp3", S_MON + 0.05, 0.14), ("sfx-click.mp3", T_NOTE, 0.3)]
    ins = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-t", f"{TOT:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
           "-i", str(R.WORK / "mon_audio.m4a")]
    ms = int(S_MON * 1000)
    fl = [f"[2:a]atrim=0:{MON_D:.3f},afade=t=in:d=0.1,afade=t=out:st={MON_D - 0.15:.3f}:d=0.15,"
          f"aformat=sample_rates=48000:channel_layouts=stereo,volume=0.7,adelay={ms}|{ms}[m]"]
    labs = ["[m]"]
    for j, (f, t, v) in enumerate(sfx):
        ins += ["-i", str(K / "11_MOTION" / f)]; ms = int(t * 1000)
        fl.append(f"[{j + 3}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={v},adelay={ms}|{ms}[s{j}]")
        labs.append(f"[s{j}]")
    fl.append(f"[1:a]{''.join(labs)}amix=inputs={1 + len(labs)}:normalize=0:duration=first,alimiter=limit=0.95[a]")
    cmd = ["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fl), "-map", "0:v", "-map", "[a]",
           "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-profile:v", "high", "-pix_fmt", "yuv420p",
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(OUT / "final.mp4")]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(round(TOT * FPS))):
        fr = at(i)
        p.stdin.write(np.ascontiguousarray(np.asarray(fr), np.uint8).tobytes())
    p.stdin.close(); p.wait(); print("done", OUT / "final.mp4", f"{TOT:.2f} s")


if __name__ == "__main__":
    if sys.argv[1:2] == ["peek"]:
        main([float(s) for s in sys.argv[2:]])
    else:
        main()
