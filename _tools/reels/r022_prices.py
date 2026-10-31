"""Ролик «Цены конкурентов» — Харви присылает отчёт по конкурентам (сценарий R022).

Аватар, сверху сообщение покупателя «В магазине 1 на 2 000 дешевле. Сделаете скидку?» →
«Конкурент снизил цену, а вы узнаёте об этом от покупателя?» → «ИИ-агент может каждый день проверять
цены конкурентов и присылать вам отчёт.» → чат Telegram «Харви» (из r019_harvi.py): отчёт за ночь,
кнопки «История цен / Таблица», нажатие → график за 30 дней → аватар: «Хотите такого агента?
Напишите «ЦЕНЫ» в директ.»

Магазины вымышленные и размыты (решение Ивана), цены постановочные.

Исходники (не публикуются) — work/r022/: heygen-full.mp4 → hook.mp4 (фразы 1–2), cta.mp4 (фраза 3);
clip.json — тайминги слов.

    python r022_prices.py screen 1 3 6   # кадры экрана work/r022/screen_<t>.png
    python r022_prices.py peek 1 5 9     # кадры ролика work/r022/peek_<t>.png
    python r022_prices.py                # -> example-r022-prices/final.mp4, cover.jpg
"""
import os, sys, json, pathlib, functools, subprocess
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r019_harvi as T
from r019_harvi import (SW, TXT, ui, top_layer, bottom_layer, chat_bg, card_mask, card_shadow,
                        CX0, CY0, CW, CHH, SHW, MSG_Y0, MSG_Y1, INB, INMUTED)
import r014_avito as R
from r014_avito import (W, H, FPS, GRAPH, OFF, BLUE, SS, clamp, prog, eout, ss, eback, lerp,
                        put, plates, font, down, background, Clip, avatar_frame, xfade)
import r020_reviews as V                    # кнопки, нажатие, сборка звука — как в R020

K = T.K
WORK = pathlib.Path(os.environ.get("R022_WORK", K / "work" / "r022"))
OUT = pathlib.Path(__file__).resolve().parent / "example-r022-prices"
R.CLIP_DIR = WORK

# ── аватар (по расшифровке, work/r022/clip.json) ──────────────────────────────
HOOK_SUB = [[("Конкурент", .3), ("снизил", .8), ("цену,", 1.1)], [("а", 1.4), ("вы", 1.5), ("узнаёте", 1.7), ("об", 2.1), ("этом", 2.2)],
            [("от", 2.5), ("покупателя?", 2.6)], [("ИИ-агент", 3.6), ("может", 4.2)], [("каждый", 4.5), ("день", 4.8), ("проверять", 5.0)],
            [("цены", 5.5), ("конкурентов", 5.8)], [("и", 6.5), ("присылать", 6.6), ("вам", 7.1), ("отчёт.", 7.3)]]
T_BRIDGE = 3.5                              # начало фразы про ИИ-агента — сообщение покупателя уходит, наезд
CTA_SUB = [[("Хотите", .2), ("такого", .5), ("агента?", .8)], [("Напишите", 1.4), ("«ЦЕНЫ»", 1.8)], [("в", 2.3), ("директ.", 2.4)]]
CTA_PL_AT = [.2, 1.8]; T_PUSH_CTA = 1.8; HOLD = 0.45
COVER_T = 0.6
COVER = [("Конкурент", OFF, GRAPH), ("снизил цену,", OFF, GRAPH), ("а вы не в курсе?", BLUE, OFF)]   # строки в полях 160 px (RULES §4)
if (WORK / "clip.json").exists():
    _c = json.load(open(WORK / "clip.json", encoding="utf-8"))
    HOOK_SUB = [[tuple(w) for w in ln] for ln in _c["hook_sub"]]
    CTA_SUB = [[tuple(w) for w in ln] for ln in _c["cta_sub"]]
    T_BRIDGE = _c["bridge"]; CTA_PL_AT = _c["cta_pl"]; T_PUSH_CTA = _c.get("push_cta", CTA_PL_AT[1])
    COVER_T = _c.get("cover_t", COVER_T)
