"""08_SOCIAL_TEMPLATES — редактируемые шаблоны постов 1080×1350 и сторис 1080×1920 (SVG с живым текстом + PNG-превью).
Фирменные приёмы: ключевое слово на синей плашке (rich/chip), гигантский модуль за краем кадра, тумблер «ручной → авто»."""
from kit import C, rect, text, measure, cap, line, logo, heavy_frame, dot, save, rich
from build_labels import L, Tone, icon_tile
from build_icons import draw as icon
from build_bg import BGS

G, W, B = C["graphite"], C["offwhite"], C["blue"]
MX = 88
HANDLE = "@username"
DASH = ' stroke-dasharray="14 12"'


def wrap(s, size, weight, maxw):
    words, rows, cur = s.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if measure(t, size, weight) > maxw and cur:
            rows.append(cur)
            cur = wd
        else:
            cur = t
    return rows + [cur]


class Frame:
    def __init__(self, h, dark=True):
        self.w, self.h = 1080, h
        self.story = h > 1500
        self.top = 250 if self.story else 96
        self.off = 170 if self.story else 0  # в сторис контент опускаем к оптическому центру
        self.bot = h - (330 if self.story else 96)
        self.fg = W if dark else G
        self.mut = C["graphite_muted"] if dark else C["offwhite_muted"]
        self.ln = C["graphite_line"] if dark else C["offwhite_line"]
        self.surf = C["graphite_surface"] if dark else C["offwhite_surface"]
        self.dark = dark


def heading(f, y, rows, size, lh=1.0, ls=-0.035, fill=None):
    """Заголовок из строк rich-частей. y — верх блока. Возвращает (svg, низ блока)."""
    fill = fill or f.fg
    out = ""
    for i, r in enumerate(rows):
        parts = [(r, None)] if isinstance(r, str) else r
        out += rich(MX, y + cap(size) + i * size * lh, parts, size, 800, fill, ls)
    return out, y + cap(size) + (len(rows) - 1) * size * lh


def para(f, y, s, size=38, weight=500, fill=None, lh=1.42, maxw=None):
    rows = wrap(s, size, weight, maxw or f.w - 2 * MX)
    out = "".join(text(MX, y + cap(size) + i * size * lh, r, size, weight, fill or f.mut) for i, r in enumerate(rows))
    return out, y + cap(size) + (len(rows) - 1) * size * lh


def header(f, kick=None, counter=None, fg=None, mut=None, accent=B):
    fg, mut = fg or f.fg, mut or f.mut
    out = logo(MX, f.top, 64, fg, accent)
    if kick:
        out += rect(MX + 64 + 28, f.top + 23, 18, 18, 5, accent) + text(MX + 64 + 58, f.top + 32 + cap(24) / 2, kick, 24, 700, mut, ls=0.16)
    if counter:
        out += text(f.w - MX, f.top + 32 + cap(26) / 2, counter, 26, 700, mut, anchor="end")
    return out


def arrow_btn(x, y, s, fg, filled=None, arr=None):
    arr = arr or fg
    base = rect(x, y, s, s, s * 0.26, filled) if filled else rect(x + 1.5, y + 1.5, s - 3, s - 3, s * 0.26, "none", fg, 3)
    k = s / 84
    return (base + line(x + 24 * k, y + s / 2, x + 58 * k, y + s / 2, arr, 5 * k)
            + f'<path d="M{x + 46 * k:g} {y + 30 * k:g}L{x + 59 * k:g} {y + s / 2:g}L{x + 46 * k:g} {y + 54 * k:g}" fill="none" stroke="{arr}" stroke-width="{5 * k:g}" stroke-linecap="round" stroke-linejoin="round"/>')


def footer(f, arrow=True, hint=None, fg=None, mut=None):
    fg, mut = fg or f.fg, mut or f.mut
    out = text(MX, f.bot, HANDLE, 28, 600, mut)
    if hint:
        out += text(f.w - MX - 84 - 24, f.bot, hint, 28, 600, mut, anchor="end")
    if arrow:
        out += arrow_btn(f.w - MX - 84, f.bot - 42 - cap(28) / 2, 84, fg)
    return out


