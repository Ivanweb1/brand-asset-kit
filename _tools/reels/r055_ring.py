"""Ролик R055 «Агентство: 350 000 ₽ — я: 15 000 ₽» (~13 с, без голоса, без плашек).

Иван за компьютером (IMG_2869, с 18 с), поверх — пузыри Telegram без фона чата: клиент пришёл от агентства →
«Сделаю за 15 000» → «Готово, откройте 👇» → монитор (IMG_7839) с сайтом «Грань»: загрузка-портал ×1,5 и лента
вправо до дуги кольца, вставлено в экран по углам → снова Иван: «Это правда за 15?!» → «Да» → «+ 15 000 ₽» (сразу вся сумма).

Исходники (work-ring/):
  site/f*.jpg   — запись «Грани» 1920×1080, 30 к/с (ring_record.py)
  mon_sdr.mp4   — IMG_7839 с 5 с, тонмап HDR → 1080×1920 30 к/с
  bg_sdr.mp4    — IMG_2869 с 18 с, то же, увеличено ×1,2 и сдвинуто (Иван выше в кадре)
  mon_audio.m4a — звук IMG_7839 с 5 с (клавиатура)

    python r055_ring.py              # -> example-r055-ring/final.mp4, cover.jpg
    python r055_ring.py peek 1 4 9   # кадры work-ring/peek_<t>.png
"""
import sys, pathlib, functools, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from r014_avito import W, H, FPS, GRAPH, OFF, BLUE, K, clamp, prog, eout, ss, eback, lerp, put, plates

WORK = HERE / "work-ring"
OUT = HERE / "example-r055-ring"
SITE = sorted((WORK / "site").glob("f*.jpg"))

# ── монтажный лист ───────────────────────────────────────────────────────────
S_MON = 2.75                                  # начало монитора
# сайт: портал с кадра 44 до 332 ×1,2 → лента 332…410 в реальном темпе → стоит на дуге (v1.2: «слишком быстро скролится»)
SRC = [44 + i * 1.2 for i in range(int((332 - 44) / 1.2))]
SRC += [332 + j for j in range(78)] + [410 + j for j in range(24)]
MON_D = len(SRC) / FPS
E_MON = S_MON + MON_D
T_NOTE = 1.95                                 # оплата сразу после «Сделаю за 15 000 прямо сейчас»
TOT = E_MON                                   # финал — на сайте, ролик зацикливается
XF = 0.12                                     # мягкий переход на склейках

QUAD = np.float32([[55, 643], [1022.2, 592.8], [996.0, 1368.1], [71.5, 1184.5]])   # экран в mon_sdr, TL TR BR BL

CHAT = [  # (время, кто, текст, время в чате, превью ссылки)
    (0.15, "in", "Здравствуйте! Нужен сайт для мастерской колец. В агентстве насчитали 350 000 и два месяца 😩", "11:02", False),
    (1.20, "out", "Сделаю за 15 000 прямо сейчас", "11:03", False),
]

# ── пузыри Telegram (тёмная тема), без фона чата ─────────────────────────────
INB = (30, 41, 54); OUTB = (53, 86, 120); INMUTED = (130, 146, 163); OUTMUTED = (170, 198, 226)
LINK = (110, 180, 255)
BF, LH, PADX, PADY, TEXT_W, RAD = 48, 62, 34, 20, 660, 34
COL_X0, COL_X1 = 50, 830                      # колонка пузырей: справа кнопки Reels (x > 830 при y > 920)
STACK_BOTTOM = 1330                           # низ стопки — под подбородком Ивана (v1.2: фон увеличен ×1,2)
STACK_TOP = 880                               # выше — пузыри уходят (лицо Ивана)


@functools.lru_cache(None)
def f_ui(size, bold=False): return ImageFont.truetype("seguisb.ttf" if bold else "segoeui.ttf", size)


@functools.lru_cache(None)
def f_emo(size): return ImageFont.truetype("seguiemj.ttf", size)


def is_emo(ch): return ord(ch) >= 0x2190 and ch not in "₽—–«»…" and not (0x2000 <= ord(ch) <= 0x206F)


def runs(s):
    out = []
    for ch in s:
        e = is_emo(ch)
        if out and out[-1][0] == e: out[-1][1] += ch
        else: out.append([e, ch])
    return out


def tlen(s, size):
    return sum((f_emo(size) if e else f_ui(size)).getlength(t) for e, t in runs(s))


def draw_text(im, x, y, s, size, fill):
    d = ImageDraw.Draw(im)
    for e, t in runs(s):
        if e:
            d.text((x, y), t, font=f_emo(size), embedded_color=True, anchor="lm"); x += f_emo(size).getlength(t)
        else:
            d.text((x, y), t, font=f_ui(size), fill=fill, anchor="lm"); x += f_ui(size).getlength(t)


def wrap(s, size, w):
    lines, cur = [], ""
    for word in s.split(" "):
        tst = (cur + " " + word).strip()
        if tlen(tst, size) <= w or not cur: cur = tst
        else: lines.append(cur); cur = word
    return lines + [cur]