CTA_PL = [(CTA_PL_AT[0], 99, [("Хотите такого агента?", OFF, GRAPH), ("«ЦЕНЫ» в директ", BLUE, OFF)], CTA_PL_AT)]

# ── экран ────────────────────────────────────────────────────────────────────
# экран идёт под фразу «ИИ-агент может…» и кончается сразу после неё — без тишины (Иван: «таких пауз не должно быть»)
T_REPORT = 0.3
WRITING = [(0.0, 0.3)]
T_KB = 0.6
T_TAP = 2.45
T_CHART = 2.85
CH = 4.4
CAPS = [(0.15, 2.3, [("Цены конкурентов —", OFF, GRAPH), ("каждое утро", BLUE, OFF)]),
        (2.5, CH - 0.15, [("Где ваш товар дороже —", OFF, GRAPH), ("сразу видно", BLUE, OFF)])]
RED = (255, 99, 92); GREEN = (76, 196, 110); PAD, RAD = 34, 38
ROWS = [("down", "{ТехноМир} — кофемашина", "41 990 → 39 990 ₽", "−5%"),      # {…} — размыто (решение Ивана)
        ("up", "{Кофе Лаб} — кофемолка", "4 490 → 4 990 ₽", "+11%"),
        ("same", "{Бариста Маркет}", "без изменений", "")]


def arrow(d, cx, cy, kind, r=16):
    if kind == "down": d.polygon([(cx - r, cy - r * 0.6), (cx + r, cy - r * 0.6), (cx, cy + r * 0.8)], fill=RED)
    elif kind == "up": d.polygon([(cx - r, cy + r * 0.6), (cx + r, cy + r * 0.6), (cx, cy - r * 0.8)], fill=GREEN)
    else: d.rounded_rectangle([cx - r, cy - 4, cx + r, cy + 4], 3, fill=INMUTED)


@functools.lru_cache(None)
def report_bubble():
    bw = 1000; bh = 74 + len(ROWS) * 104 + 30 + 110 + 50
    im = Image.new("RGBA", (SW, bh)); d = ImageDraw.Draw(im); x0 = 24
    d.rounded_rectangle([x0, 0, x0 + bw, bh], RAD, fill=INB + (255,))
    d.text((x0 + PAD, 50), "Цены конкурентов за ночь", font=ui(42), fill=TXT, anchor="lm")
    y = 100
    for kind, name, val, pct in ROWS:
        arrow(d, x0 + PAD + 18, y + 22, kind)
        T.rich_text(im, d, x0 + PAD + 56, y + 22, name, ui(38, False), TXT)
        col = RED if kind == "down" else GREEN if kind == "up" else INMUTED
        d.text((x0 + PAD + 56, y + 68), val, font=ui(38), fill=TXT if kind != "same" else INMUTED, anchor="lm")
        if pct: d.text((x0 + bw - PAD, y + 68), pct, font=ui(38), fill=col, anchor="rm")
        y += 104
    y += 14
    d.rounded_rectangle([x0 + 18, y, x0 + bw - 18, y + 100], 18, fill=(70, 40, 46, 255))
    d.text((x0 + PAD + 10, y + 50), "Ваша кофемашина дороже на 2 000 ₽", font=ui(40), fill=(255, 190, 186), anchor="lm")
    d.text((x0 + bw - PAD, bh - 30), "09:00", font=ui(30, False), fill=INMUTED, anchor="rm")
    return im


KB_H = V.KB_H


@functools.lru_cache(None)
def keyboard(pressed=-1):
    labels = ["История цен", "Таблица"]; ws = [520, 386]; gap = 12; x = 24
    im = Image.new("RGBA", (SW, KB_H)); d = ImageDraw.Draw(im)
    for k, (s, w) in enumerate(zip(labels, ws)):
        d.rounded_rectangle([x, 8, x + w, KB_H - 4], 24, fill=((110, 175, 255, 255) if k == pressed else (40, 54, 72, 235)))
        d.text((x + w / 2, (KB_H + 4) / 2), s, font=ui(38), fill=(255, 255, 255), anchor="mm"); x += w + gap
    return im