def toggle(x, y, w, on, track_on=B, knob_on=W, off_col=None):
    """Тумблер — фирменный символ «выключаем ручной режим»."""
    h = w * 0.5
    r = h * 0.3
    k = h * 0.72
    p = (h - k) / 2
    if on:
        return rect(x, y, w, h, r, track_on) + rect(x + w - p - k, y + p, k, k, k * 0.24, knob_on)
    sw = max(4, w * 0.025)
    return rect(x + sw / 2, y + sw / 2, w - sw, h - sw, r, "none", off_col, sw) + rect(x + p, y + p, k, k, k * 0.24, off_col)


def bg(f, kind):
    return BGS[kind](f.w, f.h)


TPL = {}


def tpl(name, desc, dark=True):
    def deco(fn):
        TPL[name] = (desc, fn, dark)
        return fn
    return deco


@tpl("reels-cover", "Обложка Reels")
def _(f):
    out = bg(f, "solid-graphite")
    s = 600
    gx, gy = f.w - s * 0.62, f.h - s * 0.66
    out += heavy_frame(gx, gy, s, C["graphite_line"]) + rect(gx - 220, gy, 160, 160, 38, B)
    out += header(f)
    h, _ = heading(f, f.top + f.off + 170, ["Сначала", "процесс.", [("Потом", "blue")], [("технология", "blue")]], 150, 0.95)
    out += h + text(MX, f.bot - 36, "АВТОМАТИЗАЦИЯ", 30, 600, f.fg) + text(MX, f.bot, "БИЗНЕС-ПРОЦЕССОВ", 30, 600, f.fg)
    return out


@tpl("case-cover", "Обложка кейса")
def _(f):
    out = bg(f, "solid-graphite") + header(f, "КЕЙС")
    y = f.top + f.off + 160
    h, yb = heading(f, y, ["Автоматизация", "заявок для", [("онлайн-школы", "chip")]], 96, 1.1)
    out += h
    my = yb + 120
    for i, (num, sub, col) in enumerate((("−80%", "времени на обработку", B), ("+2×", "рост конверсии", W))):
        x = MX + i * 470
        out += text(x - 4, my + cap(150), num, 150, 800, col, ls=-0.04) + text(x, my + cap(150) + 56, sub, 30, 600, f.mut)
    sy = my + cap(150) + 120
    sh = f.bot - 70 - sy
    if sh > 140:
        out += (f'<g id="photo-slot">{rect(MX, sy, f.w - 2 * MX, sh, 32, f.surf)}'
                f'{rect(MX + 2, sy + 2, f.w - 2 * MX - 4, sh - 4, 30, "none", f.ln, 3, DASH)}'
                f'{text(f.w / 2, sy + sh / 2 + 10, "Скриншот или фото проекта", 28, 600, f.mut, anchor="middle")}</g>')
    return out + footer(f)


@tpl("expert-post", "Экспертный пост", dark=False)
def _(f):
    out = bg(f, "solid-offwhite") + heavy_frame(f.w - 330, -170, 520, C["offwhite_surface"]) + header(f, "ЭКСПЕРТИЗА")
    y = f.top + f.off + 170
    h, yb = heading(f, y, ["Почему", "автоматизация", [("не работает", "chip")], "без описанного", "процесса"], 90, 1.08)
    out += h
    p, yb = para(f, yb + 70, "Если процесс живёт в головах сотрудников, бот или CRM только ускорят хаос.", 38)
    out += p
    py = yb + 70
    ph = f.bot - 70 - py
    if ph > 150:
        ph = min(ph, 230)
        out += rect(MX, py, f.w - 2 * MX, ph, 32, G) + rect(MX + 40, py + 44, 18, 18, 5, B)
        out += text(MX + 72, py + 44 + 9 + cap(24) / 2, "ГЛАВНОЕ", 24, 700, C["graphite_muted"], ls=0.16)
        out += text(MX + 40, py + 44 + 18 + 30 + cap(44), "Сначала процесс —", 44, 800, W)
        out += text(MX + 40, py + 44 + 18 + 30 + cap(44) + 56, [("потом ", W), ("инструменты", B)], 44, 800)
    return out + footer(f)


