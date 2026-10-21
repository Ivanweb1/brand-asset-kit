"""02_GRAPHIC_ELEMENTS — модули и связки в сетке знака (модуль 180, обводка 38, точка 50, шаг 65, зазор 30)."""
from kit import C, rect, line, path, heavy_frame, dot, save

G, W, B = C["graphite"], C["offwhite"], C["blue"]
LW = 8      # тонкая линия системы
P = LW / 2  # поле под обводку, чтобы ничего не обрезалось


def _frame_line(x, y, w, h, r, m, sw=LW, dash=None):
    da = f' stroke-dasharray="{dash}" stroke-linecap="round"' if dash else ""
    return f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{r:g}" fill="none" stroke="{m}" stroke-width="{sw:g}"{da}/>'


def cluster(x, y, m, a, s=50, pitch=65):
    pos = [(0, 0), (2, 0), (1, 1), (0, 2), (2, 2)]
    return "".join(dot(x + i * pitch, y + j * pitch, s, a if (i, j) == (0, 0) else m) for i, j in pos)


def chevron(x, y, size, m, sw, direction=0):
    # острие в (x, y), направление в градусах
    return path(f"M{x - size:g} {y - size:g}L{x:g} {y:g}L{x - size:g} {y + size:g}", m, sw,
                extra=f' transform="rotate({direction} {x:g} {y:g})"')


def elbow(x1, y1, x2, y2, r):
    return f"M{x1:g} {y1:g}H{x2 - r:g}A{r:g} {r:g} 0 0 1 {x2:g} {y1 + r:g}V{y2:g}"


E = {}


def el(name, desc):
    def deco(fn):
        E[name] = (desc, fn)
        return fn
    return deco


@el("module-outline", "Контурный модуль в пропорциях знака")
def _(m, a):
    return 180, 180, heavy_frame(0, 0, 180, m)


@el("module-outline-line", "Контурный модуль, тонкая линия")
def _(m, a):
    return 180 + LW, 180 + LW, _frame_line(P, P, 180, 180, 42, m)


@el("module-solid", "Заполненный модуль")
def _(m, a):
    return 180, 180, rect(0, 0, 180, 180, 42, m)


@el("module-solid-accent", "Акцентный синий модуль")
def _(m, a):
    return 180, 180, rect(0, 0, 180, 180, 42, a)


@el("dot", "Малый модуль")
def _(m, a):
    return 50, 50, dot(0, 0, 50, m)


@el("dot-accent", "Малый акцентный модуль")
def _(m, a):
    return 50, 50, dot(0, 0, 50, a)


@el("dot-cluster", "Пять малых модулей — сектор знака")
def _(m, a):
    return 180, 180, cluster(0, 0, m, a)


@el("module-row", "Ряд модулей: контур, контур, акцент")
def _(m, a):
    return 600, 180, heavy_frame(0, 0, 180, m) + heavy_frame(210, 0, 180, m) + rect(420, 0, 180, 180, 42, a)


@el("module-pair-cluster", "Модуль + сектор точек")
def _(m, a):
    return 390, 180, heavy_frame(0, 0, 180, m) + cluster(210, 0, m, a)


@el("module-cascade", "Каскад тонких модулей")
def _(m, a):
    body = _frame_line(P, P, 180, 180, 42, m) + _frame_line(P + 60, P + 60, 180, 180, 42, m)
    body += rect(P + 120, P + 120, 180, 180, 42, a)
    return 300 + LW, 300 + LW, body


@el("grid-modules-3x3", "Сетка 3×3, центральный модуль активен")
def _(m, a):
    out = ""
    for i in range(3):
        for j in range(3):
            x, y = P + i * 150, P + j * 150
            out += rect(x, y, 120, 120, 28, a) if (i, j) == (1, 1) else _frame_line(x, y, 120, 120, 28, m)
    return 420 + LW, 420 + LW, out


@el("grid-dots", "Точечная матрица 7×4")
def _(m, a):
    out = "".join(dot(i * 65, j * 65, 22, a if (i, j) == (5, 1) else m) for i in range(7) for j in range(4))
    return 6 * 65 + 22, 3 * 65 + 22, out


@el("grid-technical", "Тонкая техническая сетка")
def _(m, a):
    sw = 3
    w, h, c = 600, 360, 120
    out = _frame_line(sw / 2, sw / 2, w, h, 32, m, sw)
    out += "".join(line(sw / 2 + x, sw / 2, sw / 2 + x, sw / 2 + h, m, sw, "butt") for x in range(c, w, c))
    out += "".join(line(sw / 2, sw / 2 + y, sw / 2 + w, sw / 2 + y, m, sw, "butt") for y in range(c, h, c))
    out += rect(sw / 2 + 2 * c + 35, sw / 2 + c + 35, 50, 50, 12, a)
    return w + sw, h + sw, out


@el("connector-straight", "Связь двух модулей")
def _(m, a):
    return 600, 50, dot(0, 0, 50, m) + line(50, 25, 550, 25, m, LW, "butt") + dot(550, 0, 50, a)


@el("connector-elbow", "Угловая связь со скруглением")
def _(m, a):
    return 400, 300, dot(0, 0, 50, m) + path(elbow(50, 25, 375, 250, 48), m, LW) + dot(350, 250, 50, a)


