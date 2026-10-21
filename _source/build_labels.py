"""04_LABELS — плашки в масштабе кадра 1080 px. Каждая: тёмная/светлая (+синяя где уместно) и пустая версия."""
import math
from kit import C, T, rect, text, measure, cap, save, logo, line
from build_icons import draw as icon

R = T["radius"]
PX, PY = T["space"]["plate_pad_x"], T["space"]["plate_pad_y"]


class Tone:
    def __init__(self, name):
        self.name = name
        if name == "dark":
            self.bg, self.fg, self.mut, self.ln, self.acc, self.surf = C["graphite"], C["offwhite"], C["graphite_muted"], C["graphite_line"], C["blue"], C["graphite_surface"]
        elif name == "light":
            self.bg, self.fg, self.mut, self.ln, self.acc, self.surf = C["offwhite"], C["graphite"], C["offwhite_muted"], C["offwhite_line"], C["blue"], C["offwhite_surface"]
        else:  # blue: акцент становится светлым
            self.bg, self.fg, self.mut, self.ln, self.acc, self.surf = C["blue"], C["offwhite"], C["offwhite"], C["offwhite"], C["offwhite"], C["graphite"]


def kicker(x, y, s, t, tone, empty):
    """Надзаголовок: синий модуль + капс с трекингом."""
    out = rect(x, y - cap(26) + 1, 18, 18, 5, tone.acc)
    if not empty:
        out += text(x + 32, y, s, 26, 700, tone.mut if tone.name != "blue" else tone.fg, ls=0.16)
    return out


def tw(rows, size, weight, ls=0.0):
    return max(measure(r if isinstance(r, str) else "".join(t for t, _ in r), size, weight, ls) for r in rows)


def stack(x, y, rows, size, weight, fill, lh, empty):
    """Строки, y — верх блока. Возвращает (svg, высота блока)."""
    h = cap(size) + (len(rows) - 1) * size * lh
    if empty:
        return "", h
    out = "".join(text(x, y + cap(size) + i * size * lh, r, size, weight, fill) for i, r in enumerate(rows))
    return out, h


def icon_tile(x, y, s, name, tone):
    return rect(x, y, s, s, s * 0.25, tone.surf) + f'<g transform="translate({x + s * 0.2:g} {y + s * 0.2:g}) scale({s * 0.6 / 48:.4f})">{icon(name, tone.fg, tone.acc)}</g>'


L = {}


def label(name, desc, tones=("dark", "light")):
    def deco(fn):
        L[name] = (desc, fn, tones)
        return fn
    return deco


def text_plate(tone, empty, k, rows, size, weight, lh=1.15, minw=0, maxw=940, bar=False, sub=None):
    """Универсальная плашка: [надзаголовок] + строки + [подпись]."""
    x0 = PX + (28 if bar else 0)
    w = x0 + max(tw(rows, size, weight), measure(k or "", 26, 700, 0.16) + 32, tw(sub[0], sub[1], 500) if sub else 0) + PX
    w = min(max(w, minw), maxw)
    y = PY
    body = ""
    if k:
        body += kicker(x0, y + cap(26), k, k, tone, empty)
        y += cap(26) + 28
    s, h = stack(x0, y, rows, size, weight, tone.fg, lh, empty)
    body += s
    y += h
    if sub:
        y += 22
        s, h = stack(x0, y, sub[0], sub[1], 500, tone.mut, 1.3, empty)
        body += s
        y += h
    hgt = y + PY + 6
    plate = rect(0, 0, w, hgt, R["lg"], tone.bg)
    if bar:
        plate += rect(PX, PY, 8, hgt - 2 * PY, 4, tone.acc)
    return w, hgt, plate + body


@label("title", "Заголовок")
def _(tone, empty):
    return text_plate(tone, empty, None, ["Сначала процесс,", "потом технология"], 68, 800, 1.12)