@tpl("quote-post", "Пост с крупной цитатой")
def _(f):
    out = bg(f, "solid-graphite") + heavy_frame(f.w - 300, f.h - 330, 560, C["graphite_surface"]) + header(f)
    y = f.top + f.off + 190
    out += rect(MX, y, 70, 110, 20, B) + rect(MX + 92, y, 70, 110, 20, B)
    h, yb = heading(f, y + 190, ["Технология", "не исправит", "процесс, который", [("не работает", "chip")]], 96, 1.1)
    out += h + rect(MX, yb + 96, 56, 4, 2, f.mut) + text(MX + 80, yb + 96 + 2 + cap(28) / 2, "ИМЯ ФАМИЛИЯ", 28, 700, f.mut, ls=0.16)
    return out + footer(f, False)


@tpl("key-number-post", "Пост с ключевой цифрой")
def _(f):
    out = bg(f, "solid-blue") + header(f, fg=W, mut=W, accent=W)
    y = f.top + f.off + 200
    out += text(MX - 16, y + cap(340), "−80%", 340, 800, W, ls=-0.05)
    by = y + cap(340) + 90
    n, gap = 10, 14
    cw = (f.w - 2 * MX - gap * (n - 1)) / n
    out += "".join(rect(MX + i * (cw + gap), by, cw, cw, cw * 0.24, W if i < 8 else G) for i in range(n))
    p, _ = para(f, by + cw + 80, "времени на обработку заявок после внедрения CRM и чат-бота", 50, 700, W, 1.18)
    return out + p + text(MX, f.bot, HANDLE, 28, 600, W, opacity=0.85)


@tpl("product-announce", "Анонс продукта")
def _(f):
    out = bg(f, "solid-graphite") + header(f, "НОВЫЙ ПРОДУКТ")
    y = f.top + f.off + 160
    h, yb = heading(f, y, ["Аудит", "процессов", [("за 7 дней", "chip")]], 110, 1.06)
    out += h
    p, yb = para(f, yb + 70, "Находим, где команда теряет время, и даём план автоматизации с расчётом эффекта.", 36)
    out += p
    yy = yb + 70
    ch = min(124, (f.bot - 90 - yy - 2 * 16) / 3)
    for i, (ic, t, d) in enumerate((("process", "Карта процессов", "Как работа идёт сейчас"), ("analytics", "Расчёт экономии", "Часы и деньги в месяц"), ("system", "План внедрения", "Что, в каком порядке, чем"))):
        ts = min(88, ch - 24)
        out += rect(MX, yy, f.w - 2 * MX, ch, 28, f.surf) + icon_tile(MX + 18, yy + (ch - ts) / 2, ts, ic, Tone("dark"))
        out += text(MX + ts + 44, yy + ch / 2 - 6, t, 38, 800, W) + text(MX + ts + 44, yy + ch / 2 + 36, d, 28, 500, f.mut)
        out += text(f.w - MX - 32, yy + ch / 2 + cap(30) / 2, f"0{i + 1}", 30, 800, B, anchor="end")
        yy += ch + 16
    return out + footer(f)


@tpl("process-explain", "Объяснение бизнес-процесса", dark=False)
def _(f):
    out = bg(f, "solid-offwhite") + header(f, "КАК ЭТО РАБОТАЕТ")
    y = f.top + f.off + 160
    h, yb = heading(f, y, ["Путь заявки", [("без ручной работы", "chip")]], 82, 1.16)
    out += h
    steps = [("website", "Заявка с сайта", "Форма или квиз"), ("crm", "Карточка в CRM", "Создаётся автоматически"),
             ("chatbot", "Ответ бота", "Клиент получает ответ за 30 сек"), ("reports", "Отчёт", "Собирается каждый понедельник")]
    yy = yb + 100
    ts = 120
    gap = (f.bot - 110 - yy - ts) / 3
    for i, (ic, t, d) in enumerate(steps):
        last = i == len(steps) - 1
        if not last:
            out += line(MX + ts / 2, yy + ts, MX + ts / 2, yy + gap, C["offwhite_line"], 6, "butt")
        out += rect(MX, yy, ts, ts, 30, B if last else G) + f'<g transform="translate({MX + 28} {yy + 28}) scale({64 / 48:.4f})">{icon(ic, W, W if last else B)}</g>'
        out += text(MX + ts + 36, yy + 22 + cap(24), f"ШАГ 0{i + 1}", 24, 700, B if last else C["offwhite_muted"], ls=0.16)
        out += text(MX + ts + 36, yy + 22 + cap(24) + 22 + cap(42), t, 42, 800, G)
        out += text(MX + ts + 36, yy + 22 + cap(24) + 22 + cap(42) + 44, d, 28, 500, C["offwhite_muted"])
        yy += gap
    return out + footer(Frame(f.h, dark=False))


