"""Ролик «Нет кейса в нише — а предоплата пришла» (сценарий R042), ~9 с, без голоса и без автора.

1. Чат с «Аня · дизайнер»: клиент из пожарной безопасности спрашивает кейсы в нише, а их нет →
   ответ «Попроси Claude собрать концепт-кейс под их нишу. Смотри ↓».
2. Экран Claude (как в R040): печатается промпт, прикрепляются сайт клиента, конкуренты и скилл — всё размыто.
3. Первый экран сайта на весь кадр в окне браузера: проявление, наезд на заголовок, короткий скролл к «О компании».
   Название компании в кадре вымышленное — «ЗАСЛОН» (кадры: Desktop/fire-concept-demo/shots).
4. Снова чат: «Показала как концепт под их компанию — сказали „давайте предоплату“» → уведомление об оплате.

    python r042_niche_case.py              # -> example-r042-niche-case/final.mp4, cover.jpg
    python r042_niche_case.py peek 0.5 3   # кадры work/r042/peek_<t>.png
"""
import sys, pathlib, functools
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r024_site as V                                 # экран Claude (Q) и карточки файлов (P)
from r024_site import Q, P
import r030_silent as B                               # чат с крупным телефоном, плашки, уведомление
import r019_harvi as T
import r025_sales as S
from r014_avito import W, H, FPS, GRAPH, OFF, BLUE, K, clamp, prog, eout, ss, lerp, put, plates, background, xfade

B.WORK = K / "work" / "r042"
B.OUT = pathlib.Path(__file__).resolve().parent / "example-r042-niche-case"
SHOTS = pathlib.Path.home() / "Desktop" / "fire-concept-demo" / "shots"
B.AMOUNT = 38000                                      # своя сумма (в роликах разные, 38 000 ещё не было)

# ── сцены ────────────────────────────────────────────────────────────────────
A = 2.0                                               # конец первого чата
CL = 1.9                                              # экран Claude
G0 = A + CL                                           # первый экран сайта
G1 = G0 + 3.0
T_END = G1 + 0.2                                      # реплика Ани
B.T_NOTE = T_END + 0.55                               # уведомление об оплате
B.TOT = B.T_NOTE + 1.5

T.NAME = "Аня · дизайнер"; T.harvi_avatar = lambda d=128: B.face(K / "work" / "r019" / "av_anna.jpg", d)
T.empty_chat.cache_clear()
if hasattr(T.top_layer, "cache_clear"): T.top_layer.cache_clear()
B.SUBS = ["в сети", "печатает…"]
for s in B.SUBS: T.empty_chat(s); T.top_layer(s)
B.MSGS = [
    (-1.0, "sep", "Сегодня", None, "", None),
    (-1.0, "in", "Клиент — пожарная безопасность, спрашивает: «А кейсы в нашей нише есть?» А у меня ни одного(", None, "18:02", None),
    (0.70, "out", "Попроси Claude собрать концепт-кейс под их нишу. Смотри ↓", None, "18:03", None),
    (T_END, "in", "Показала как концепт под их компанию — сказали «давайте предоплату»!", None, "21:40", None),
]
HOOK = [("Кейс в любой нише —", OFF, GRAPH), ("в 2 клика", BLUE, OFF)]   # правки Ивана 07.11
HOOK_END = 1.75                                       # хук и уведомление об оплате с первого кадра
B.CAPS = [(-1.0, HOOK_END, HOOK),                    # хук виден с первого кадра, без проявления
          (B.T_NOTE, 99, [("Предоплата пришла", BLUE, OFF)])]
B.COVER = HOOK
NOTE_Y = 590                                          # уведомление сразу под плашкой хука
B.sub_at = lambda t: "печатает…" if 0.15 <= t < 0.7 or T_END - 0.45 <= t < T_END else "в сети"

# ── Claude: ниша клиента в промпте + сайт, конкуренты и скилл вложениями, всё размыто ─
Q.PROMPT = ("Клиент — монтаж пожарной сигнализации и пожаротушения под ключ. Вот его сайт и сайты конкурентов. "
            "Собери концепт-кейс: задача, решение и первый экран главной в тёмном премиальном стиле")
