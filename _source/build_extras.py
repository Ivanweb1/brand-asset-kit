"""09_EXTRA_ELEMENTS — курсоры, маркеры внимания, лоадеры, UI-элементы, схемы процессов, фавиконы."""
from kit import C, rect, text, cap, line, path, logo, dot, measure, save, KIT
from build_labels import Tone, icon_tile
from build_icons import draw as icon

G, W, B = C["graphite"], C["offwhite"], C["blue"]
X = {}


def ex(name, desc):
    def deco(fn):
        X[name] = (desc, fn)
        return fn
    return deco


CURSOR = "M6 4L6 66L22 51L33 76L46 70L35 46L56 46Z"


@ex("cursor-arrow", "Фирменный курсор")
def _(t):
    return 64, 84, path(CURSOR, t.bg, 5, t.fg)


@ex("cursor-arrow-blue", "Курсор-акцент")
def _(t):
    return 64, 84, path(CURSOR, W, 5, B)


@ex("cursor-click", "Курсор с кликом")
def _(t):
    rays = "".join(line(30 + dx, 30 + dy, 30 + ex_, 30 + ey, B, 6) for dx, dy, ex_, ey in ((-6, -12, -6, -26), (-14, -4, -28, -4), (-12, -12, -22, -22)))
    return 110, 120, rays + f'<g transform="translate(34 32)">{path(CURSOR, t.bg, 5, t.fg)}</g>'


@ex("cursor-module", "Модульный курсор-фокус")
def _(t):
    return 96, 96, rect(3, 3, 90, 90, 24, "none", t.fg, 5) + dot(28, 28, 40, B)


@ex("attention-brackets", "Маркер внимания: фокус-скобки")
def _(t):
    s, a, r, p = 220, 56, 28, 4
    d = (f"M{p} {p + a}V{p + r}A{r} {r} 0 0 1 {p + r} {p}H{p + a}M{s - a} {p}H{s - r}A{r} {r} 0 0 1 {s} {p + r}V{p + a}"
         f"M{s} {s - a}V{s - r}A{r} {r} 0 0 1 {s - r} {s}H{s - a}M{p + a} {s}H{p + r}A{r} {r} 0 0 1 {p} {s - r}V{s - a}")
    return s + p, s + p, path(d, B, 8)


@ex("attention-dot", "Маркер внимания: пульс-модуль")
def _(t):
    return 120, 120, rect(4, 4, 112, 112, 30, "none", B, 4, ' stroke-opacity="0.35"') + rect(22, 22, 76, 76, 20, "none", B, 4, ' stroke-opacity="0.7"') + dot(40, 40, 40, B)


@ex("highlight-underline", "Подчёркивание-акцент")
def _(t):
    return 600, 22, rect(0, 0, 600, 22, 8, B)


@ex("highlight-box", "Обводка-выделение")
def _(t):
    return 608, 208, rect(4, 4, 600, 200, 32, "none", B, 8)


@ex("progress-modules", "Прогресс из модулей (3 из 5)")
def _(t):
    return 5 * 56 - 16, 40, "".join(rect(i * 56, 0, 40, 40, 10, B if i < 3 else t.ln) for i in range(5))


@ex("progress-bar", "Полоса прогресса")
def _(t):
    return 600, 32, rect(0, 0, 600, 32, 10, t.ln) + rect(0, 0, 390, 32, 10, B) + rect(398, 0, 32, 32, 10, t.fg)


@ex("status-done", "Статус: готово")
def _(t):
    return _status(t, "Готово", B, True)


@ex("status-in-progress", "Статус: в работе")
def _(t):
    return _status(t, "В работе", t.fg, False)


@ex("status-error", "Статус: требует внимания")
def _(t):
    return _status(t, "Требует внимания", t.mut, False, True)


def _status(t, s, col, filled, warn=False):
    w = 24 + 28 + 18 + measure(s, 30, 700) + 26
    body = rect(0, 0, w, 64, 20, t.bg)
    body += rect(24, 18, 28, 28, 8, col) if filled else rect(26, 20, 24, 24, 7, "none", col, 4)
    if warn:
        body += line(38, 26, 38, 34, col, 4) + dot(36, 37, 4, col)
    return w, 64, body + text(70, 32 + cap(30) / 2, s, 30, 700, t.fg)


@ex("automation-symbol", "Символ автоматизации: ручной → система")
def _(t):
    body = rect(4, 4, 160, 88, 26, "none", t.mut, 5) + rect(18, 18, 60, 60, 16, t.mut)
    body += line(196, 48, 286, 48, t.fg, 6) + path("M268 30L287 48L268 66", t.fg, 6)
    body += rect(320, 4, 160, 88, 26, B) + rect(404, 16, 64, 64, 18, W)
    return 484, 96, body