@tpl("cta-post", "Пост с CTA")
def _(f):
    out = bg(f, "solid-graphite") + header(f)
    y = f.top + f.off + 160
    h, yb = heading(f, y, ["Выключаем", [("ручной режим", "blue")]], 124, 1.0)
    out += h
    ty = yb + 100
    tw = 520
    out += toggle(MX, ty, tw, True)
    out += text(MX + tw + 40, ty + 70 + cap(30), "АВТО", 30, 800, B, ls=0.16)
    out += text(MX + tw + 40, ty + 70 + cap(30) + 50, "включено", 30, 500, f.mut)
    w, hh, cta = L["cta"][1](Tone("blue"), False)
    k = min(1, (f.w - 2 * MX) / w)
    out += f'<g transform="translate({MX} {ty + tw * 0.5 + 90}) scale({k:.4f})">{cta}</g>'
    return out + text(MX, f.bot, HANDLE, 28, 600, f.mut)


@tpl("before-after-post", "Пост «Ручной режим / Автоматизация»", dark=False)
def _(f):
    out = bg(f, "solid-offwhite") + header(f, "ДО / ПОСЛЕ")
    y = f.top + f.off + 160
    h, yb = heading(f, y, ["Из ручных", "процессов —", [("в систему", "chip")]], 96, 1.08)
    out += h
    cy = yb + 90
    ch = min(250, (f.bot - 80 - cy - 20) / 2)
    for i, (on, t, num, sub) in enumerate(((False, "Ручной режим", "10 часов", "в неделю"), (True, "Автоматизация", "1 час", "в неделю"))):
        yy = cy + i * (ch + 20)
        bgc, fg = (B, W) if on else (C["offwhite_surface"], G)
        mut = W if on else C["offwhite_muted"]
        out += rect(MX, yy, f.w - 2 * MX, ch, 34, bgc)
        out += toggle(MX + 40, yy + 40, 150, on, W, B, C["offwhite_muted"])
        out += text(MX + 40, yy + ch - 44, t, 34, 700, mut, opacity=0.85 if on else None)
        out += text(f.w - MX - 40, yy + ch / 2 + cap(96) / 2 - 14, num, 96, 800, fg, anchor="end", ls=-0.03)
        out += text(f.w - MX - 40, yy + ch / 2 + cap(96) / 2 + 36, sub, 28, 600, mut, anchor="end", opacity=0.85 if on else None)
    return out + footer(Frame(f.h, dark=False))


# ---------------------------------------------------------------- карусели
MISTAKES = [
    ("Нет анализа процесса", "Автоматизируют то, что никто не описал. Система повторяет хаос — только быстрее.",
     "Сначала опишите процесс: шаги, роли, сроки."),
    ("Слишком сложные решения", "Под простую задачу строят громоздкую систему, которую некому поддерживать.",
     "Начните с одного узкого места и простого решения."),
    ("Нет интеграций", "Данные вручную переносят между сервисами — и ошибки возвращаются.",
     "Свяжите сайт, CRM и мессенджеры, чтобы данные шли сами."),
    ("Игнорирование команды", "Систему внедряют без тех, кто будет работать в ней каждый день.",
     "Вовлекайте сотрудников с первого дня."),
    ("Нет контроля результата", "Не измеряют время и деньги до и после — эффект нельзя доказать.",
     "Зафиксируйте метрики до старта и сравните через месяц."),
]