@el("connector-dashed", "Пунктирная связь")
def _(m, a):
    return 600, 50, dot(0, 0, 50, m) + line(76, 25, 524, 25, m, LW, "round", "0 22") + dot(550, 0, 50, a)


@el("connector-branch", "Разветвление 1 → 2")
def _(m, a):
    body = dot(0, 125, 50, m) + line(50, 150, 160, 150, m, LW, "butt")
    body += path("M160 150V73A48 48 0 0 1 208 25H350", m, LW) + path("M160 150V227A48 48 0 0 0 208 275H350", m, LW)
    body += dot(350, 0, 50, a) + dot(350, 250, 50, m)
    return 400, 300, body


@el("line-dashed", "Пунктирная линия")
def _(m, a):
    return 600, LW, line(P + 9, P, 600 - P - 9, P, m, LW, "round", "18 22")


@el("line-dotted", "Точечная линия")
def _(m, a):
    return 600, LW, line(P, P, 600 - P, P, m, LW, "round", "0 22")


@el("divider-accent", "Разделитель с акцентом")
def _(m, a):
    return 600, 24, rect(0, 0, 24, 24, 6, a) + line(48, 12, 600, 12, m, 3, "butt")


@el("divider-modules", "Разделитель из модулей")
def _(m, a):
    return 6 * 44 + 24, 24, "".join(rect(i * 44, 0, 24, 24, 6, a if i == 0 else m) for i in range(7))


@el("corner-brackets", "Рамка из угловых скобок")
def _(m, a):
    w, h, arm, r = 600, 400, 90, 42
    d = (f"M{P} {P + arm}V{P + r}A{r} {r} 0 0 1 {P + r} {P}H{P + arm}"
         f"M{P + w - arm} {P}H{P + w - r}A{r} {r} 0 0 1 {P + w} {P + r}V{P + arm}"
         f"M{P + w} {P + h - arm}V{P + h - r}A{r} {r} 0 0 1 {P + w - r} {P + h}H{P + w - arm}"
         f"M{P + arm} {P + h}H{P + r}A{r} {r} 0 0 1 {P} {P + h - r}V{P + h - arm}")
    return w + LW, h + LW, path(d, m, LW)


@el("corner-single", "Угловой элемент")
def _(m, a):
    arm, r = 140, 42
    return arm + P, arm + P, path(f"M{P} {arm}V{P + r}A{r} {r} 0 0 1 {P + r} {P}H{arm}", m, LW) + dot(P + 40, P + 40, 36, a)


@el("marker-active", "Индикатор активного состояния")
def _(m, a):
    return 120 + LW, 120 + LW, _frame_line(P, P, 120, 120, 30, m) + dot(P + 35, P + 35, 50, a)


@el("marker-pin", "Маркер-выноска")
def _(m, a):
    return 50, 260, dot(0, 0, 50, a) + line(25, 50, 25, 256, m, LW, "round", "0 20")


@el("marker-numbered-dot", "Маркер шага: модуль + линия")
def _(m, a):
    return 360, 50, dot(0, 0, 50, a) + line(80, 25, 360 - P, 25, m, LW)


@el("toggle-on", "Переключатель «включено»")
def _(m, a):
    return 220, 120, rect(0, 0, 220, 120, 36, a) + rect(118, 18, 84, 84, 22, W)


@el("toggle-off", "Переключатель «ручной режим»")
def _(m, a):
    return 220 + LW, 120 + LW, _frame_line(P, P, 220, 120, 36, m) + rect(P + 18, P + 18, 84, 84, 22, m)


@el("arrow-right", "Стрелка перехода")
def _(m, a):
    sw = 12
    return 200 + sw, 120 + sw, line(sw / 2, 66, 200, 66, m, sw) + chevron(200, 66, 60, m, sw)


@el("arrow-diagonal", "Диагональная стрелка ↗")
def _(m, a):
    sw = 12
    return 160 + sw, 160 + sw, path(f"M{sw / 2} {160 + sw / 2}L{160 + sw / 2} {sw / 2}M{40 + sw / 2} {sw / 2}H{160 + sw / 2}V{120 + sw / 2}", m, sw)


@el("arrow-module", "Стрелка с модулем-источником")
def _(m, a):
    sw = 8
    return 520, 100, dot(0, 25, 50, a) + line(80, 50, 510, 50, m, sw) + chevron(510, 50, 40, m, sw)


@el("frame-line", "Рамка 16:9, тонкая линия")
def _(m, a):
    return 640 + LW, 360 + LW, _frame_line(P, P, 640, 360, 44, m)


@el("frame-dashed", "Пунктирная рамка (зона, слот)")
def _(m, a):
    return 300 + LW, 300 + LW, _frame_line(P, P, 300, 300, 56, a, LW, "18 18")


def build():
    n = 0
    for name, (desc, fn) in E.items():
        variants = {tone: fn(m, B) for tone, m in (("on-light", G), ("on-dark", W))}
        same = variants["on-light"][2] == variants["on-dark"][2]  # только синий — один файл на любой фон
        for tone, (w, h, body) in variants.items():
            if same and tone == "on-dark":
                continue
            tone = "any-bg" if same else tone
            pw = round(1024 * w / max(w, h))
            save(f"02_GRAPHIC_ELEMENTS/SVG/el-{name}-{tone}.svg", w, h, body, desc,
                 pngs=[(f"02_GRAPHIC_ELEMENTS/PNG/el-{name}-{tone}.png", max(pw, 1))])
        n += 1
    return n