@ex("schema-linear", "Схема процесса: 3 шага")
def _(t):
    out = ""
    for i, (ic, s) in enumerate((("leads", "Заявка"), ("crm", "CRM"), ("reports", "Отчёт"))):
        x = i * 300
        last = i == 2
        out += rect(x, 0, 140, 140, 34, B if last else t.surf) + f'<g transform="translate({x + 34} 34) scale({72 / 48:.4f})">{icon(ic, W if last else t.fg, W if last else B)}</g>'
        out += text(x + 70, 196, s, 34, 700, t.fg, anchor="middle")
        if i < 2:
            out += line(x + 160, 70, x + 270, 70, t.fg, 5, "round", "0 14") + path(f"M{x + 262} 58L{x + 276} 70L{x + 262} 82", t.fg, 5)
    return 740, 210, out


@ex("schema-branch", "Схема: разветвление по условию")
def _(t):
    out = rect(0, 130, 140, 140, 34, t.surf) + f'<g transform="translate(34 164) scale(1.5)">{icon("leads", t.fg, B)}</g>'
    out += path("M140 200H210V112A44 44 0 0 1 254 68H330", t.fg, 5) + path("M210 200V288A44 44 0 0 0 254 332H330", t.fg, 5)
    out += rect(340, 0, 140, 140, 34, B) + f'<g transform="translate(374 34) scale(1.5)">{icon("chatbot", W, W)}</g>'
    out += rect(340, 262, 140, 140, 34, t.surf) + f'<g transform="translate(374 296) scale(1.5)">{icon("crm", t.fg, B)}</g>'
    out += text(504, 84, "Бот", 34, 700, t.fg) + text(504, 346, "Менеджер", 34, 700, t.fg)
    return 504 + measure("Менеджер", 34, 700) + 4, 402, out


@ex("schema-hub", "Схема соединения модулей: хаб")
def _(t):
    cx = cy = 300
    out = ""
    nodes = (("website", 300, 60), ("crm", 540, 300), ("messages", 300, 540), ("analytics", 60, 300))
    for ic, x, y in nodes:
        out += line(cx, cy, x, y, t.ln, 5, "butt")
    out += rect(cx - 90, cy - 90, 180, 180, 42, B) + logo(cx - 50, cy - 50, 100, W, W)
    for ic, x, y in nodes:
        out += rect(x - 60, y - 60, 120, 120, 30, t.surf) + f'<g transform="translate({x - 30} {y - 30}) scale(1.25)">{icon(ic, t.fg, B)}</g>'
    return 600, 600, out


@ex("ui-window", "UI: окно приложения")
def _(t):
    body = rect(2, 2, 716, 456, 32, t.bg, t.ln, 4) + line(2, 74, 718, 74, t.ln, 4, "butt")
    body += "".join(rect(32 + i * 30, 30, 16, 16, 5, B if i == 0 else t.ln) for i in range(3))
    body += rect(32, 108, 200, 316, 20, t.surf) + rect(260, 108, 428, 140, 20, t.surf) + rect(260, 272, 204, 152, 20, B) + rect(484, 272, 204, 152, 20, t.surf)
    return 720, 460, body


@ex("ui-button", "UI: кнопка")
def _(t):
    s = "Запустить"
    w = 44 + measure(s, 34, 700) + 24 + 30 + 40
    body = rect(0, 0, w, 88, 24, B) + text(44, 44 + cap(34) / 2, s, 34, 700, W)
    x = w - 40 - 30
    return w, 88, body + line(x, 44, x + 28, 44, W, 5) + path(f"M{x + 16} 32L{x + 29} 44L{x + 16} 56", W, 5)


@ex("ui-input", "UI: поле ввода с курсором")
def _(t):
    body = rect(2, 2, 636, 96, 26, t.bg, t.ln, 4) + text(36, 50 + cap(32) / 2, "Как автоматизировать", 32, 500, t.fg)
    x = 36 + measure("Как автоматизировать", 32, 500) + 6
    return 640, 100, body + rect(x, 30, 4, 40, 2, B)


@ex("ui-toast", "UI: уведомление «Новая заявка»")
def _(t):
    body = rect(0, 0, 680, 140, 32, t.bg, t.ln, 0) + icon_tile(24, 24, 92, "leads", t)
    body += text(140, 60, "Новая заявка", 36, 800, t.fg) + text(140, 104, "Карточка создана в CRM · сейчас", 28, 500, t.mut)
    return 680, 140, body + dot(628, 28, 24, B)


