"""06_VIDEO_OVERLAYS — полноформатные прозрачные оверлеи 1080×1920 с учётом безопасных зон Reels/Shorts."""
from kit import C, T, rect, text, cap, line, logo, save, measure
from build_labels import L, Tone, text_plate, icon_tile, PX, PY, kicker, bars
from build_elements import E

V = T["video"]
VW, VH = V["width"], V["height"]
SL, SR, ST, SB = V["safe"]["left"], V["safe"]["right"], V["safe"]["top"], V["safe"]["bottom"]
X1, Y1 = VW - SR, VH - SB          # 920, 1500
SAFE_W = X1 - SL                     # 848
G, W, B = C["graphite"], C["offwhite"], C["blue"]


def place(wh_body, x, y, max_w=SAFE_W, anchor="left", grow=1.0):
    """Вписывает плашку в безопасную зону; grow>1 разрешает укрупнение для читаемости на телефоне."""
    w, h, body = wh_body
    k = min(grow, max_w / w)
    if anchor == "center":
        x = SL + (SAFE_W - w * k) / 2
    return f'<g transform="translate({x:.1f} {y:.1f}) scale({k:.4f})">{body}</g>', w * k, h * k


def center(wh_body, cy, grow=1.3):
    w, h, _ = wh_body
    k = min(grow, SAFE_W / w)
    g, _, _ = place(wh_body, SL, cy - h * k / 2, grow=grow)
    return g


def lab(name, tone="dark"):
    return L[name][1](Tone(tone), False)


O = {}


def ov(name, desc):
    def deco(fn):
        O[name] = (desc, fn)
        return fn
    return deco


@ov("lower-third", "Нижняя плашка с подписью спикера")
def _():
    w, h, _ = lab("speaker")
    k = min(1.1, SAFE_W / w)
    g, _, _ = place(lab("speaker"), SL, Y1 - h * k - 10, grow=1.1)
    return g


@ov("title-accent", "Ленточный заголовок вверху кадра")
def _():
    g, _, _ = place(bars([("Как автоматизировать", False), ("заявки", True), ("за 1 день?", False)], 84, Tone("dark")), SL, ST + 20)
    return g


@ov("title-bars-center", "Ленточный заголовок по центру (светлый)")
def _():
    w, h, body = bars([("Сначала процесс,", False), ("потом", False), ("технология", True)], 88, Tone("light"))
    g, _, _ = place((w, h, body), SL, 880 - h / 2)
    return g


@ov("toggle-switch", "Тумблер «ручной → авто» крупно")
def _():
    return center(lab("toggle-switch"), 880, 1.6)


@ov("key-thought", "Плашка с ключевой мыслью по центру")
def _():
    return center(lab("key-thought"), 880)


@ov("big-number", "Крупная цифра со шкалой")
def _():
    w, h = SAFE_W, 560
    y = 880 - h / 2
    out = rect(SL, y, w, h, 44, B) + text(SL + 50, y + 60 + cap(250), "−80%", 250, 800, W, ls=-0.05)
    n, gap = 10, 12
    cw = (w - 100 - gap * (n - 1)) / n
    by = y + 60 + cap(250) + 60
    out += "".join(rect(SL + 50 + i * (cw + gap), by, cw, cw, cw * 0.24, W if i < 8 else G) for i in range(n))
    out += text(SL + 50, by + cw + 40 + cap(40), "времени на обработку заявок", 40, 700, W)
    return out


@ov("before-after", "До / После")
def _():
    return center(lab("before-after"), 880)


@ov("steps-3", "Трёхшаговая схема")
def _():
    out, y = "", 520
    for n in ("01", "02", "03"):
        w, h, body = lab(f"step-{n}")
        k = 1.3
        out += f'<g transform="translate({SL} {y}) scale({k})">{body}</g>'
        if n != "03":
            out += line(SL + 80 * k, y + h * k + 10, SL + 80 * k, y + h * k + 52, W, 7, "round", "0 15")
        y += h * k + 62
    return out


@ov("side-panel", "Боковой информационный блок")
def _():
    tone = Tone("dark")
    w, rows = 560, [("crm", "CRM"), ("chatbot", "Telegram-бот"), ("analytics", "Аналитика")]
    h = PY + cap(26) + 34 + len(rows) * 96 + (len(rows) - 1) * 26 + PY
    x, y = SL, 700
    out = rect(x, y, w, h, 32, tone.bg) + kicker(x + PX, y + PY + cap(26), "СТЕК", "СТЕК", tone, False)
    yy = y + PY + cap(26) + 34
    for ic, t in rows:
        from build_social import num_tile
        n = [r[0] for r in rows].index(ic) + 1
        out += num_tile(x + PX, yy, 96, n, n == len(rows)) + text(x + PX + 96 + 28, yy + 48 + cap(44) / 2, t, 44, 700, tone.fg)
        yy += 96 + 26
    return out


@ov("logo-marker", "Маркер с логотипом в углу")
def _():
    return rect(SL, ST, 132, 132, 32, G) + logo(SL + 28, ST + 28, 76, W, B)


