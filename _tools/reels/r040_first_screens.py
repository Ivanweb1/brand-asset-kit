"""Ролик «Клиент ждёт концепт завтра — а идей ноль» (сценарий R040), ~9 с, без голоса и без автора.

Чат с коллегой Аней: «Клиент ждёт концепт к утру, а я 6 часов над первым экраном» (с первого кадра) →
ответ «Так кинь бриф в Claude — он даёт 6 первых экранов. Смотри ↓» → на весь кадр сетка 2×3 из шести
первых экранов барбершопа, собранных Claude по одному брифу (Desktop/barber-first-screens-demo/shots) →
наезд и рамка на №2 → снова чат: «Клиент выбрал второй и сразу внёс предоплату!» → конец.

Уведомление об оплате не ставим, пока Иван не назовёт сумму: задать AMOUNT и NOTE = True.

Обёртка над r030_silent (крупный телефон, плашки) + своя сцена сетки.

    python r040_first_screens.py              # -> example-r040-first-screens/final.mp4, cover.jpg
    python r040_first_screens.py peek 0.5 3   # кадры work/r040/peek_<t>.png
"""
import sys, pathlib, functools
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r030_silent as B
import r019_harvi as T
import r025_sales as S
from r014_avito import W, H, GRAPH, OFF, BLUE, K, clamp, prog, eout, eback, ss, lerp, put, plates, background

B.WORK = K / "work" / "r040"
B.OUT = pathlib.Path(__file__).resolve().parent / "example-r040-first-screens"
SHOTS = pathlib.Path.home() / "Desktop" / "barber-first-screens-demo" / "shots"

NOTE = False                                          # уведомление об оплате — только с суммой от Ивана
B.AMOUNT = 0

# коллега — Аня, дизайнер
T.NAME = "Аня"; T.harvi_avatar = lambda d=128: B.face(K / "work" / "r019" / "av_anna.jpg", d)
T.empty_chat.cache_clear()
if hasattr(T.top_layer, "cache_clear"): T.top_layer.cache_clear()
B.SUBS = ["в сети", "печатает…"]
for s in B.SUBS: T.empty_chat(s); T.top_layer(s)

G0, G1 = 2.0, 5.75                                    # сцена сетки
T_END = 6.05                                          # финальная реплика Ани
B.T_NOTE = T_END                                     # после реплики — лёгкий наезд из r030 (без статики)
B.TOT = T_END + 2.4
if not NOTE: B.note = lambda: Image.new("RGBA", (8, 8))
B.MSGS = [
    (-1.0, "sep", "Сегодня", None, "", None),
    (-1.0, "in", "Клиент ждёт концепт главной к утру, а я 6 часов сижу над первым экраном(", None, "22:40", None),
    (0.70, "out", "Так кинь бриф в Claude — он даёт 6 первых экранов. Смотри ↓", None, "22:41", None),
    (T_END, "in", "Скинула все шесть — клиент выбрал второй и сразу внёс предоплату!", None, "23:15", None),
]
B.CAPS = [(0.0, G0 - 0.1, [("Клиент ждёт концепт завтра —", OFF, GRAPH), ("а идей ноль", BLUE, OFF)]),
          (G0 + 0.05, G1 - 0.15, [("6 первых экранов", OFF, GRAPH), ("из одного брифа", BLUE, OFF)]),
          (G1 + 0.15, 99, [("Клиент выбрал второй", BLUE, OFF)])]
B.COVER = [("Клиент ждёт концепт —", OFF, GRAPH), ("а идей ноль", BLUE, OFF)]
B.sub_at = lambda t: "печатает…" if 0.15 <= t < 0.7 or 5.6 <= t < T_END else "в сети"

# ── сетка 2×3 ────────────────────────────────────────────────────────────────
GX, GAP, GY = 44, 20, 640
TW = (W - 2 * GX - GAP) // 2; TH = round(TW * 900 / 1440)
FILES = ["s1-dark-premium", "s2-magazine", "s3-light-minimal", "s4-vintage", "s5-bold", "s6-collage"]
PICK = 1                                              # клиент выбрал второй


@functools.lru_cache(None)
def tile(i):
    im = Image.open(SHOTS / f"{FILES[i]}.png").convert("RGB").resize((TW, TH), Image.LANCZOS).convert("RGBA")
    m = Image.new("L", (TW, TH), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, TW - 1, TH - 1], 18, fill=255)
    im.putalpha(m)
    sh = Image.new("RGBA", (TW + 60, TH + 60)); ImageDraw.Draw(sh).rounded_rectangle([30, 38, 30 + TW, 38 + TH], 18, fill=(0, 0, 0, 160))
    sh = sh.filter(ImageFilter.GaussianBlur(14)); sh.alpha_composite(im, (30, 30)); return sh


def pos(i):
    r, c = divmod(i, 2); return GX + c * (TW + GAP), GY + r * (TH + GAP)


def grid_layer(t):
    """Плитки появляются по одной (0,32 с), на 4,3 с наезд на №2 и синяя рамка."""
    lay = Image.new("RGBA", (W, H))
    for i in range(6):
        p = prog(t, G0 + 0.15 + 0.32 * i, 0.3)
        if p <= 0: continue
        sp = tile(i); s = lerp(0.82, 1.0, eback(p))
        sp = sp.resize((int(sp.width * s), int(sp.height * s)), Image.BICUBIC)
        x, y = pos(i); put(lay, sp, x - 30 + (TW + 60) * (1 - s) / 2, y - 30 + (TH + 60) * (1 - s) / 2, eout(clamp(p * 1.6)))
    hp = eout(prog(t, 4.35, 0.3))
    if hp > 0:
        x, y = pos(PICK); d = ImageDraw.Draw(lay)
        d.rounded_rectangle([x - 8, y - 8, x + TW + 8, y + TH + 8], 24, outline=BLUE + (int(255 * hp),), width=8)
    z = 1 + 0.07 * ss(prog(t, 4.35, 1.2))             # мягкий наезд к выбранному экрану
    if z > 1:
        x, y = pos(PICK); cx, cy = (W / 2 + x + TW / 2) / 2, y + TH / 2
        lay = lay.resize((round(W * z), round(H * z)), Image.BICUBIC)
        ox, oy = cx * z - cx, cy * z - cy
        lay = lay.crop((int(ox), int(oy), int(ox) + W, int(oy) + H))
    return lay


_frame = B.frame


def frame(t, caps=True, note_y=600):
    if t < G0 - 0.05 or t >= G1 + 0.3 or not caps:
        return _frame(t, caps, note_y)
    chat = _frame(t, False, note_y)                  # телефон уходит под сетку
    fr = background().copy()
    a = eout(prog(t, G0 - 0.05, 0.3)) * (1 - eout(prog(t, G1, 0.3)))
    fr = Image.blend(chat.convert("RGBA"), fr, a)
    fr.alpha_composite(grid_layer(t)) if a >= 0.99 else put(fr, grid_layer(t), 0, 0, a)
    S.caps(fr, t, B.CAPS)
    return fr


B.frame = frame


def make_cover():
    """Обложка: хук над сеткой из шести экранов (до рамки на №2)."""
    fr = background().copy(); fr.alpha_composite(grid_layer(4.3))
    plates(fr, B.COVER, 76, 450, lambda k: 1.0)
    fr.convert("RGB").save(B.OUT / "cover.jpg", quality=95)


B.make_cover = make_cover

if __name__ == "__main__":
    if sys.argv[1:2] == ["peek"]:
        B.main([float(s) for s in sys.argv[2:]])
    else:
        B.main()
