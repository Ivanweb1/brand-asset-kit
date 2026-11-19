"""Ролик R057 «Парад сайтов» (v1.3, 6,9 с, без голоса, под бит sound-01) — утверждён 19.11.

Монитор из видео Ивана (IMG_7839 с 5 с → work-r057/mon_sdr.mp4, как в R055/R056), в экран по углам вставлены
пять сайтов, каждый сразу с вау-участка; смена — каждые три доли бита (130 BPM, 1,38 с):
MIRRA (струя → флакон) → KAFFA (всплеск) → «ОБЪЁМ» (бетон → интерьер) → ЖК (сквозь окно) → «Грань» (портал).
Хук весь ролик — значки без текста: Claude + аватарка Ивана (hook3); подпись ниши под монитором.
Текстовые хуки v1–v1.1 (plates, hook2) оставлены в коде для истории, в ролике не используются.

Исходники (work-r057/, в git не попадают):
  mon_sdr.mp4, mon_audio.m4a — IMG_7839 с 5 с, HDR → SDR (hable), 1080×1920, 30 к/с
  kaffa/ perfume/ interior/ window/ ring/ f*.jpg — записи сайтов 1920×1080, 30 к/с (work-r057/record_all.ps1)
  звук — reels-content-system/references/audio/sound-01.m4a (в git не попадает)

    python r057_parade.py              # -> example-r057-parade/final.mp4, cover.jpg
    python r057_parade.py peek 0.5 2   # кадры work-r057/peek_<t>.png
"""
import sys, pathlib, functools, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from r014_avito import W, H, FPS, GRAPH, OFF, BLUE, clamp, prog, eout, ss, put, plates

WORK = HERE / "work-r057"
OUT = HERE / "example-r057-parade"
AUDIO = pathlib.Path(r"C:\Users\panki\Desktop\reels-content-system\references\audio\sound-01.m4a")

# ── монтажный лист ───────────────────────────────────────────────────────────
BEAT = 60 / 130.4; B0 = 0.05                   # доли sound-01: 0,05 + 0,46·k
def beat(k): return B0 + BEAT * k

# (папка, первый кадр записи, скорость, подпись ниши)
SITES = {
    "perfume":  (80, 1.6, "парфюм"),          # струя закручивается → флакон (кадры 80…146)
    "kaffa":    (296, 1.2, "кофе"),            # пролив → всплеск (320…336) → кружка (296…345)
    "interior": (110, 1.8, "интерьеры"),       # бетон → отделка → мебель (110…184)
    "window":   (110, 1.6, "недвижимость"),    # квартал → сквозь окно в квартиру (110…176)
    "ring":     (110, 2.2, "ювелирка"),        # кольцо в шкатулке → портал → закат (110…200)
}
CUTS = [(0.0, "perfume"), (beat(3), "kaffa"), (beat(6), "interior"), (beat(9), "window"), (beat(12), "ring")]
TOT = beat(15)                                 # v1.3: финал на «Грани», без повтора MIRRA (Иван 19.11)
HOOK_OUT = beat(4)                             # хук уходит на второй доле KAFFA (~1,9 с)
HOOK = [("Все эти сайты —", OFF, GRAPH), ("без кода и верстальщика", BLUE, OFF)]

QUAD = np.float32([[55, 643], [1022.2, 592.8], [996.0, 1368.1], [71.5, 1184.5]])   # экран в mon_sdr (из R055)


def seg_at(t):
    k = max(j for j, (s, _) in enumerate(CUTS) if s <= t + 1e-6)
    s, name = CUTS[k]
    return name, t - s, k                      # финал = начало: MIRRA снова с первого кадра записи