@ov("frame-minimal", "Минималистичная рамка по безопасной зоне")
def _():
    arm, r, sw = 110, 44, 8
    x0, y0, x1, y1 = SL, ST, X1, Y1
    d = (f"M{x0} {y0 + arm}V{y0 + r}A{r} {r} 0 0 1 {x0 + r} {y0}H{x0 + arm}"
         f"M{x1 - arm} {y0}H{x1 - r}A{r} {r} 0 0 1 {x1} {y0 + r}V{y0 + arm}"
         f"M{x1} {y1 - arm}V{y1 - r}A{r} {r} 0 0 1 {x1 - r} {y1}H{x1 - arm}"
         f"M{x0 + arm} {y1}H{x0 + r}A{r} {r} 0 0 1 {x0} {y1 - r}V{y1 - arm}")
    return (f'<path d="{d}" fill="none" stroke="{W}" stroke-width="{sw}" stroke-linecap="round"/>'
            + rect(x0 + 34, y0 + 34, 30, 30, 8, B))


@ov("cta-end-screen", "Финальный экран с CTA (непрозрачный)")
def _():
    out = rect(0, 0, VW, VH, 0, G)
    # деликатная мозаика модулей справа сверху, уходящая за край
    from kit import heavy_frame
    out += f'<g opacity="0.08">{heavy_frame(700, 120, 300, W)}{heavy_frame(1050, 120, 300, W)}{heavy_frame(700, 470, 300, W)}</g>'
    from kit import rich
    out += logo(SL, ST + 40, 120, W, B)
    out += rect(SL, 520, 240, 120, 36, B) + rect(SL + 240 - 14 - 92, 534, 92, 92, 22, W)
    out += text(SL, 780, "Хотите так же", 96, 800, W, ls=-0.03) + rich(SL, 780 + 118, [("в своём бизнесе?", "chip")], 96, 800, W)
    out += text(SL, 1010, "Разберу ваш процесс и покажу,", 38, 500, C["graphite_muted"])
    out += text(SL, 1010 + 52, "что можно автоматизировать", 38, 500, C["graphite_muted"])
    g, _, _ = place(lab("cta", "blue"), SL, 1180)
    out += g
    out += text(SL, Y1 - 10, "АВТОМАТИЗАЦИЯ БИЗНЕС-ПРОЦЕССОВ", 26, 500, C["graphite_muted"])
    return out


@ov("problem-solution", "Проблема → Решение")
def _():
    a = lab("problem")
    b = lab("solution", "blue")
    g1, w1, h1 = place(a, SL, 560, grow=1.3)
    y2 = 560 + h1 + 140
    g2, w2, _ = place(b, SL, y2, grow=1.3)
    ax = SL + (PX + 52) * w2 / b[0]
    arrow = (line(ax, 620 + h1 + 24, ax, y2 - 28, W, 8)
             + f'<path d="M{ax - 22} {y2 - 50}L{ax} {y2 - 28}L{ax + 22} {y2 - 50}" fill="none" stroke="{W}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>')
    return g1 + arrow + g2


@ov("tool-name", "Плашка с названием сервиса")
def _():
    tone = Tone("light")
    t = "Название сервиса"
    w = PX + 104 + 32 + max(measure(t, 48, 800), 260) + PX
    h = 104 + 2 * 32
    out = rect(0, 0, w, h, 32, tone.bg) + icon_tile(32, 32, 104, "integrations", Tone("dark"))
    out += text(32 + 104 + 32, 32 + 34, "ИНСТРУМЕНТ", 24, 700, tone.mut, ls=0.16)
    out += text(32 + 104 + 32, 32 + 34 + 26 + cap(48), t, 48, 800, tone.fg)
    g, _, _ = place((w, h, out), SL, ST + 40, grow=1.2)
    return g


def safe_guide():
    """Служебный слой: безопасные зоны Reels/Shorts. Не для публикации."""
    red = "#FF3B30"
    out = rect(0, 0, VW, ST, 0, red, extra=' fill-opacity="0.18"') + rect(0, Y1, VW, SB, 0, red, extra=' fill-opacity="0.18"')
    out += rect(X1, ST, SR, Y1 - ST, 0, red, extra=' fill-opacity="0.18"') + rect(0, ST, SL, Y1 - ST, 0, red, extra=' fill-opacity="0.10"')
    out += rect(SL, ST, SAFE_W, Y1 - ST, 0, "none", B, 3, ' stroke-dasharray="14 10"')
    out += text(SL + 20, ST + 50, f"Безопасная зона {SAFE_W}×{Y1 - ST}", 30, 700, B)
    out += text(40, 150, "Шапка / профиль", 30, 600, red) + text(40, Y1 + 120, "Подпись, кнопки, музыка", 30, 600, red)
    out += text(X1 + 20, 900, "Лайки", 26, 600, red)
    return out


def build():
    for name, (desc, fn) in O.items():
        save(f"06_VIDEO_OVERLAYS/SVG/overlay-reels-{name}.svg", VW, VH, fn(), desc,
             pngs=[(f"06_VIDEO_OVERLAYS/PNG/overlay-reels-{name}.png", VW)])
    save("06_VIDEO_OVERLAYS/SVG/guide-safe-zones-1080x1920.svg", VW, VH, safe_guide(), "Гайд безопасных зон",
         pngs=[("06_VIDEO_OVERLAYS/PNG/guide-safe-zones-1080x1920.png", VW)])
    return len(O)