@label("subtitle", "Подзаголовок")
def _(tone, empty):
    return text_plate(tone, empty, None, ["Как убрать ручной ввод заявок"], 40, 700)


@label("key-thought", "Важная мысль")
def _(tone, empty):
    return text_plate(tone, empty, "ВАЖНО", ["Сначала наводим порядок,", "потом автоматизируем", "процесс"], 44, 700, 1.22, bar=True)


@label("key-number", "Ключевая цифра", ("dark", "light", "blue"))
def _(tone, empty):
    w, size = 620, 170
    body = ""
    y = PY + 10 + cap(size)
    if not empty:
        body += text(PX - 6, y, [("20", tone.fg), (" ч", tone.acc)], size, 800, ls=-0.03)
    y2 = y + 40
    s, h = stack(PX, y2, ["экономии времени", "каждую неделю"], 36, 500, tone.mut, 1.3, empty)
    hgt = y2 + h + PY + 6
    return w, hgt, rect(0, 0, w, hgt, R["lg"], tone.bg) + body + s


@label("percent", "Процент", ("dark", "light", "blue"))
def _(tone, empty):
    w, size = 620, 170
    y = PY + 10 + cap(size)
    body = "" if empty else text(PX - 6, y, [("−80", tone.fg), ("%", tone.acc)], size, 800, ls=-0.03)
    y2 = y + 40
    s, h = stack(PX, y2, ["времени на обработку", "заявок"], 36, 500, tone.mut, 1.3, empty)
    hgt = y2 + h + PY + 6
    return w, hgt, rect(0, 0, w, hgt, R["lg"], tone.bg) + body + s


def icon_plate(tone, empty, ic, k, rows, size=40, weight=700, w=None):
    ts = 104
    x0 = PX + ts + 32
    w = w or x0 + max(tw(rows, size, weight), measure(k, 26, 700, 0.16) + 32) + PX
    y = PY
    body = kicker(x0, y + cap(26), k, k, tone, empty)
    y += cap(26) + 26
    s, h = stack(x0, y, rows, size, weight, tone.fg, 1.18, empty)
    hgt = max(y + h + PY + 6, ts + 2 * PY)
    return w, hgt, rect(0, 0, w, hgt, R["lg"], tone.bg) + icon_tile(PX, (hgt - ts) / 2, ts, ic, tone) + body + s


@label("error", "Ошибка")
def _(tone, empty):
    return icon_plate(tone, empty, "errors", "ОШИБКА", ["Автоматизировать хаос"])


@label("problem", "Проблема")
def _(tone, empty):
    return icon_plate(tone, empty, "manual", "ПРОБЛЕМА", ["Ручные процессы", "отнимают время"])


@label("solution", "Решение", ("dark", "light", "blue"))
def _(tone, empty):
    return icon_plate(tone, empty, "result", "РЕШЕНИЕ", ["Автоматизируем", "и выстраиваем систему"])


@label("tip", "Совет")
def _(tone, empty):
    return icon_plate(tone, empty, "control", "СОВЕТ", ["Начните с одного процесса,", "который повторяется каждый день"], 36, 600)


@label("conclusion", "Вывод")
def _(tone, empty):
    return text_plate(tone, empty, "ВЫВОД", ["Система работает,", "даже когда вас нет"], 48, 800, 1.15)