# ── видео ────────────────────────────────────────────────────────────────────
class Clip:
    def __init__(self, path):
        self.cap = cv2.VideoCapture(str(path)); self.i = -1; self.fr = None
        self.n = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))

    def at(self, i):
        i = min(max(i, 0), self.n - 1)
        if i < self.i: self.cap.set(cv2.CAP_PROP_POS_FRAMES, i); self.i = i - 1
        while self.i < i:
            ok, f = self.cap.read(); self.i += 1
            if ok: self.fr = f
        return self.fr


MON = Clip(WORK / "mon_sdr.mp4")


@functools.lru_cache(None)
def frames(name): return sorted((WORK / name).glob("f*.jpg"))


@functools.lru_cache(maxsize=8)
def site_img(name, i):
    fs = frames(name); im = cv2.imread(str(fs[min(max(i, 0), len(fs) - 1)]))
    if im.shape[:2] != (1080, 1920): im = cv2.resize(im, (1920, 1080), interpolation=cv2.INTER_AREA)
    return im.astype(np.float32)


def site_at(name, lt):
    f0, v, _ = SITES[name]; src = f0 + lt * FPS * v
    a = int(src); w = src - a
    return site_img(name, a) if w < 1e-3 else site_img(name, a) * (1 - w) + site_img(name, a + 1) * w


@functools.lru_cache(None)
def screen_geom():
    c = QUAD.mean(0); q = c + (QUAD - c) * (1 + 1.5 / np.linalg.norm(QUAD - c, axis=1, keepdims=True))
    Hm = cv2.getPerspectiveTransform(np.float32([[0, 0], [1920, 0], [1920, 1080], [0, 1080]]), q)
    m = np.zeros((H * 4, W * 4), np.uint8); cv2.fillPoly(m, [np.round(QUAD * 4).astype(np.int32)], 255, cv2.LINE_AA)
    mask = cv2.resize(m, (W, H), interpolation=cv2.INTER_AREA).astype(np.float32)[..., None] / 255
    yy, xx = np.mgrid[0:1080, 0:1920].astype(np.float32)
    fall = 1.0 - 0.10 * (1 - xx / 1920) * (yy / 1080) - 0.04 * (yy / 1080)
    return Hm, mask, fall[..., None]


RNG = np.random.default_rng(57)


def monitor_frame(t, site):
    i = int(round(t * FPS))
    bg = MON.at(i).astype(np.float32)
    Hm, mask, fall = screen_geom()
    s = 10 + site * fall * 0.93
    s = cv2.GaussianBlur(s, (0, 0), 0.9)
    warped = cv2.warpPerspective(s, Hm, (W, H), flags=cv2.INTER_LINEAR)
    warped += RNG.normal(0, 2.2, warped.shape).astype(np.float32)
    out = bg * (1 - mask) + warped * mask
    z = 1 + 0.07 * ss(prog(t, 0, TOT)); cx, cy = 540, 980          # медленный наезд через весь ролик
    M = np.float32([[z, 0, cx - z * cx], [0, z, cy - z * cy]])
    out = cv2.warpAffine(out, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return Image.fromarray(cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_BGR2RGB)).convert("RGBA")


# ── надписи ──────────────────────────────────────────────────────────────────
@functools.lru_cache(None)
def label(text):
    from r014_avito import font
    f = font("SemiBold", 40)
    tw = int(f.getlength(text)); pad = 26; h = 64
    im = Image.new("RGBA", (tw + pad * 2 + 60, h + 60))
    sh = Image.new("RGBA", im.size); ImageDraw.Draw(sh).rounded_rectangle([30, 36, 30 + tw + pad * 2, 36 + h], 32, fill=(0, 0, 0, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(12)))
    d = ImageDraw.Draw(im); d.rounded_rectangle([30, 30, 30 + tw + pad * 2, 30 + h], 32, fill=GRAPH + (215,))
    d.text((30 + pad, 30 + h / 2), text, font=f, fill=OFF, anchor="lm")
    return im