P.FILES = [("Сайт клиента", "URL", (200, 60, 50)), ("Конкуренты — 3 сайта", "PDF", (60, 60, 66)),
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
Q.CAPS = [(0.0, CL - 0.2, [("Ниша клиента — в Claude", OFF, GRAPH)])]

# ── первый экран в окне браузера ─────────────────────────────────────────────
WX, WY = 20, 580                                      # окно
WW = W - 2 * WX
BAR = 46                                              # шапка окна
CROP = (95, 1345)                                     # по ширине css: поля страницы по бокам срезаны, контент целиком
VH = round(WW * 900 / (CROP[1] - CROP[0]))            # видимая часть страницы (900 css по высоте)
SCROLL = 430                                          # на сколько px кадра прокрутить к «О компании»
G_CAPS = [(0.05, 99, [("Концепт под нишу —", OFF, GRAPH), ("за вечер", BLUE, OFF)])]
T_SCROLL = (1.75, 0.9)                                # от начала сцены: старт, длительность


@functools.lru_cache(None)
def page():
    im = Image.open(SHOTS / "page-top-1440-scroll.png").convert("RGB")
    k = im.width / 1440; im = im.crop((round(CROP[0] * k), 0, round(CROP[1] * k), im.height))
    return im.resize((WW, round(im.height * WW / im.width)), Image.LANCZOS)


@functools.lru_cache(None)
def chrome():
    """Тень и шапка окна браузера (три точки), без адреса."""
    sh = Image.new("RGBA", (WW + 80, BAR + VH + 80))
    ImageDraw.Draw(sh).rounded_rectangle([40, 52, 40 + WW, 52 + BAR + VH], 26, fill=(0, 0, 0, 170))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    bar = Image.new("RGBA", (WW, BAR), (38, 40, 44, 255)); d = ImageDraw.Draw(bar)
    for j, c in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        d.ellipse([22 + j * 26, BAR // 2 - 8, 38 + j * 26, BAR // 2 + 8], fill=c)
    return sh, bar


def window(t):
    off = round(SCROLL * ss(prog(t, *T_SCROLL)))
    view = page().crop((0, off, WW, off + VH)).convert("RGBA")
    sh, bar = chrome()
    win = Image.new("RGBA", (WW, BAR + VH)); win.paste(bar, (0, 0)); win.paste(view, (0, BAR))
    m = Image.new("L", win.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, WW - 1, BAR + VH - 1], 26, fill=255)
    win.putalpha(m)
    out = sh.copy(); out.alpha_composite(win, (40, 40)); return out


def site_layer(t):
    """Окно появляется с подъёмом, затем короткий скролл."""
    lay = Image.new("RGBA", (W, H))
    p = eout(prog(t, 0.05, 0.4))
    if p <= 0: return lay
    put(lay, window(t), WX - 40, WY - 40 + lerp(60, 0, p), p)   # без наезда: окно и так во всю ширину (правка Ивана 07.11)
    return lay


def site_frame(t):
    fr = background().copy(); fr.alpha_composite(site_layer(t)); S.caps(fr, t, G_CAPS); return fr.convert("RGB")


def hook_note(fr, t):
    """Уведомление об оплате под хуком в начале ролика: стоит с первого кадра, уходит вверх к HOOK_END."""
    o = ss(prog(t, HOOK_END, 0.25))
    if o >= 1: return fr
    fr = fr.convert("RGBA"); n = B.note()
    put(fr, n, (W - n.width) / 2, NOTE_Y - 40 - 160 * o, 1 - o)
    return fr


def at(i):
    t = i / FPS; XF = 0.18
    if t < A:
        fr = B.frame(t, caps=False)
        fr = hook_note(fr, t); S.caps(fr, t, B.CAPS); fr = fr.convert("RGB")
        if t > A - XF: fr = xfade(fr, Q.frame(0), (t - (A - XF)) / XF)
    elif t < G0:
        fr = Q.frame(t - A)
        if t > G0 - XF: fr = xfade(fr, site_frame(0), (t - (G0 - XF)) / XF)
    elif t < G1:
        fr = site_frame(t - G0)
        if t > G1 - XF: fr = xfade(fr, B.frame(G1).convert("RGB"), (t - (G1 - XF)) / XF)
    else:
        fr = B.frame(t).convert("RGB")
    return fr


B.at = at


def make_cover():
    """Обложка: хук и уведомление об оплате над первым экраном сайта."""
    fr = background().copy(); fr.alpha_composite(site_layer(0.6), (0, 510))   # окно ниже хука и оплаты
    plates(fr, B.COVER, 76, 450, lambda k: 1.0)
    n = B.note(); put(fr, n, (W - n.width) / 2, 725 - 40, 1.0)
    fr.convert("RGB").save(B.OUT / "cover.jpg", quality=95)


B.make_cover = make_cover

if __name__ == "__main__":
    if sys.argv[1:2] == ["peek"]:
        B.main([float(s) for s in sys.argv[2:]])
    else:
        B.main()
