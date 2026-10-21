"""03_ICONS — 25 иконок на сетке 48, обводка 3, скругления как у модулей. Синий — один «акцентный модуль» на иконку."""
from kit import C, rect, save, T

G, W, B = C["graphite"], C["offwhite"], C["blue"]
SW = T["stroke"]["icon"]


def S(d):  # контур
    return f'<path d="{d}" fill="none" stroke="{{m}}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round"/>'


def SA(d):  # контур акцентом
    return f'<path d="{d}" fill="none" stroke="{{a}}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round"/>'


def R(x, y, w, h, r):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="none" stroke="{{m}}" stroke-width="{SW}"/>'


def F(x, y, w, h, r, acc=False):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{{{"a" if acc else "m"}}}"/>'


def O(cx, cy, r, fill=None):
    if fill:
        return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{{{fill}}}"/>'
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{{m}}" stroke-width="{SW}"/>'


BUBBLE = "M11 7h26a7 7 0 0 1 7 7v14a7 7 0 0 1-7 7H22l-8 7v-7h-3a7 7 0 0 1-7-7V14a7 7 0 0 1 7-7Z"

ICONS = {
    "automation": ("Автоматизация", [S("M9 24A15 15 0 0 1 34.6 13.4"), S("M27.6 13.4H34.6V6.4"),
                                     S("M39 24A15 15 0 0 1 13.4 34.6"), S("M20.4 34.6H13.4V41.6"), F(19.5, 19.5, 9, 9, 2.2, True)]),
    "process": ("Бизнес-процессы", [R(4, 4, 13, 13, 3.5), S("M17 10.5H31"), R(31, 4, 13, 13, 3.5),
                                    S("M37.5 17V21.5A3 3 0 0 1 34.5 24.5H13.5A3 3 0 0 0 10.5 27.5V31"), F(4, 31, 13, 13, 3.5, True)]),
    "ai": ("AI", [R(12, 12, 24, 24, 5), S("M20 5V12M28 5V12M20 36V43M28 36V43M5 20H12M5 28H12M36 20H43M36 28H43"),
                  F(19, 19, 10, 10, 2.5, True)]),
    "crm": ("CRM", [R(4, 8, 40, 32, 6), O(16, 19.5, 4.5), S("M9 33C9 29 12 26.5 16 26.5S23 29 23 33"),
                    S("M28 18H38M28 24H35"), F(28, 29, 6, 6, 1.5, True)]),
    "sales": ("Продажи", [S("M25 5H39A4 4 0 0 1 43 9V23.3A4 4 0 0 1 41.8 26.1L26.3 41.6A4 4 0 0 1 20.7 41.6L6.4 27.3A4 4 0 0 1 6.4 21.7L22.2 6.2A4 4 0 0 1 25 5Z"),
                         F(31, 11, 6, 6, 1.5, True)]),
    "leads": ("Заявки", [R(4, 20, 40, 22, 6), S("M4 31H14.5L17.5 35.5H30.5L33.5 31H44"), SA("M24 4V21M18 15.5L24 21.5L30 15.5")]),
    "clients": ("Клиенты", [O(18, 17, 6), S("M6 41C6 34.4 11.4 30 18 30S30 34.4 30 41"), O(33, 14, 4.5, "a"),
                           S("M34 25.5C39.5 26 43 30 43 35.5")]),
    "messages": ("Сообщения", [S(BUBBLE), F(13.5, 18.5, 5, 5, 1.3), F(21.5, 18.5, 5, 5, 1.3), F(29.5, 18.5, 5, 5, 1.3, True)]),
    "notifications": ("Уведомления", [S("M12 34V22A12 12 0 0 1 36 22V34"), S("M7 34H41"), S("M24 6V10"), S("M20 40H28"),
                                      F(34, 3, 9, 9, 2.4, True)]),
    "analytics": ("Аналитика", [R(6, 24, 8, 18, 2.5), R(20, 14, 8, 28, 2.5), F(34, 6, 8, 36, 2.5, True)]),
    "reports": ("Отчёты", [S("M12 4H29L40 15V40A4 4 0 0 1 36 44H12A4 4 0 0 1 8 40V8A4 4 0 0 1 12 4Z"), S("M29 4V12A3 3 0 0 0 32 15H40"),
                          S("M15 21H25"), F(15, 30, 4.5, 7, 1.2), F(21.75, 27, 4.5, 10, 1.2), F(28.5, 24, 4.5, 13, 1.2, True)]),
    "integrations": ("Интеграции", [f'<g transform="rotate(-45 24 24)">{R(4, 17, 23, 14, 7)}'
                                    f'<rect x="21" y="17" width="23" height="14" rx="7" fill="none" stroke="{{a}}" stroke-width="{SW}"/></g>']),
    "website": ("Сайт", [R(4, 7, 40, 34, 6), S("M4 16H44"), F(9, 10, 3.5, 3.5, 1), F(14.5, 10, 3.5, 3.5, 1), F(20, 10, 3.5, 3.5, 1),
                        F(10, 22, 12, 13, 2.5, True), S("M27 24H38M27 30H35")]),
    "chatbot": ("Чат-бот", [S("M10 6H38A6 6 0 0 1 44 12V30A6 6 0 0 1 38 36H24L15 43V36H10A6 6 0 0 1 4 30V12A6 6 0 0 1 10 6Z"),
                           F(15.5, 12.5, 7, 7, 1.8), F(25.5, 12.5, 7, 7, 1.8), F(15.5, 22.5, 7, 7, 1.8), F(25.5, 22.5, 7, 7, 1.8, True)]),
    "time": ("Время", [O(24, 24, 19), S("M24 24V13"), SA("M24 24L32 29")]),
    "savings": ("Экономия", [R(4, 4, 40, 40, 10), S("M16 32L32 16"), F(12.5, 12.5, 7, 7, 1.8), F(28.5, 28.5, 7, 7, 1.8, True)]),
    "money": ("Деньги", [R(4, 12, 40, 24, 6), O(24, 24, 6), F(9, 17, 5, 5, 1.3, True), F(34, 26, 5, 5, 1.3)]),
    "growth": ("Рост", [S("M5 38L16 27L24 34L42 16"), SA("M32 15H43V26")]),
    "team": ("Команда", [O(24, 15, 5.5), S("M14 39C14 32.5 18.5 28.5 24 28.5S34 32.5 34 39"), O(10, 19, 4),
                        S("M3.5 37C3.5 32.5 6 29.5 9.5 29"), O(38, 19, 4, "a"), S("M44.5 37C44.5 32.5 42 29.5 38.5 29")]),
    "tasks": ("Задачи", [F(5, 5, 10, 10, 2.5, True), R(5, 19, 10, 10, 2.5), R(5, 33, 10, 10, 2.5), S("M21 10H43M21 24H43M21 38H36")]),
    "system": ("Система", [R(5, 5, 16, 16, 4.5), R(27, 5, 16, 16, 4.5), R(5, 27, 16, 16, 4.5), F(27, 27, 16, 16, 4.5, True)]),
    "errors": ("Ошибки", [S("M24 5L44 41H4Z"), S("M24 17V28"), F(22, 32, 4, 4, 1, True)]),
    "control": ("Контроль", [S("M12 6V42M24 6V42M36 6V42"), F(7.5, 26, 9, 9, 2.4), F(19.5, 11, 9, 9, 2.4, True), F(31.5, 20, 9, 9, 2.4)]),
    "manual": ("Ручная работа", [R(4, 14, 40, 20, 7), F(9, 19, 10, 10, 2.5), SA("M27 24H36")]),
    "result": ("Результат", [R(4, 4, 40, 40, 10), R(12, 12, 24, 24, 6), F(19, 19, 10, 10, 2.5, True)]),
}

VARIANTS = {
    "on-light": (G, G, None),
    "on-light-accent": (G, B, None),
    "on-dark": (W, W, None),
    "on-dark-accent": (W, B, None),
    "tile-dark": (W, B, G),
    "tile-light": (G, B, W),
}


def draw(name, m, a):
    return "".join(p.replace("{m}", m).replace("{a}", a) for p in ICONS[name][1])


def build():
    for name, (title, _) in ICONS.items():
        for v, (m, a, tile) in VARIANTS.items():
            if tile:
                body = rect(0, 0, 64, 64, 16, tile) + f'<g transform="translate(12 12) scale(0.8333)">{draw(name, m, a)}</g>'
                w = 64
            else:
                body, w = draw(name, m, a), 48
            save(f"03_ICONS/SVG/icon-{name}-{v}.svg", w, w, body, f"Иконка: {title}",
                 pngs=[(f"03_ICONS/PNG/{s}/icon-{name}-{v}.png", s) for s in (256, 512)])
    return len(ICONS)