def checks(d, x, y, col):
    for dx in (0, 11):
        d.line([(x + dx, y), (x + dx + 6, y + 6), (x + dx + 17, y - 7)], fill=col, width=3)


@functools.lru_cache(None)
def preview_thumb(w=460, h=259):
    im = Image.open(SITE[331]).convert("RGB")                  # первый экран «Грани»
    return im.resize((w, h), Image.LANCZOS)


@functools.lru_cache(None)
def bubble(k):
    _, who, text, tm, prev = CHAT[k]; out = who == "out"
    lines = wrap(text, BF, TEXT_W); tf = f_ui(28)
    tw = max(tlen(l, BF) for l in lines)
    tw = max(tw, tlen(lines[-1], BF) + (130 if out else 90))
    pv_h = 0
    if prev:
        tw = max(tw, 500); pv_h = 22 + 40 + 34 + 12 + 259 + 10
    bw = int(tw + 2 * PADX); bh = int(len(lines) * LH + 2 * PADY + 6 + pv_h)
    SS = 2
    im = Image.new("RGBA", (bw * SS, bh * SS)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, bw * SS - 1, bh * SS - 1], RAD * SS, fill=(OUTB if out else INB) + (238,))
    im = im.resize((bw, bh), Image.LANCZOS); d = ImageDraw.Draw(im)
    mut = OUTMUTED if out else INMUTED; y = PADY + LH / 2
    for l in lines:
        draw_text(im, PADX, y, l, BF, (255, 255, 255)); y += LH
    if prev:                                                    # превью ссылки: полоса, название, описание, картинка
        y0 = int(y - LH / 2 + 14)
        d.rounded_rectangle([PADX, y0, PADX + 5, y0 + pv_h - 26], 3, fill=LINK)
        d.text((PADX + 20, y0 + 18), "Грань", font=f_ui(30, True), fill=LINK, anchor="lm")
        d.text((PADX + 20, y0 + 54), "Кольца ручной работы", font=f_ui(28), fill=(235, 240, 245), anchor="lm")
        th = preview_thumb(); m = Image.new("L", th.size, 0)
        ImageDraw.Draw(m).rounded_rectangle([0, 0, th.width - 1, th.height - 1], 16, fill=255)
        im.paste(th, (PADX + 20, y0 + 80), m)
    tx = bw - PADX - tf.getlength(tm) - (34 if out else 0)
    d.text((tx, bh - PADY - 6), tm, font=tf, fill=mut, anchor="lm")
    if out: checks(d, bw - PADX - 26, bh - PADY - 6, mut)
    return im


@functools.lru_cache(None)
def bshadow(k):
    b = bubble(k); sh = Image.new("RGBA", (b.width + 60, b.height + 60))
    ImageDraw.Draw(sh).rounded_rectangle([30, 36, 30 + b.width, 36 + b.height], RAD, fill=(0, 0, 0, 110))
    return sh.filter(ImageFilter.GaussianBlur(14))


def chat_layer(fr, t, ks):
    """Стопка снизу вверх: новое сообщение выезжает снизу и поднимает старые; выше STACK_TOP — гаснут."""
    shown = [k for k in ks if t >= CHAT[k][0]]
    if not shown: return
    # вся стопка едет вверх, пока последнее сообщение выезжает снизу на своё место
    last = shown[-1]; q = eout(prog(t, CHAT[last][0], 0.3))
    off = (bubble(last).height + 16) * (1 - q)
    y = STACK_BOTTOM
    for k in reversed(shown):
        b = bubble(k); y -= b.height; yy = y + off
        out = CHAT[k][1] == "out"
        x = COL_X1 - b.width if out else COL_X0
        a = clamp(1 - (STACK_TOP - yy) / 90) if yy < STACK_TOP else 1.0
        if k == last: a *= clamp(q * 1.4)
        if a > 0:
            put(fr, bshadow(k), x - 30, yy - 30, a * 0.8); put(fr, b, x, yy, a)
        y -= 16


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


BG = Clip(WORK / "bg_sdr.mp4"); MON = Clip(WORK / "mon_sdr.mp4")


@functools.lru_cache(maxsize=4)
def site_img(i):
    return cv2.imread(str(SITE[min(i, len(SITE) - 1)])).astype(np.float32)


def site_at(src):
    a = int(src); w = src - a
    im = site_img(a) if w < 1e-3 else site_img(a) * (1 - w) + site_img(a + 1) * w
    return im