# ── хук v2: без плашек — тонкая типографика на мягком затемнении (Иван 19.11: «аккуратный, более премиальный») ──
HOOK2 = ["Твои сайты, когда наконец-то", "научился работать с ИИ"]   # Иван 19.11
HOOK2_STYLE = "clean"                        # "clean" — две строки; "line" — с тонкой чертой между строками


def _track(d, xy, s, f, fill, sp):
    """Текст с разрядкой sp px, по центру относительно xy[0]."""
    w = sum(f.getlength(ch) for ch in s) + sp * (len(s) - 1); x = xy[0] - w / 2
    for ch in s:
        d.text((x, xy[1]), ch, font=f, fill=fill); x += f.getlength(ch) + sp


@functools.lru_cache(None)
def hook_sprite(rows, style):
    from r014_avito import font
    SS = 3; im = Image.new("RGBA", (W * SS, 360 * SS)); d = ImageDraw.Draw(im)
    f1 = font("Medium", 50 * SS); f2 = font("SemiBold", 58 * SS)
    y = 40 * SS
    _track(d, (W * SS / 2, y), rows[0], f1, OFF + (235,), 2 * SS); y += 78 * SS
    if style == "line":
        d.line([(W * SS / 2 - 36 * SS, y), (W * SS / 2 + 36 * SS, y)], fill=OFF + (150,), width=2 * SS); y += 26 * SS
    _track(d, (W * SS / 2, y), rows[1], f2, OFF + (255,), 0)
    im = im.resize((W, 360), Image.LANCZOS)
    sh = Image.new("RGBA", im.size); sh.putalpha(im.getchannel("A").point(lambda v: v * 0.55))
    sh = Image.merge("RGBA", (*Image.new("RGB", im.size, (0, 0, 0)).split(), sh.getchannel("A"))).filter(ImageFilter.GaussianBlur(10))
    out = Image.new("RGBA", im.size); out.alpha_composite(sh, (0, 3)); out.alpha_composite(im)
    return out


@functools.lru_cache(None)
def top_veil():
    """Мягкое затемнение сверху, чтобы светлый текст читался на обоях."""
    a = np.clip(1 - np.arange(H) / 900, 0, 1) ** 1.6 * 150
    im = Image.new("RGBA", (W, H), (12, 10, 10, 0)); im.putalpha(Image.fromarray(np.repeat(a[:, None], W, 1).astype(np.uint8)))
    return im


# ── хук v3: формула [значок Claude] + [аватарка Ивана] = эти сайты (Иван 19.11) ─────────────────────────
ICON = 132                                     # сторона значков, px


@functools.lru_cache(None)
def formula_sprite():
    from r014_avito import font
    SS = 3; s = ICON * SS
    logo = Image.open(WORK / "claude-logo.png").convert("RGBA").resize((s, s), Image.LANCZOS)
    m = Image.new("L", (s, s), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, s - 1, s - 1], int(s * 0.23), fill=255)
    logo.putalpha(m)
    av = Image.open(WORK / "avatar.jpg").convert("RGBA").resize((s, s), Image.LANCZOS)
    m = Image.new("L", (s, s), 0); ImageDraw.Draw(m).ellipse([0, 0, s - 1, s - 1], fill=255); av.putalpha(m)
    f_op = font("Medium", 64 * SS)
    gap = 34 * SS                              # v1.5: только «Claude + аватарка», без «= эти сайты» (Иван 19.11)
    w_plus = f_op.getlength("+")
    total = s + gap + w_plus + gap + s
    im = Image.new("RGBA", (W * SS, (ICON + 60) * SS)); d = ImageDraw.Draw(im)
    x = (W * SS - total) / 2; y = 30 * SS; cy = y + s / 2
    im.alpha_composite(logo, (int(x), int(y))); x += s + gap
    d.text((x, cy), "+", font=f_op, fill=OFF + (230,), anchor="lm"); x += w_plus + gap
    im.alpha_composite(av, (int(x), int(y)))
    d.ellipse([x, y, x + s - 1, y + s - 1], outline=OFF + (90,), width=2 * SS)
    im = im.resize((W, ICON + 60), Image.LANCZOS)
    a = im.getchannel("A").point(lambda v: int(v * 0.6))
    sh = Image.merge("RGBA", (*Image.new("RGB", im.size, (0, 0, 0)).split(), a)).filter(ImageFilter.GaussianBlur(14))
    out = Image.new("RGBA", im.size); out.alpha_composite(sh, (0, 6)); out.alpha_composite(im)
    return out