@functools.lru_cache(None)
def chart_bubble():
    """График цены кофемашины за 30 дней: конкуренты серые, ваша цена синяя."""
    bw, ph = 1000, 420; bh = ph + 140
    im = Image.new("RGBA", (SW, bh)); d = ImageDraw.Draw(im); x0 = 24
    d.rounded_rectangle([x0, 0, x0 + bw, bh], RAD, fill=INB + (255,))
    d.text((x0 + PAD, 48), "Кофемашина · 30 дней", font=ui(40), fill=TXT, anchor="lm")
    gx0, gx1, gy0, gy1 = x0 + PAD + 110, x0 + bw - PAD - 20, 100, 100 + ph - 60
    lo, hi = 38500, 44000
    Y = lambda v: gy1 - (v - lo) / (hi - lo) * (gy1 - gy0)
    for v in (39000, 41000, 43000):
        d.line([(gx0, Y(v)), (gx1, Y(v))], fill=(50, 64, 82), width=2)
        d.text((gx0 - 14, Y(v)), f"{v // 1000} {v % 1000:03d}", font=ui(28, False), fill=INMUTED, anchor="rm")
    n = 30; X = lambda i: gx0 + (gx1 - gx0) * i / (n - 1)
    series = [
        ([43190] * 16 + [42690] * 12 + [39990] * 2, RED, "{ТехноМир}"),
        ([43490] * 8 + [43990] * 14 + [43490] * 8, (130, 140, 155), "{Кофе Лаб}"),
        ([42290] * 30, (100, 110, 125), "{Бариста Маркет}"),
        ([41990] * 30, (110, 175, 255), "Вы"),
    ]
    for vals, col, _ in series:
        pts = []
        for i, v in enumerate(vals):
            if pts and Y(v) != pts[-1][1]: pts.append((X(i), pts[-1][1]))
            pts.append((X(i), Y(v)))
        d.line(pts, fill=col, width=7 if col[2] == 255 and col[0] == 110 else 5, joint="curve")
    d.ellipse([X(29) - 11, Y(39990) - 11, X(29) + 11, Y(39990) + 11], fill=RED)
    d.ellipse([X(29) - 11, Y(41990) - 11, X(29) + 11, Y(41990) + 11], fill=(110, 175, 255))
    lx = x0 + PAD; ly = bh - 46
    for _, col, name in series:
        d.rounded_rectangle([lx, ly - 6, lx + 30, ly + 6], 4, fill=col)
        T.rich_text(im, d, lx + 40, ly, name, ui(30, False), TXT); lx += 60 + ui(30, False).getlength(T.plain(name)) + 24
    return im


def screen(t):
    sub = "бот"
    for a, b in WRITING:
        if a <= t < b: sub = "печатает" + "." * (int((t - a) * 4) % 4)
    im = chat_bg().copy(); items, y, gap = [], 30, 18
    if t >= T_REPORT:
        b = report_bubble(); items.append((b, y, prog(t, T_REPORT, 0.32))); y += lerp(0, b.height + gap, eout(prog(t, T_REPORT, 0.28)))
    if t >= T_KB:
        kb = keyboard(0 if T_TAP <= t < T_TAP + 0.35 else -1)
        items.append((kb, y - gap + 6, prog(t, T_KB, 0.3))); y += lerp(0, KB_H + gap, eout(prog(t, T_KB, 0.28)))
    kb_y = y - KB_H - gap
    if t >= T_CHART:
        b = chart_bubble(); items.append((b, y, prog(t, T_CHART, 0.32))); y += lerp(0, b.height + gap, eout(prog(t, T_CHART, 0.28)))
    shift = max(0, y - gap - (MSG_Y1 - MSG_Y0 - 10))
    for spr, yy, p in items:
        if p >= 1: put(im, spr, 0, MSG_Y0 + yy - shift)
        else:
            s = lerp(0.9, 1.0, eback(p)); sp = spr.resize((int(spr.width * s), max(1, int(spr.height * s))), Image.BICUBIC)
            put(im, sp, (SW - sp.width) / 2, MSG_Y0 + yy - shift + (spr.height - sp.height) / 2 + 24 * (1 - eout(p)), eout(p * 1.6))
    if T_TAP - 0.35 <= t < T_TAP + 0.45:      # нажатие на «История цен»
        bx, by = 24 + 260, MSG_Y0 + kb_y - shift + KB_H / 2 + 6
        p = prog(t, T_TAP - 0.35, 0.35); a = clamp(p * 2) * (1 - prog(t, T_TAP + 0.2, 0.25))
        r = lerp(70, 44, eout(p)); dot = Image.new("RGBA", (200, 200)); ImageDraw.Draw(dot).ellipse([100 - r, 100 - r, 100 + r, 100 + r], fill=(255, 255, 255, 110))
        put(im, dot, bx - 100, by - 100, a)
    im.alpha_composite(top_layer(sub), (0, 0))
    im.alpha_composite(bottom_layer(), (0, SHW - bottom_layer().height))
    return im