@ex("ui-checkbox-on", "UI: чекбокс отмечен")
def _(t):
    return 64, 64, rect(0, 0, 64, 64, 16, B) + path("M18 33L28 43L47 22", W, 6)


@ex("ui-checkbox-off", "UI: чекбокс пуст")
def _(t):
    return 64, 64, rect(2.5, 2.5, 59, 59, 15, "none", t.fg, 5)


def loader_frame(k, t):
    """Кадр лоадера: модули 3×3 загораются по кругу."""
    order = [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2), (0, 1)]
    out = ""
    for idx, (i, j) in enumerate(order):
        d = (k - idx) % 8
        col, op = (B, 1) if d == 0 else (t.fg, [1, .55, .3, .15, .15, .15, .15, .15][d])
        out += f'<rect x="{i * 44}" y="{j * 44}" width="32" height="32" rx="8" fill="{col}" opacity="{op}"/>'
    return out + f'<rect x="44" y="44" width="32" height="32" rx="8" fill="{t.fg}" opacity="0.15"/>'


def loader_animated(t):
    order = [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (1, 2), (0, 2), (0, 1)]
    out = f'<rect x="44" y="44" width="32" height="32" rx="8" fill="{t.fg}" opacity="0.15"/>'
    for idx, (i, j) in enumerate(order):
        out += (f'<rect x="{i * 44}" y="{j * 44}" width="32" height="32" rx="8" fill="{t.fg}" opacity="0.15">'
                f'<animate attributeName="fill" values="{B};{t.fg};{t.fg}" keyTimes="0;0.125;1" dur="1.2s" begin="{idx * 0.15:.2f}s" repeatCount="indefinite"/>'
                f'<animate attributeName="opacity" values="1;0.55;0.15;0.15" keyTimes="0;0.125;0.4;1" dur="1.2s" begin="{idx * 0.15:.2f}s" repeatCount="indefinite"/></rect>')
    return out


def build():
    import math
    for name, (desc, fn) in X.items():
        variants = {tn: fn(Tone(tn)) for tn in ("dark", "light")}
        same = variants["dark"][2] == variants["light"][2]   # элемент только из синего — один файл на оба фона
        for tn, (w, h, body) in variants.items():
            if same and tn == "light":
                continue
            suffix = "" if same else ("-on-dark" if tn == "dark" else "-on-light")
            pw = round(1024 * w / max(w, h)) if max(w, h) < 1024 else math.ceil(w)
            save(f"09_EXTRA_ELEMENTS/SVG/x-{name}{suffix}.svg", math.ceil(w), math.ceil(h), body, desc,
                 pngs=[(f"09_EXTRA_ELEMENTS/PNG/x-{name}{suffix}.png", pw)])
    for tn, tone in (("dark", "on-dark"), ("light", "on-light")):
        t = Tone(tn)
        save(f"09_EXTRA_ELEMENTS/SVG/x-loader-modules-animated-{tone}.svg", 120, 120, loader_animated(t), "Лоадер (анимированный SVG)")
        for k in range(8):
            save(f"_source/_cache/loader-{tone}-{k:02d}.svg", 120, 120, loader_frame(k, t), "Кадр лоадера",
                 pngs=[(f"09_EXTRA_ELEMENTS/PNG/loader-sequence-{tone}/loader-{k:02d}.png", 480)], section="_frames")
    # фавиконы
    save("09_EXTRA_ELEMENTS/SVG/favicon.svg", 1000, 1000, rect(0, 0, 1000, 1000, 233, G) + logo(220, 220, 560, W, B), "Фавикон",
         pngs=[(f"09_EXTRA_ELEMENTS/PNG/favicon/favicon-{s}.png", s) for s in (16, 32, 48, 180, 192, 512)])
    return len(X) + 2


def post_render():
    """После рендера: favicon.ico и GIF лоадера."""
    from PIL import Image
    fav = KIT / "09_EXTRA_ELEMENTS/PNG/favicon"
    imgs = [Image.open(fav / f"favicon-{s}.png") for s in (16, 32, 48)]
    imgs[2].save(fav / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)], append_images=imgs[:2])
    for tone, bgc in (("on-dark", G), ("on-light", W)):
        frames = []
        for k in range(8):
            im = Image.open(KIT / f"09_EXTRA_ELEMENTS/PNG/loader-sequence-{tone}/loader-{k:02d}.png").convert("RGBA")
            base = Image.new("RGBA", im.size, bgc)
            base.alpha_composite(im)
            frames.append(base.convert("P", palette=Image.ADAPTIVE))
        frames[0].save(KIT / f"09_EXTRA_ELEMENTS/PNG/x-loader-modules-{tone}.gif", save_all=True, append_images=frames[1:], duration=150, loop=0)