@label("before-after", "До / После")
def _(tone, empty):
    w, h, gap = 900, 300, 16
    cw = (w - gap) / 2
    left = rect(0, 0, cw, h, R["lg"], tone.bg)
    right = rect(cw + gap, 0, cw, h, R["lg"], C["blue"])
    # переключатели: ручной (выкл) и автоматический (вкл)
    tl = rect(PX, PY, 92, 52, 16, "none", tone.mut, 4) + rect(PX + 10, PY + 10, 32, 32, 9, tone.mut)
    tr = rect(cw + gap + PX, PY, 92, 52, 16, C["offwhite"]) + rect(cw + gap + PX + 50, PY + 10, 32, 32, 9, C["blue"])
    body = left + right + tl + tr
    if not empty:
        ty = PY + 52 + 40 + cap(26)
        body += text(PX, ty, "ДО", 26, 700, tone.mut, ls=0.16)
        body += text(PX, ty + 74, "10 часов", 60, 800, tone.fg, ls=-0.02)
        body += text(PX, ty + 120, "в неделю вручную", 30, 500, tone.mut)
        x2 = cw + gap + PX
        body += text(x2, ty, "ПОСЛЕ", 26, 700, C["offwhite"], ls=0.16, opacity=0.8)
        body += text(x2, ty + 74, "1 час", 60, 800, C["offwhite"], ls=-0.02)
        body += text(x2, ty + 120, "на контроль системы", 30, 500, C["offwhite"], opacity=0.8)
    return w, h, body


for _n, (_num, _t) in enumerate((("01", ["Разбираем процесс"]), ("02", ["Проектируем систему"]), ("03", ["Автоматизируем"])), 1):
    def _mk(num=_num, rows=_t):
        def fn(tone, empty):
            ts = 104
            x0 = PX + ts + 32
            w = x0 + max(tw(rows, 44, 800), 300) + PX
            hgt = ts + 2 * 28
            y = 28
            body = rect(0, 0, w, hgt, R["lg"], tone.bg) + rect(28, y, ts, ts, 26, C["blue"])
            if not empty:
                body += text(28 + ts / 2, y + ts / 2 + cap(46) / 2, num, 46, 800, C["offwhite"], anchor="middle")
                body += text(x0, y + 34, f"ШАГ {num}", 24, 700, tone.mut, ls=0.16)
                body += text(x0, y + 34 + 26 + cap(44), rows[0], 44, 800, tone.fg)
            return w, hgt, body
        return fn
    L[f"step-{_num}"] = (f"Шаг {_num}", _mk(), ("dark", "light"))


def badge(tone, empty, kind, t):
    h = 88
    pad = 22
    if kind == "ai":
        lead = 52
        g = f'<g transform="translate({pad} {(h - lead) / 2}) scale({lead / 48:.4f})">{icon("ai", tone.fg, tone.acc)}</g>'
    elif kind == "on":
        lead = 84
        tg = C["offwhite"] if tone.name == "blue" else C["blue"]
        kn = C["blue"] if tone.name == "blue" else C["offwhite"]
        g = rect(pad, (h - 46) / 2, lead, 46, 14, tg) + rect(pad + lead - 40, (h - 46) / 2 + 6, 34, 34, 9, kn)
    else:
        lead = 84
        g = rect(pad + 2, (h - 46) / 2 + 2, lead - 4, 42, 13, "none", tone.mut, 4) + rect(pad + 8, (h - 46) / 2 + 8, 30, 30, 8, tone.mut)
    x0 = pad + lead + 20
    w = x0 + measure(t, 36, 700) + 30
    body = rect(0, 0, w, h, R["md"], tone.bg) + g
    if not empty:
        body += text(x0, h / 2 + cap(36) / 2, t, 36, 700, tone.fg)
    return w, h, body


@label("ai", "AI", ("dark", "light", "blue"))
def _(tone, empty):
    return badge(tone, empty, "ai", "AI-инструмент")


@label("automated", "Автоматизировано", ("dark", "light", "blue"))
def _(tone, empty):
    return badge(tone, empty, "on", "Автоматизировано")


@label("manual-process", "Ручной процесс")
def _(tone, empty):
    return badge(tone, empty, "off", "Ручной процесс")


@label("time-saved", "Экономия времени", ("dark", "light", "blue"))
def _(tone, empty):
    return icon_plate(tone, empty, "time", "ЭКОНОМИЯ ВРЕМЕНИ", ["До 20 часов", "в неделю"], 44, 800)