def mistakes_cover(f):
    f.__init__(f.h, dark=False)
    out = bg(f, "solid-offwhite") + heavy_frame(f.w - 300, -150, 500, C["offwhite_surface"]) + header(f, counter="01/07")
    y = f.top + f.off + 150
    out += rich(MX, y + cap(200), [("5", "chip"), (" ошибок", None)], 200, 800, G, -0.045)
    out += text(MX, y + cap(200) + 110, "в автоматизации", 64, 700, G, ls=-0.02) + text(MX, y + cap(200) + 186, "бизнес-процессов", 64, 700, G, ls=-0.02)
    yy = y + cap(200) + 186 + 90
    step = min(96, (f.bot - 120 - yy) / 5)
    for i, (t, _, _) in enumerate(MISTAKES):
        out += line(MX, yy, f.w - MX, yy, C["offwhite_line"], 2, "butt")
        out += text(MX, yy + step / 2 + cap(30) / 2, f"0{i + 1}", 30, 800, B) + text(MX + 76, yy + step / 2 + cap(34) / 2, t, 34, 600, G)
        yy += step
    return out + footer(f, hint="Листайте")


def mistake_slide(i):
    def fn(f):
        f.__init__(f.h, dark=i % 2 == 0)
        out = bg(f, "solid-graphite" if f.dark else "solid-offwhite") + header(f, "ОШИБКА", f"0{i + 2}/07")
        t, d, fix = MISTAKES[i]
        y = f.top + f.off + 140
        out += text(MX - 10, y + cap(260), f"0{i + 1}", 260, 800, B, ls=-0.05)
        h, yb = heading(f, y + cap(260) + 80, wrap(t, 92, 800, f.w - 2 * MX), 92, 1.04)
        out += h
        p, yb = para(f, yb + 56, d, 38)
        out += p
        fy = yb + 64
        fh = 190
        if fy + fh < f.bot - 120:
            out += rect(MX, fy, f.w - 2 * MX, fh, 30, f.surf) + rect(MX + 36, fy + 40, 18, 18, 5, B)
            out += text(MX + 68, fy + 49 + cap(24) / 2, "КАК НАДО", 24, 700, B, ls=0.16)
            fr = wrap(fix, 36, 700, f.w - 2 * MX - 72)
            out += "".join(text(MX + 36, fy + 92 + cap(36) + k * 46, r, 36, 700, f.fg) for k, r in enumerate(fr[:2]))
        out += "".join(rect(MX + k * 40, f.bot - cap(28) - 76, 24, 24, 6, B if k == i else f.ln) for k in range(5))
        return out + footer(f)
    return fn


def final_cta(counter):
    def fn(f):
        out = bg(f, "solid-blue") + header(f, counter=counter, fg=W, mut=W, accent=W)
        y = f.top + f.off + 170
        out += toggle(MX, y, 260, True, W, B)
        h, yb = heading(f, y + 210, ["Найдём, что", "автоматизировать", "в вашем бизнесе"], 92, 1.04, fill=W)
        out += h
        w, hh, cta = L["cta"][1](Tone("dark"), False)
        k = min(1, (f.w - 2 * MX) / w)
        out += f'<g transform="translate({MX} {yb + 100}) scale({k:.4f})">{cta}</g>'
        return out + text(MX, f.bot, HANDLE, 28, 600, W, opacity=0.85)
    return fn


def ba_cover(f):
    out = bg(f, "solid-graphite") + heavy_frame(f.w - 330, f.h - 360, 560, C["graphite_surface"]) + header(f, "ДО / ПОСЛЕ", "01/04")
    y = f.top + f.off + 170
    h, yb = heading(f, y, ["Как мы", "выключили", [("ручной режим", "chip")], "в отделе продаж"], 104, 1.08)
    out += h
    ty = yb + 110
    out += toggle(MX, ty, 200, False, off_col=f.mut) + line(MX + 236, ty + 50, MX + 330, ty + 50, W, 6)
    out += f'<path d="M{MX + 312} {ty + 32}L{MX + 332} {ty + 50}L{MX + 312} {ty + 68}" fill="none" stroke="{W}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>'
    out += toggle(MX + 370, ty, 200, True)
    return out + footer(f, hint="Листайте")