FORMULA_Y = 392                                # верх значков ~422 px: под шапкой Reels, над монитором


def hook3(fr, a, dy=0):
    if a <= 0: return
    put(fr, top_veil(), 0, 0, a * 0.8)
    put(fr, formula_sprite(), 0, FORMULA_Y + dy + 18 * (1 - a), a)


def hook2(fr, a, rows=None, style=None):
    if a <= 0: return
    rows = tuple(rows or HOOK2); style = style or HOOK2_STYLE
    v = top_veil(); put(fr, v, 0, 0, a)
    sp = hook_sprite(rows, style); put(fr, sp, 0, HOOK_Y - 50 + 18 * (1 - a), a)   # верх текста ~362 px: ниже шапки Reels, выше монитора


LABEL_Y = 1430                                # под монитором, выше нижней зоны интерфейса (1640)
HOOK_Y = 372                                   # под шапкой Reels (340), над экраном монитора


def at(i):
    t = i / FPS
    name, lt, k = seg_at(t)
    fr = monitor_frame(t, site_at(name, lt))
    # подпись ниши: короткое появление на каждой склейке
    if True:
        p = eout(prog(lt, 0, 0.18)); lb = label(SITES[name][2])
        put(fr, lb, (W - lb.width) / 2, LABEL_Y + 16 * (1 - p), p)
    # хук: значки Claude + аватарка весь ролик (Иван 19.11: «это на протяжении всего ролика»)
    hook3(fr, 1)
    return fr.convert("RGB")


def make_cover():
    """Флакон MIRRA на мониторе + плашка-хук (как в сценарии)."""
    fr = monitor_frame(0.0, site_at("perfume", COVER_LT))
    # в ленте виден только квадрат y 420…1500 (RULES §9): значки опускаем на 50 px — внутрь квадрата с отступом
    hook3(fr, 1, dy=40)
    fr.convert("RGB").save(OUT / "cover.jpg", quality=95)


COVER_LT = (150 - 80) / (FPS * 1.6)           # кадр MIRRA 150 — флакон собран


def main(peek=None):
    OUT.mkdir(exist_ok=True)
    if peek:
        for s in peek: at(int(s * FPS)).save(WORK / f"peek_{s}.png")
        return
    make_cover()
    ins = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", str(AUDIO), "-i", str(WORK / "mon_audio.m4a")]
    fl = [f"[1:a]atrim=0:{TOT:.3f},afade=t=out:st={TOT - 0.12:.3f}:d=0.12,aformat=sample_rates=48000:channel_layouts=stereo[m]",
          f"[2:a]atrim=0:{TOT:.3f},aformat=sample_rates=48000:channel_layouts=stereo,volume=0.25[k]",
          "[m][k]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]"]
    cmd = ["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fl), "-map", "0:v", "-map", "[a]",
           "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-profile:v", "high", "-pix_fmt", "yuv420p",
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", "-t", f"{TOT:.3f}", str(OUT / "final.mp4")]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(round(TOT * FPS))):
        p.stdin.write(np.ascontiguousarray(np.asarray(at(i)), np.uint8).tobytes())
    p.stdin.close(); p.wait(); print("done", OUT / "final.mp4", f"{TOT:.2f} s")


if __name__ == "__main__":
    if sys.argv[1:2] == ["peek"]:
        main([float(s) for s in sys.argv[2:]])
    else:
        main()