@label("cta", "Призыв к действию", ("blue", "dark", "light"))
def _(tone, empty):
    t = ["Разберём ваш процесс", "на бесплатной консультации"]
    w = PX + max(measure(t[0], 44, 800), measure(t[1], 32, 500)) + 48 + 104 + PX
    hgt = 2 * PY + 104 + 8
    tile_bg = C["offwhite"] if tone.name == "blue" else C["blue"]
    arr = C["blue"] if tone.name == "blue" else C["offwhite"]
    ax, ay = w - PX - 104, (hgt - 104) / 2
    body = rect(0, 0, w, hgt, R["lg"], tone.bg) + rect(ax, ay, 104, 104, 26, tile_bg)
    body += line(ax + 36, ay + 52, ax + 68, ay + 52, arr, 4.5) + f'<path d="M{ax + 58} {ay + 42}L{ax + 68} {ay + 52}L{ax + 58} {ay + 62}" fill="none" stroke="{arr}" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round"/>'
    if not empty:
        body += text(PX, hgt / 2 - 6, t[0], 44, 800, tone.fg)
        body += text(PX, hgt / 2 + 42, t[1], 32, 500, tone.fg if tone.name == "blue" else tone.mut, opacity=0.85 if tone.name == "blue" else None)
    return w, hgt, body


@label("speaker", "Подпись спикера")
def _(tone, empty):
    ms = 96
    x0 = PX + ms + 32
    w = max(760, x0 + measure("Автоматизация бизнес-процессов", 30, 500) + PX)
    hgt = ms + 2 * 34
    mark = logo(PX, 34, ms, tone.fg, C["blue"])
    body = rect(0, 0, w, hgt, R["lg"], tone.bg) + mark
    body += line(x0 - 16, 40, x0 - 16, hgt - 40, tone.ln, 2, "butt")
    if not empty:
        body += text(x0 + 8, 34 + cap(46) + 6, "Имя Фамилия", 46, 800, tone.fg)
        body += text(x0 + 8, 34 + cap(46) + 58, "Автоматизация бизнес-процессов", 30, 500, tone.mut)
    return w, hgt, body


@label("project", "Подпись проекта")
def _(tone, empty):
    return text_plate(tone, empty, "КЕЙС", ["Автоматизация заявок"], 48, 800, sub=(["Онлайн-школа · CRM + Telegram-бот"], 30))


@label("quote", "Короткая цитата")
def _(tone, empty):
    rows = ["Технология усиливает", "процесс, который", "уже работает"]
    w = PX + tw(rows, 46, 700) + PX + 20
    y = PY + 70
    s, h = stack(PX, y + 20, rows, 46, 700, tone.fg, 1.2, empty)
    y2 = y + 20 + h + 34
    q = rect(PX, PY, 40, 40, 9.6, C["blue"]) + rect(PX + 52, PY, 40, 40, 9.6, C["blue"])
    body = q + s
    if not empty:
        body += text(PX, y2 + cap(28), "— ИМЯ АВТОРА", 26, 700, tone.mut, ls=0.16)
    hgt = y2 + cap(28) + PY + 6
    return w, hgt, rect(0, 0, w, hgt, R["lg"], tone.bg) + body


def bars(rows, size, tone, empty=False, pad=None, gap=10, weight=800):
    """Ленточный заголовок: каждая строка на своей плашке, строка с флагом True — синяя.
    Фирменный приём для титров поверх видео."""
    pad = pad or size * 0.36
    h = cap(size) + size * 0.8
    out, y, w = "", 0, 0
    for t, hot in rows:
        tw_ = measure(t, size, weight, -0.02) - (-0.02 * size)
        bw = tw_ + 2 * pad
        out += rect(0, y, bw, h, size * 0.22, C["blue"] if hot else tone.bg)
        if not empty:
            out += text(pad, y + size * 0.36 + cap(size), t, size, weight, C["offwhite"] if hot else tone.fg, ls=-0.02)
        w = max(w, bw)
        y += h + gap
    return w, y - gap, out


