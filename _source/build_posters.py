"""08_SOCIAL_TEMPLATES/posters — серия постеров-манифестов по сетке утверждённых постеров:
поля 15% ширины, заголовок Medium 13% ширины с интерлиньяжем 0.89, дескриптор SemiBold 3.8% внизу."""
from kit import C, rect, text, measure, cap, heavy_frame, logo, save, rich

G, W, B = C["graphite"], C["offwhite"], C["blue"]
SIZES = [(990, 1400, "a-poster"), (1080, 1350, "post-1080x1350"), (1080, 1920, "story-1080x1920")]


class P:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.m = round(w * 0.1515)
        self.hs = w * 0.13            # кегль заголовка
        self.ds = w * 0.0384          # кегль дескриптора
        self.top = h * (0.155 if h / w > 1.3 else 0.13)
        self.desc_y = h * 0.854 if h / w < 1.6 else h * 0.78


def desc(p, rows, fill):
    return "".join(text(p.m, p.desc_y + i * p.ds * 1.21, r, p.ds, 600, fill) for i, r in enumerate(rows))


def block(p, y, rows, fill, size=None, lh=0.89):
    """rows: строки или rich-части. y — верх первой прописной. Возвращает (svg, y следующей группы)."""
    size = size or p.hs
    from kit import rich_width
    maxw = p.w - p.m - p.m * 0.55   # справа поле можно сузить, как на постере «технология»
    widest = max(rich_width([(r, None)] if isinstance(r, str) else r, size, 800, -0.02) for r in rows)
    size = min(size, size * maxw / widest)
    out = ""
    for i, r in enumerate(rows):
        parts = [(r, None)] if isinstance(r, str) else r
        out += rich(p.m, y + cap(size) + i * size * lh, parts, size, 800, fill, -0.02)
    return out, y + len(rows) * size * lh + size * 0.47


def strike(p, y, word, size, col):
    """Зачёркнутое слово — четвёртый приём: «ручной режим» перечёркнут синим."""
    w = measure(word, size, 800, -0.02) - (-0.02 * size)
    bar = size * 0.12
    return rect(p.m - size * 0.04, y + cap(size) * 0.52 - bar / 2, w + size * 0.08, bar, bar * 0.3, B) if col else ""


POSTERS = {}


def poster(name, desc_):
    def deco(fn):
        POSTERS[name] = (desc_, fn)
        return fn
    return deco


@poster("logo", "Постер: знак (утверждённый)")
def _(p):
    s = p.w - 2 * p.m
    return rect(0, 0, p.w, p.h, 0, W) + logo(p.m, p.h * 0.18, s, G, B) + desc(p, ["АВТОМАТИЗАЦИЯ", "БИЗНЕС-ПРОЦЕССОВ"], G)


@poster("slogan", "Постер: ключевая фраза (утверждённый)")
def _(p):
    out = rect(0, 0, p.w, p.h, 0, G)
    b1, y = block(p, p.top, ["Сначала", "процесс"], W)
    b2, _ = block(p, y, ["Потом", "технология"], B)
    return out + b1 + b2 + desc(p, ["АВТОМАТИЗИРУЮ", "БИЗНЕС-ПРОЦЕССЫ"], W)


@poster("manual-off", "Постер: зачёркнутый ручной режим")
def _(p):
    out = rect(0, 0, p.w, p.h, 0, G)
    y0 = p.top
    for i, wd in enumerate(("Ручной", "режим")):
        yy = y0 + i * p.hs * 0.89
        out += text(p.m, yy + cap(p.hs), wd, p.hs, 800, C["graphite_muted"], ls=-0.02) + strike(p, yy, wd, p.hs, True)
    b, _ = block(p, y0 + 2 * p.hs * 0.89 + p.hs * 0.47, ["Выключаем."], W)
    return out + b + desc(p, ["АВТОМАТИЗИРУЮ", "БИЗНЕС-ПРОЦЕССЫ"], W)


@poster("into-system", "Постер: синий, «в систему»")
def _(p):
    out = rect(0, 0, p.w, p.h, 0, B)
    b1, y = block(p, p.top, ["Из ручных", "процессов —"], W)
    b2, _ = block(p, y, ["в систему"], G)
    return out + b1 + b2 + desc(p, ["АВТОМАТИЗАЦИЯ", "БИЗНЕС-ПРОЦЕССОВ"], W)


@poster("giant-module", "Постер: гигантский модуль")
def _(p):
    s = p.w * 0.9
    x0, y0 = p.m, p.h * 0.12
    out = rect(0, 0, p.w, p.h, 0, G) + heavy_frame(x0, y0, s, W)
    hole = s * (180 - 76) / 180
    k = hole * 0.36
    out += rect(x0 + s * 38 / 180 + hole - k - hole * 0.12, y0 + s * 38 / 180 + hole - k - hole * 0.12, k, k, k * 0.24, B)
    return out + desc(p, ["СНАЧАЛА ПРОЦЕСС.", "ПОТОМ ТЕХНОЛОГИЯ."], W)


@poster("ten-to-one", "Постер: 10 ч → 1 ч")
def _(p):
    out = rect(0, 0, p.w, p.h, 0, G)
    big = p.w * 0.33
    y = p.top
    out += text(p.m - big * 0.04, y + cap(big), "10 ч", big, 800, W, ls=-0.04, opacity=0.2)
    out += text(p.m - big * 0.04, y + cap(big) + big * 0.95, "1 ч", big, 800, B, ls=-0.04)
    out += text(p.m, y + cap(big) + big * 0.95 + p.hs * 0.75, "в неделю на заявки.", p.hs * 0.42, 800, W, ls=-0.01)
    out += text(p.m, y + cap(big) + big * 0.95 + p.hs * 0.75 + p.hs * 0.5, "Остальное делает система.", p.hs * 0.42, 800, C["graphite_muted"], ls=-0.01)
    return out + desc(p, ["АВТОМАТИЗИРУЮ", "БИЗНЕС-ПРОЦЕССЫ"], W)


@poster("no-chaos", "Постер: не автоматизируем хаос")
def _(p):
    out = rect(0, 0, p.w, p.h, 0, W)
    b, _ = block(p, p.top, ["Не авто-", "матизируем", [("хаос.", "chip")]], G, None, 1.0)
    return out + b + desc(p, ["СНАЧАЛА ПРОЦЕСС.", "ПОТОМ ТЕХНОЛОГИЯ."], G)


@poster("toggle", "Постер: тумблер")
def _(p):
    out = rect(0, 0, p.w, p.h, 0, W)
    b, y = block(p, p.top, ["Выключаем", "ручной режим"], G)
    tw = p.w - 2 * p.m
    th = tw * 0.5
    ty = y + p.hs * 0.3
    if ty + th > p.desc_y - p.ds * 2:
        th = p.desc_y - p.ds * 2 - ty
        tw = th * 2
    r, k = th * 0.3, th * 0.72
    pad = (th - k) / 2
    out += b + rect(p.m, ty, tw, th, r, B) + rect(p.m + tw - pad - k, ty + pad, k, k, k * 0.24, W)
    return out + desc(p, ["АВТОМАТИЗАЦИЯ", "БИЗНЕС-ПРОЦЕССОВ"], G)


def build():
    for name, (d, fn) in POSTERS.items():
        for w, h, tag in SIZES:
            save(f"08_SOCIAL_TEMPLATES/SVG/posters/poster-{name}-{tag}.svg", w, h, fn(P(w, h)), d,
                 pngs=[(f"08_SOCIAL_TEMPLATES/PNG/posters/poster-{name}-{tag}.png", w)])
    return len(POSTERS)