@functools.lru_cache(None)
def screen_geom():
    c = QUAD.mean(0); q = c + (QUAD - c) * (1 + 1.5 / np.linalg.norm(QUAD - c, axis=1, keepdims=True))  # под рамку на 1,5 px
    Hm = cv2.getPerspectiveTransform(np.float32([[0, 0], [1920, 0], [1920, 1080], [0, 1080]]), q)
    m = np.zeros((H * 4, W * 4), np.uint8); cv2.fillPoly(m, [np.round(QUAD * 4).astype(np.int32)], 255, cv2.LINE_AA)
    mask = cv2.resize(m, (W, H), interpolation=cv2.INTER_AREA).astype(np.float32)[..., None] / 255
    # спад яркости экрана к левому нижнему краю (угол обзора), как на исходнике
    yy, xx = np.mgrid[0:1080, 0:1920].astype(np.float32)
    fall = 1.0 - 0.10 * (1 - xx / 1920) * (yy / 1080) - 0.04 * (yy / 1080)
    return Hm, mask, fall[..., None]


RNG = np.random.default_rng(55)


def monitor_frame(t):
    i = int(round(t * FPS)); src = SITE and SRC[min(i, len(SRC) - 1)]
    bg = MON.at(i).astype(np.float32)
    Hm, mask, fall = screen_geom()
    s = site_at(src) * fall
    s = 10 + s * 0.93                                             # экран на камеру: чёрный не чёрный, белый не белый
    s = cv2.GaussianBlur(s, (0, 0), 0.9)
    warped = cv2.warpPerspective(s, Hm, (W, H), flags=cv2.INTER_LINEAR)
    warped += RNG.normal(0, 2.2, warped.shape).astype(np.float32)  # зерно телефона
    out = bg * (1 - mask) + warped * mask
    # медленный наезд к экрану — без статики
    z = 1 + 0.07 * ss(prog(t, 0, MON_D)); cx, cy = 540, 980
    M = np.float32([[z, 0, cx - z * cx], [0, z, cy - z * cy]])
    out = cv2.warpAffine(out, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return Image.fromarray(cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_BGR2RGB)).convert("RGBA")


def bg_frame(t):
    return Image.fromarray(cv2.cvtColor(BG.at(int(round(t * FPS))), cv2.COLOR_BGR2RGB)).convert("RGBA")


@functools.lru_cache(None)
def top_shade():
    im = Image.new("RGBA", (W, H)); a = np.zeros((H, W), np.float32)
    y = np.arange(H, dtype=np.float32)[:, None]
    a += np.clip((y - 820) / 700, 0, 1) * 110                    # затемнение под пузырями
    im.putalpha(Image.fromarray(a.astype(np.uint8).repeat(W, 1) if a.shape[1] == 1 else a.astype(np.uint8)))
    return im


@functools.lru_cache(None)
def note():
    p = WORK / "payment-15000.png"
    if not p.exists():
        import payment_note
        payment_note.make(15000, p)
    im = Image.open(p).convert("RGBA"); w = 880
    im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    sh = Image.new("RGBA", (w + 80, im.height + 80))
    ImageDraw.Draw(sh).rounded_rectangle([40, 50, 40 + w, 50 + im.height], 40, fill=(0, 0, 0, 150))
    sh = sh.filter(ImageFilter.GaussianBlur(18)); sh.alpha_composite(im, (40, 40)); return sh


def scene(t):
    if S_MON <= t < E_MON:
        return monitor_frame(t - S_MON)
    fr = bg_frame(t); fr.alpha_composite(top_shade())
    chat_layer(fr, t, [0, 1])
    if t >= T_NOTE:
        p = eback(prog(t, T_NOTE, 0.45)); n = note()
        put(fr, n, (W - n.width) / 2, 1340 + 140 * (1 - p), clamp(p * 1.5))   # под сообщениями
    return fr


def at(i):
    t = i / FPS
    fr = scene(t).convert("RGB")
    for b in (S_MON,):
        if b - XF < t < b:
            fr = Image.blend(fr, scene(b).convert("RGB"), (t - (b - XF)) / XF)
    return fr


def make_cover():
    """Кольцо в небе на мониторе, без надписей (плашки убраны по решению Ивана 17.11)."""
    k = next(i for i, s in enumerate(SRC) if s >= 225)            # пролёт сквозь кольцо в закат
    fr = monitor_frame(k / FPS)
    fr.convert("RGB").save(OUT / "cover.jpg", quality=95)


def main(peek=None):
    OUT.mkdir(exist_ok=True)
    if peek:
        for s in peek: at(int(s * FPS)).save(WORK / f"peek_{s}.png")
        return
    make_cover()
    sfx = [("sfx-pop.mp3", c[0], 0.2) for c in CHAT] + [("sfx-pop.mp3", S_MON + 0.05, 0.14), ("sfx-click.mp3", T_NOTE, 0.3)]
    ins = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-t", f"{TOT:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
           "-i", str(WORK / "mon_audio.m4a")]
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
        fr = Image.open(OUT / "cover.jpg").convert("RGB") if i == 0 else at(i)
        p.stdin.write(np.ascontiguousarray(np.asarray(fr), np.uint8).tobytes())
    p.stdin.close(); p.wait(); print("done", OUT / "final.mp4", f"{TOT:.2f} s")


if __name__ == "__main__":
    if sys.argv[1:2] == ["peek"]:
        main([float(s) for s in sys.argv[2:]])
    else:
        main()