@label("headline-bars", "Ленточный заголовок", ("dark", "light"))
def _(tone, empty):
    return bars([("Как убрать", False), ("ручной ввод", True), ("заявок", False)], 72, tone, empty)


@label("highlight", "Фраза с выделенным словом", ("dark", "light"))
def _(tone, empty):
    from kit import rich, rich_width
    parts = [("Выключаем ", None), ("ручной режим", "chip")]
    size = 60
    w = PX + rich_width(parts, size) + PX + size * 0.2
    h = 2 * PY + cap(size) + size * 0.5
    body = rect(0, 0, w, h, R["lg"], tone.bg)
    if not empty:
        body += rich(PX, PY + cap(size) + size * 0.2, parts, size, 800, tone.fg)
    else:
        body += rect(PX + measure("Выключаем ", size, 800, -0.03), PY + size * 0.07, rich_width([("ручной режим", "chip")], size) - size * 0.16, cap(size) + size * 0.37, size * 0.2, C["blue"])
    return w, h, body


@label("toggle-switch", "Тумблер «ручной → авто»", ("dark", "light"))
def _(tone, empty):
    tw_, th = 200, 100
    w, h = PX + tw_ + 150 + tw_ + PX, 2 * 40 + th + 64
    body = rect(0, 0, w, h, R["lg"], tone.bg)
    x2 = PX + tw_ + 150
    body += rect(PX + 3, 43, tw_ - 6, th - 6, 28, "none", tone.mut, 6) + rect(PX + 14, 54, 72, 72, 18, tone.mut)
    body += line(PX + tw_ + 34, 90, PX + tw_ + 112, 90, tone.fg, 7)
    body += f'<path d="M{PX + tw_ + 96} {72}L{PX + tw_ + 115} {90}L{PX + tw_ + 96} {108}" fill="none" stroke="{tone.fg}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>'
    body += rect(x2, 40, tw_, th, 30, C["blue"]) + rect(x2 + tw_ - 14 - 72, 54, 72, 72, 18, C["offwhite"])
    if not empty:
        body += text(PX, h - 34, "РУЧНОЙ", 24, 700, tone.mut, ls=0.16) + text(x2, h - 34, "АВТО", 24, 700, C["blue"] if tone.name != "blue" else tone.fg, ls=0.16)
    return w, h, body


@label("strike", "Зачёркнутый «ручной режим»", ("dark", "light"))
def _(tone, empty):
    size = 64
    old, new = "Ручной режим", "Система"
    wa = measure(old, size, 800, -0.02)
    w = PX + max(wa, measure(new, size, 800, -0.02)) + PX
    y1 = PY + cap(size)
    y2 = y1 + size * 0.95 + cap(size) * 0.0 + size * 0.2
    h = y2 + PY + 10
    bar = size * 0.12
    body = rect(0, 0, w, h, R["lg"], tone.bg)
    if not empty:
        body += text(PX, y1, old, size, 800, tone.mut, ls=-0.02) + text(PX, y2, new, size, 800, tone.fg, ls=-0.02)
    body += rect(PX - 4, y1 - cap(size) * 0.48 - bar / 2, wa + 8, bar, bar * 0.3, C["blue"])
    return w, h, body


def build():
    for name, (desc, fn, tones) in L.items():
        for tn in tones:
            for empty in (False, True):
                if empty and name == "percent":
                    continue  # пустая версия совпадает с key-number-empty
                w, h, body = fn(Tone(tn), empty)
                w, h = math.ceil(w), math.ceil(h)
                suffix = f"{tn}-empty" if empty else tn
                base = f"label-{name}-{suffix}"
                save(f"04_LABELS/SVG/{base}.svg", w, h, body, f"Плашка: {desc}",
                     pngs=[(f"04_LABELS/PNG/1x/{base}.png", w), (f"04_LABELS/PNG/2x/{base}@2x.png", w * 2)])
    return len(L)