def ba_slide(after):
    def fn(f):
        f.__init__(f.h, dark=not after)
        out = bg(f, "solid-offwhite" if after else "solid-graphite") + header(f, "ПОСЛЕ" if after else "ДО", "03/04" if after else "02/04")
        y = f.top + f.off + 160
        out += toggle(MX, y, 220, after, off_col=f.mut)
        h, yb = heading(f, y + 160, ["Автоматический", "режим"] if after else ["Ручной", "режим"], 104, 1.0)
        out += h
        items = (["Заявка сразу попадает в CRM", "Бот отвечает за 30 секунд", "Менеджер видит тёплых клиентов", "Отчёт собирается сам"] if after else
                 ["Заявки копируют из почты в таблицу", "Ответ клиенту — через 3 часа", "Менеджер забывает перезвонить", "Отчёт собирают вручную"])
        yy = yb + 80
        for it in items:
            out += line(MX, yy, f.w - MX, yy, f.ln, 2, "butt")
            out += rect(MX, yy + 25, 24, 24, 6, B if after else f.mut) + text(MX + 50, yy + 37 + cap(34) / 2, it, 34, 600, f.fg)
            yy += 74
        num = ("1 час", "в неделю на контроль") if after else ("10 часов", "в неделю вручную")
        out += text(MX - 4, f.bot - 120, num[0], 110, 800, B if after else f.fg, ls=-0.03)
        out += text(MX + measure(num[0], 110, 800, -0.03) + 28, f.bot - 120, num[1], 30, 600, f.mut)
        return out + footer(f)
    return fn


def ba_result(f):
    out = bg(f, "solid-blue") + header(f, "РЕЗУЛЬТАТ", "04/04", fg=W, mut=W, accent=W)
    y = f.top + f.off + 170
    out += text(MX - 8, y + cap(220), "10 ч", 220, 800, W, ls=-0.045, opacity=0.45)
    out += text(MX - 8, y + cap(220) + 250, "1 ч", 220, 800, W, ls=-0.045)
    out += text(MX + measure("10 ч", 220, 800, -0.045) + 40, y + cap(220) - 10, "было", 34, 700, W, opacity=0.6)
    out += text(MX + measure("1 ч", 220, 800, -0.045) + 40, y + cap(220) + 240, "стало", 34, 700, W)
    p, yb = para(f, y + cap(220) + 340, "в неделю на обработку заявок — остальное делает система", 40, 700, W, 1.25)
    out += p
    w, hh, cta = L["cta"][1](Tone("dark"), False)
    k = min(1, (f.w - 2 * MX) / w)
    out += f'<g transform="translate({MX} {yb + 80}) scale({k:.4f})">{cta}</g>'
    return out + text(MX, f.bot, HANDLE, 28, 600, W, opacity=0.85)


CAROUSELS = {
    "carousel-5-mistakes": ("Карусель «5 ошибок»", [mistakes_cover] + [mistake_slide(i) for i in range(5)] + [final_cta("07/07")]),
    "carousel-before-after": ("Карусель «До / После»", [ba_cover, ba_slide(False), ba_slide(True), ba_result]),
}


def build():
    n = 0
    for name, (desc, fn, dark) in TPL.items():
        for h, tag in ((1350, "post-1080x1350"), (1920, "story-1080x1920")):
            body = fn(Frame(h, dark))
            save(f"08_SOCIAL_TEMPLATES/SVG/{name}-{tag}.svg", 1080, h, body, desc, pngs=[(f"08_SOCIAL_TEMPLATES/PNG/{name}-{tag}.png", 1080)])
        n += 1
    for name, (desc, slides) in CAROUSELS.items():
        for i, fn in enumerate(slides, 1):
            body = fn(Frame(1350, True))
            save(f"08_SOCIAL_TEMPLATES/SVG/{name}/{name}-{i:02d}-1080x1350.svg", 1080, 1350, body, f"{desc}, слайд {i}",
                 pngs=[(f"08_SOCIAL_TEMPLATES/PNG/{name}/{name}-{i:02d}-1080x1350.png", 1080)])
        body = slides[0](Frame(1920, True))
        save(f"08_SOCIAL_TEMPLATES/SVG/{name}/{name}-cover-story-1080x1920.svg", 1080, 1920, body, desc,
             pngs=[(f"08_SOCIAL_TEMPLATES/PNG/{name}/{name}-cover-story-1080x1920.png", 1080)])
        n += 1
    return n