def screen_frame(t):
    fr = background().copy()
    wp = eout(prog(t, 0, 0.5)); y = CY0 + 520 * (1 - wp)
    c = screen(t).resize((CW, CHH), Image.LANCZOS); c.putalpha(card_mask())
    ImageDraw.Draw(c).rounded_rectangle([0, 0, CW - 1, CHH - 1], 44, outline=(255, 255, 255, 40), width=2)
    put(fr, card_shadow(), CX0 - 80, y - 100, wp); put(fr, c, CX0, y, wp)
    for a, b, rows in CAPS:
        if a <= t < b + 0.3:
            o = ss(prog(t, b, 0.25))
            plates(fr, rows, 60, 356, lambda k: clamp(prog(t, a + 0.1 * k, 0.35) - o))
    return fr.convert("RGB")


# ── сообщение покупателя над аватаром ─────────────────────────────────────────
@functools.lru_cache(None)
def buyer_msg():
    w, h = 880, 168; im = Image.new("RGBA", (w * SS, h * SS)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * SS - 1, h * SS - 1], 40 * SS, fill=(36, 37, 41, 250), outline=(255, 255, 255, 30), width=2 * SS)
    r = 44 * SS; cx, cy = 30 * SS + r, h * SS / 2
    ph = Image.open(K / "work" / "r018" / "av_dmitry.jpg").convert("RGB")
    s = ph.width * 0.62; ph = ph.crop(((ph.width - s) / 2, ph.height * 0.02, (ph.width + s) / 2, ph.height * 0.02 + s)).resize((2 * r, 2 * r), Image.LANCZOS)
    m = Image.new("L", (2 * r, 2 * r), 0); ImageDraw.Draw(m).ellipse([0, 0, 2 * r - 1, 2 * r - 1], fill=255)
    im.paste(ph, (int(cx - r), int(cy - r)), m)
    tx = cx + r + 24 * SS
    d.text((tx, 44 * SS), "Дмитрий", font=font("Bold", 30 * SS), fill=(250, 250, 250, 255), anchor="lm")
    d.text(((w - 30) * SS, 44 * SS), "сейчас", font=font("Medium", 22 * SS), fill=(160, 160, 165, 255), anchor="rm")
    T.rich_text(im, d, tx, 92 * SS, "В {«ТехноМире»} на 2 000 дешевле.", font("Medium", 30 * SS), (225, 225, 228, 255), pad=6 * SS, r=11 * SS)
    d.text((tx, 132 * SS), "Сделаете скидку?", font=font("Medium", 30 * SS), fill=(225, 225, 228, 255), anchor="lm")
    return down(im)


T_MSG = 0.05


def hook_frame(clip, t, dur):
    R.FACE_AT = (540, 1010)
    fr = avatar_frame(clip.at(int(t * FPS)), t, dur, HOOK_SUB, [])
    R.FACE_AT = (540, 870)
    fr = fr.convert("RGBA"); n = buyer_msg()
    p = eback(prog(t, T_MSG, 0.45)) - 1.2 * ss(prog(t, dur - 0.3, 0.3))
    if p > -0.2: put(fr, n, (W - n.width) / 2, 420 - 260 * (1 - p), clamp(p * 1.5))
    return fr.convert("RGB")


def clen(name):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                 str(WORK / f"{name}.mp4")], capture_output=True, text=True).stdout)


