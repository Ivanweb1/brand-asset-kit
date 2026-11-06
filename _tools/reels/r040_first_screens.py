"""Ролик «Клиент ждёт концепт завтра — а идей ноль» (сценарий R040), ~9 с, без голоса и без автора.

1. Чат с «Аня · дизайнер»: «Клиент ждёт концепт к утру, а я 6 часов над первым экраном» (с первого кадра) →
   ответ «Так кинь бриф в Claude — он даёт 6 первых экранов. Смотри ↓».
2. Экран Claude (из R024/R028): печатается промпт с брифом, прикрепляются бриф и скиллы — всё размыто.
3. Сетка 2×3 из шести первых экранов барбершопа, собранных Claude по одному брифу
   (Desktop/barber-first-screens-demo/shots), рамка и наезд на №2.
4. Снова чат: «Скинула все шесть — клиент выбрал второй и сразу внёс предоплату!» → уведомление об оплате.

Правки Ивана 06.11: «написать аня дизайнер. показать как вставляю инфу и пишу промпт и прикрепляю скилы в клод,
но все заблюрить. и обязательно плашку оплаты как триггер».

    python r040_first_screens.py              # -> example-r040-first-screens/final.mp4, cover.jpg
    python r040_first_screens.py peek 0.5 3   # кадры work/r040/peek_<t>.png
"""
import sys, pathlib, functools
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r024_site as V                                 # экран Claude (Q) и карточки файлов (P), как в R024/R028
from r024_site import Q, P
import r030_silent as B                               # чат с крупным телефоном, плашки, уведомление
import r019_harvi as T
import r025_sales as S
from r014_avito import W, H, FPS, GRAPH, OFF, BLUE, K, clamp, prog, eout, eback, ss, lerp, put, plates, background, xfade

B.WORK = K / "work" / "r040"
B.OUT = pathlib.Path(__file__).resolve().parent / "example-r040-first-screens"
SHOTS = pathlib.Path.home() / "Desktop" / "barber-first-screens-demo" / "shots"
B.AMOUNT = 55000                                      # своя сумма (в роликах разные: 10–60 тыс. уже заняты)

# ── сцены ────────────────────────────────────────────────────────────────────
A = 2.0                                               # конец первого чата
CL = 1.9                                              # экран Claude
G0 = A + CL                                           # сетка
G1 = G0 + 2.95
T_END = G1 + 0.2                                      # реплика Ани
B.T_NOTE = T_END + 0.55                               # уведомление об оплате
B.TOT = B.T_NOTE + 1.5

# коллега — «Аня · дизайнер»
T.NAME = "Аня · дизайнер"; T.harvi_avatar = lambda d=128: B.face(K / "work" / "r019" / "av_anna.jpg", d)
T.empty_chat.cache_clear()
if hasattr(T.top_layer, "cache_clear"): T.top_layer.cache_clear()
B.SUBS = ["в сети", "печатает…"]
for s in B.SUBS: T.empty_chat(s); T.top_layer(s)
B.MSGS = [
    (-1.0, "sep", "Сегодня", None, "", None),
    (-1.0, "in", "Клиент ждёт концепт главной к утру, а я 6 часов сижу над первым экраном(", None, "22:40", None),
    (0.70, "out", "Так кинь бриф в Claude — он даёт 6 первых экранов. Смотри ↓", None, "22:41", None),
    (T_END, "in", "Скинула все шесть — клиент выбрал второй и сразу внёс предоплату!", None, "23:15", None),
]
B.CAPS = [(0.0, A - 0.1, [("Клиент ждёт концепт завтра —", OFF, GRAPH), ("а идей ноль", BLUE, OFF)]),
          (T_END, B.T_NOTE - 0.15, [("Клиент выбрал второй", BLUE, OFF)]),
          (B.T_NOTE, 99, [("Предоплата пришла", BLUE, OFF)])]
B.COVER = [("Клиент ждёт концепт —", OFF, GRAPH), ("а идей ноль", BLUE, OFF)]
B.sub_at = lambda t: "печатает…" if 0.15 <= t < 0.7 or T_END - 0.45 <= t < T_END else "в сети"

# ── Claude: бриф в промпте + бриф и скиллы вложениями, всё размыто ───────────
Q.PROMPT = ("Вот бриф барбершопа: услуги, аудитория, характер, цель сайта — онлайн-запись. Сделай 6 разных "
            "первых экранов главной: тёмный премиум, журнал, минимализм, винтаж, яркий, коллаж")
