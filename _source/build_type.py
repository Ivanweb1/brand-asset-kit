"""05_TYPOGRAPHY — текстовые композиции. Каждая: SVG с живым текстом, SVG в кривых, PNG."""
import math

from kit import C, text, measure, cap, save, rect

G, W, B = C["graphite"], C["offwhite"], C["blue"]
DISPLAY_LS = -0.02


def block(rows, size, weight, lh, ls=0.0, align="start"):
    """rows: списки spans (цвет None = основной). Возвращает функцию (fg, outline) -> (w, h, body)."""
    def draw(fg, outline):
        widths = [measure("".join(t for t, _ in r), size, weight, ls) - (ls * size) for r in rows]
        w = max(widths)
        h = cap(size) + (len(rows) - 1) * size * lh
        # поле под выносные элементы (й, Д, р, у) — 0.28 кегля снизу, 0.08 сверху
        top, bot = size * 0.12, size * 0.30
        out = ""
        for i, r in enumerate(rows):
            spans = [(t, c or fg) for t, c in r]
            x = {"start": 0, "middle": w / 2, "end": w}[align]
            out += text(x + 2, top + cap(size) + i * size * lh, spans, size, weight, fg, anchor=align, ls=ls, outline=outline)
        return math.ceil(w + 4), math.ceil(h + top + bot), out
    return draw


def poster_slogan(fg, outline):
    """Как на постере: две группы по 0.89 интерлиньяжа, между группами 1.36 кегля."""
    size, lh, gap = 160, 0.89, 1.36
    rows = [("Сначала", None), ("процесс", None), ("Потом", B), ("технология", B)]
    ys = [0, lh, lh + gap, 2 * lh + gap]
    w = max(measure(t, size, 800, DISPLAY_LS) for t, _ in rows) - DISPLAY_LS * size
    top = size * 0.12
    out = "".join(text(2, top + cap(size) + k * size, t, size, 800, c or fg, ls=DISPLAY_LS, outline=outline) for (t, c), k in zip(rows, ys))
    return math.ceil(w + 4), math.ceil(top + cap(size) + ys[-1] * size + size * 0.3), out


def r(*spans):
    return [s if isinstance(s, tuple) else (s, None) for s in spans]


COMPS = {
    "slogan-process-technology-stacked": poster_slogan,
    "slogan-process-technology-2lines": block([r("Сначала процесс"), r(("Потом технология", B))], 120, 800, 1.05, DISPLAY_LS),
    "slogan-process-technology-1line": block([r("Сначала процесс. ", ("Потом технология", B))], 96, 800, 1, DISPLAY_LS),
    "slogan-manual-off-stacked": block([r("Выключаем"), r(("ручной режим", B))], 140, 800, 1.02, DISPLAY_LS),
    "slogan-manual-off-1line": block([r("Выключаем ", ("ручной режим", B))], 96, 800, 1, DISPLAY_LS),
    "slogan-manual-to-system-stacked": block([r("Из ручных"), r("процессов —"), r(("в систему", B))], 140, 800, 1.02, DISPLAY_LS),
    "slogan-manual-to-system-1line": block([r("Из ручных процессов — ", ("в систему", B))], 96, 800, 1, DISPLAY_LS),
    "descriptor-automation-2lines": block([r("АВТОМАТИЗАЦИЯ"), r("БИЗНЕС-ПРОЦЕССОВ")], 56, 600, 1.21, 0),
    "descriptor-automation-1line": block([r("АВТОМАТИЗАЦИЯ БИЗНЕС-ПРОЦЕССОВ")], 56, 600, 1, 0),
    "descriptor-automate-2lines": block([r("АВТОМАТИЗИРУЮ"), r("БИЗНЕС-ПРОЦЕССЫ")], 56, 600, 1.21, 0),
    "descriptor-automate-1line": block([r("АВТОМАТИЗИРУЮ БИЗНЕС-ПРОЦЕССЫ")], 56, 600, 1, 0),
    "word-ai": block([r("AI")], 300, 800, 1, -0.02),
    "word-system": block([r("SYSTEM")], 220, 800, 1, -0.02),
    "word-process": block([r("PROCESS")], 220, 800, 1, -0.02),
    "word-automation": block([r("AUTOMATION")], 220, 800, 1, -0.02),
    "word-digital": block([r("DIGITAL")], 220, 800, 1, -0.02),
    "word-system-tracked": block([r("SYSTEM")], 90, 600, 1, 0.4),
    "word-process-tracked": block([r("PROCESS")], 90, 600, 1, 0.4),
    "word-automation-tracked": block([r("AUTOMATION")], 90, 600, 1, 0.4),
    "numbers-01-02-03": block([r("01", (" / ", "MUTED"), "02", (" / ", "MUTED"), "03")], 200, 800, 1, -0.02),
    "number-01": block([r("01")], 300, 800, 1, -0.03),
    "number-02": block([r("02")], 300, 800, 1, -0.03),
    "number-03": block([r("03")], 300, 800, 1, -0.03),
}


def word_with_module(word, size=220):
    """Слово + синий малый модуль вместо точки — фирменная «точка системы»."""
    base = block([r(word)], size, 800, 1, -0.02)

    def draw(fg, outline):
        w, h, body = base(fg, outline)
        s = size * 0.2
        x = w + size * 0.06
        y = size * 0.12 + cap(size) - s
        return math.ceil(x + s + 2), h, body + rect(x, y, s, s, s * 0.24, B)
    return draw


for _w in ("AI", "SYSTEM", "PROCESS", "AUTOMATION", "DIGITAL"):
    COMPS[f"word-{_w.lower()}-dot"] = word_with_module(_w, 300 if _w == "AI" else 220)


def build():
    for name, fn in COMPS.items():
        for tone, fg, mut in (("on-light", G, C["offwhite_line"]), ("on-dark", W, C["graphite_line"])):
            for outline, folder in ((False, "SVG_editable-text"), (True, "SVG_outlined")):
                w, h, body = fn(fg, outline)
                body = body.replace('"MUTED"', f'"{mut}"')
                save(f"05_TYPOGRAPHY/{folder}/type-{name}-{tone}.svg", w, h, body, "Типографика",
                     pngs=[(f"05_TYPOGRAPHY/PNG/type-{name}-{tone}.png", min(w * 2, 3000))] if outline else None)
    return len(COMPS)