def make_cover():
    src = Clip("hook").at(int(COVER_T * FPS)); z = 1.4
    x0 = clamp(R.FACE[0] - 540 / z, 0, W - W / z); y0 = clamp(R.FACE[1] - 1190 / z, 0, H - H / z)
    fr = src.transform((W, H), Image.AFFINE, (1 / z, 0, x0, 0, 1 / z, y0), Image.BICUBIC).convert("RGBA")
    plates(fr, COVER, 84, 560, lambda k: 1.0)
    fr.convert("RGB").save(OUT / "cover.jpg", quality=95)


def main(peek=None):
    OUT.mkdir(exist_ok=True)
    # экран — сразу на словах «ИИ-агент…» (решение Ивана): видео аватара обрывается на T_BRIDGE,
    # голос этой фразы идёт дальше поверх экрана
    A = T_BRIDGE; Bo = clen("cta") + HOLD; TOT = A + CH + Bo; XF = R.XF
    assert CH >= clen("hook") - A, "экран короче фразы про агента"
    hook, cta = Clip("hook"), Clip("cta"); last = int((Bo - HOLD) * FPS) - 1

    def at(i):
        t = i / FPS
        if t < A:
            fr = hook_frame(hook, t, A)
            if t > A - XF: fr = xfade(fr, screen_frame(0), (t - (A - XF)) / XF)
        elif t < A + CH:
            fr = screen_frame(t - A)
        else:
            tb = t - A - CH
            fr = avatar_frame(cta.at(min(int(tb * FPS), last)), tb, Bo, CTA_SUB, CTA_PL, T_PUSH_CTA)
            if tb < XF: fr = xfade(screen_frame(CH), fr, tb / XF)
        return fr

    if peek:
        for i in range(int(max(peek) * FPS) + 1):
            fr = at(i)
            for s in peek:
                if int(s * FPS) == i: fr.save(WORK / f"peek_{s}.png")
        return
    sfx = [("sfx-pop.mp3", T_MSG, 0.25), ("sfx-pop.mp3", A + T_REPORT, 0.16), ("sfx-click.mp3", A + T_TAP, 0.25),
           ("sfx-pop.mp3", A + T_CHART, 0.16)]
    ins = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-f", "lavfi", "-t", f"{TOT:.3f}", "-i", "anullsrc=r=48000:cl=stereo",
           "-i", str(WORK / "hook.mp4"), "-i", str(WORK / "cta.mp4")]
    oms = int((A + CH) * 1000)
    fl = ["[2:a]loudnorm=I=-14:TP=-1.5,aformat=sample_rates=48000:channel_layouts=stereo[v0]",
          f"[3:a]loudnorm=I=-14:TP=-1.5,aformat=sample_rates=48000:channel_layouts=stereo,adelay={oms}|{oms}[v1]"]
    labs = ["[v0]", "[v1]"]
    for j, (f, t, v) in enumerate(sfx):
        ins += ["-i", str(K / "11_MOTION" / f)]; ms = int(t * 1000)
        fl.append(f"[{j + 4}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={v},adelay={ms}|{ms}[s{j}]")
        labs.append(f"[s{j}]")
    fl.append(f"[1:a]{''.join(labs)}amix=inputs={1 + len(labs)}:normalize=0:duration=first,alimiter=limit=0.95[a]")
    cmd = ["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fl), "-map", "0:v", "-map", "[a]",
           "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-profile:v", "high", "-pix_fmt", "yuv420p",
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(OUT / "final.mp4")]
    make_cover()
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(int(round(TOT * FPS))):
        fr = Image.open(OUT / "cover.jpg").convert("RGB") if i == 0 else at(i)
        p.stdin.write(np.ascontiguousarray(np.asarray(fr.convert("RGB")), np.uint8).tobytes())
    p.stdin.close(); p.wait(); print("done", OUT / "final.mp4", f"{TOT:.2f} s")


if __name__ == "__main__":
    WORK.mkdir(parents=True, exist_ok=True)
    if sys.argv[1:2] == ["screen"]:
        for s in sys.argv[2:]: screen_frame(float(s)).save(WORK / f"screen_{s}.png")
    elif sys.argv[1:2] == ["peek"]:
        main([float(s) for s in sys.argv[2:]])
    else:
        main()