P.FILES = [("Бриф барбершопа", "PDF", (200, 60, 50)), ("skill · first-screens", "MD", (60, 60, 66)),
           ("skill · web-design", "MD", (23, 105, 255))]


@functools.lru_cache(None)
def blurred_tile(k): return P.file_card(k).filter(ImageFilter.GaussianBlur(5))


Q.tile = blurred_tile
Q.BLUR_TEXT = True
Q.T_CARD = -1.0
Q.T_TYPE = (0.1, 0.8)
Q.CUR_PLUS = (0.82, 1.0); Q.T_CLICK_PLUS = 1.03
Q.T_REFS = [1.08, 1.2, 1.32]
Q.CUR_SEND = (1.38, 1.58); Q.T_SEND = 1.6
Q.T_VIEW = 99.0
Q.CAPS = [(0.0, CL - 0.2, [("Бриф и скиллы — в Claude", OFF, GRAPH)])]

# ── сетка 2×3 ────────────────────────────────────────────────────────────────
GX, GAP, GY = 44, 20, 640
TW = (W - 2 * GX - GAP) // 2; TH = round(TW * 900 / 1440)
FILES = ["s1-dark-premium", "s2-magazine", "s3-light-minimal", "s4-vintage", "s5-bold", "s6-collage"]
PICK = 1                                              # клиент выбрал второй
G_CAPS = [(0.05, 99, [("6 первых экранов", OFF, GRAPH), ("из одного брифа", BLUE, OFF)])]
T_PICK = 1.75                                         # от начала сетки


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
    """t — от начала сетки. Плитки по одной (0,25 с), на T_PICK рамка и мягкий наезд к №2."""
    lay = Image.new("RGBA", (W, H))
    for i in range(6):
        p = prog(t, 0.1 + 0.25 * i, 0.3)
        if p <= 0: continue
        sp = tile(i); s = lerp(0.82, 1.0, eback(p))
        sp = sp.resize((int(sp.width * s), int(sp.height * s)), Image.BICUBIC)
        x, y = pos(i); put(lay, sp, x - 30 + (TW + 60) * (1 - s) / 2, y - 30 + (TH + 60) * (1 - s) / 2, eout(clamp(p * 1.6)))
    hp = eout(prog(t, T_PICK, 0.3))
    if hp > 0:
        x, y = pos(PICK)
        ImageDraw.Draw(lay).rounded_rectangle([x - 8, y - 8, x + TW + 8, y + TH + 8], 24, outline=BLUE + (int(255 * hp),), width=8)
    z = 1 + 0.07 * ss(prog(t, T_PICK, 1.2))
    if z > 1:
        x, y = pos(PICK); cx, cy = (W / 2 + x + TW / 2) / 2, y + TH / 2
        lay = lay.resize((round(W * z), round(H * z)), Image.BICUBIC)
        ox, oy = cx * z - cx, cy * z - cy
        lay = lay.crop((int(ox), int(oy), int(ox) + W, int(oy) + H))
    return lay


def grid_frame(t):
    fr = background().copy(); fr.alpha_composite(grid_layer(t)); S.caps(fr, t, G_CAPS); return fr.convert("RGB")


def at(i):
    t = i / FPS; XF = 0.18
    if t < A:
        fr = B.frame(t).convert("RGB")
        if t > A - XF: fr = xfade(fr, Q.frame(0), (t - (A - XF)) / XF)
    elif t < G0:
        fr = Q.frame(t - A)
        if t > G0 - XF: fr = xfade(fr, grid_frame(0), (t - (G0 - XF)) / XF)
    elif t < G1:
        fr = grid_frame(t - G0)
        if t > G1 - XF: fr = xfade(fr, B.frame(G1).convert("RGB"), (t - (G1 - XF)) / XF)
    else:
        fr = B.frame(t).convert("RGB")
    return fr


B.at = at


def make_cover():
    """Обложка: хук над сеткой из шести экранов (до рамки на №2)."""
    fr = background().copy(); fr.alpha_composite(grid_layer(T_PICK - 0.05))
    plates(fr, B.COVER, 76, 450, lambda k: 1.0)
    fr.convert("RGB").save(B.OUT / "cover.jpg", quality=95)


B.make_cover = make_cover

if __name__ == "__main__":
    if sys.argv[1:2] == ["peek"]:
        B.main([float(s) for s in sys.argv[2:]])
    else:
        B.main()
