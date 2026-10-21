"""07_BACKGROUNDS — фирменные фоны, параметрические под 4 формата."""
from kit import C, rect, heavy_frame, dot, line, path, save

G, W, B = C["graphite"], C["offwhite"], C["blue"]
SIZES = [(1080, 1920), (1080, 1350), (1080, 1080), (1920, 1080)]


def pattern_modular(w, h, bg, ln):
    t = 260
    tile = (f'<pattern id="pm-{bg[1:]}" width="{t}" height="{t}" patternUnits="userSpaceOnUse">'
            f'<rect x="20" y="20" width="110" height="110" rx="26" fill="none" stroke="{ln}" stroke-width="3"/>'
            f'{dot(162, 162, 22, ln)}{dot(206, 162, 22, ln)}{dot(162, 206, 22, ln)}</pattern>')
    return f"<defs>{tile}</defs>" + rect(0, 0, w, h, 0, bg) + f'<rect width="{w}" height="{h}" fill="url(#pm-{bg[1:]})"/>'


def dots(w, h, bg, ln, pitch=36, s=5):
    tile = (f'<pattern id="pd-{bg[1:]}" width="{pitch}" height="{pitch}" patternUnits="userSpaceOnUse">'
            f'<rect x="{(pitch - s) / 2}" y="{(pitch - s) / 2}" width="{s}" height="{s}" rx="1.2" fill="{ln}"/></pattern>')
    return f"<defs>{tile}</defs>" + rect(0, 0, w, h, 0, bg) + f'<rect width="{w}" height="{h}" fill="url(#pd-{bg[1:]})"/>'


def tech_grid(w, h):
    c = 54
    out = rect(0, 0, w, h, 0, G)
    for x in range(0, w + 1, c):
        out += line(x, 0, x, h, C["graphite_surface"] if x % (c * 4) else C["graphite_line"], 1.5, "butt")
    for y in range(0, h + 1, c):
        out += line(0, y, w, y, C["graphite_surface"] if y % (c * 4) else C["graphite_line"], 1.5, "butt")
    gx, gy = (w // (c * 4)) * c * 4 - c * 4, (h // c - 10) * c
    return out + rect(gx + 2, gy + 2, c - 4, c - 4, 12, B)


def composition(w, h):
    m = min(w, h)
    s = m * 0.42
    out = rect(0, 0, w, h, 0, G)
    x0, y0 = w - s * 1.75, h - s * 1.75
    out += heavy_frame(x0, y0, s, C["graphite_surface"]) + heavy_frame(x0 + s * 1.1667, y0, s, C["graphite_surface"])
    out += heavy_frame(x0, y0 + s * 1.1667, s, C["graphite_surface"])
    d = s * 50 / 180
    p = s * 65 / 180
    bx, by = x0 + s * 1.1667, y0 + s * 1.1667
    out += dot(bx, by, d, B) + dot(bx + p, by + p, d, C["graphite_surface"]) + dot(bx + 2 * p, by, d, C["graphite_surface"])
    return out


def accent_blue(w, h):
    m = min(w, h)
    s = m * 0.18
    out = rect(0, 0, w, h, 0, G)
    x, y = w - s - m * 0.09, h - s - m * 0.09
    out += line(m * 0.09, y + s / 2, x - 30, y + s / 2, C["graphite_line"], 3, "butt")
    out += rect(m * 0.09 - 9, y + s / 2 - 9, 18, 18, 5, C["graphite_line"])
    return out + rect(x, y, s, s, s * 0.233, B)


def geo_lines(w, h):
    out = rect(0, 0, w, h, 0, G)
    ln = C["graphite_line"]
    m = min(w, h)
    for i, (fx, fy, tx, ty) in enumerate(((0.0, 0.22, 0.72, 0.62), (0.0, 0.42, 0.52, 0.9), (0.3, 0.0, 1.0, 0.36))):
        x1, y1, x2, y2 = fx * w, fy * h, tx * w, ty * h
        r = m * 0.06
        out += path(f"M{x1:g} {y1:g}H{x2 - r:g}A{r:g} {r:g} 0 0 1 {x2:g} {y1 + r:g}V{y2:g}", ln, 3)
        out += rect(x2 - 11, y2 - 11, 22, 22, 6, B if i == 0 else ln)
    return out


def outlines_light(w, h):
    m = min(w, h)
    s = m * 0.42
    out = rect(0, 0, w, h, 0, W)
    o = s * 0.28
    x, y = w - s - 2 * o - m * 0.08, h * 0.16
    for i in range(3):
        out += rect(x + i * o, y + i * o, s, s, s * 0.233, "none", C["offwhite_line"], 4)
    q = s * 0.16
    return out + rect(x + 2 * o + s - q - s * 0.1, y + 2 * o + s * 0.1, q, q, q * 0.24, B)


def giant_mark(w, h, bg=G, col=None):
    """Модули знака в масштабе кадра, уходят за край — фирменный «крупный план»."""
    col = col or C["graphite_surface"]
    m = min(w, h)
    s = m * 0.78
    x0, y0 = w - s * 1.45, h - s * 1.5
    out = rect(0, 0, w, h, 0, bg) + heavy_frame(x0, y0, s, col) + heavy_frame(x0 + s * 1.1667, y0, s, col) + heavy_frame(x0, y0 + s * 1.1667, s, col)
    d, p = s * 50 / 180, s * 65 / 180
    bx, by = x0 + s * 1.1667, y0 + s * 1.1667
    out += dot(bx, by, d, B) + dot(bx + 2 * p, by, d, col) + dot(bx + p, by + p, d, col)
    return out


def blue_block(w, h):
    m = min(w, h)
    r = m * 0.07
    bh = h * 0.34
    return rect(0, 0, w, h, 0, G) + rect(m * 0.05, h - bh, w - m * 0.1, bh + r, r, B)


BGS = {
    "solid-graphite": lambda w, h: rect(0, 0, w, h, 0, G),
    "solid-offwhite": lambda w, h: rect(0, 0, w, h, 0, W),
    "solid-blue": lambda w, h: rect(0, 0, w, h, 0, B),
    "pattern-modular-dark": lambda w, h: pattern_modular(w, h, G, C["graphite_surface"]),
    "pattern-modular-light": lambda w, h: pattern_modular(w, h, W, C["offwhite_surface"]),
    "composition-squares-dark": composition,
    "grid-technical-dark": tech_grid,
    "accent-blue-dark": accent_blue,
    "lines-geometric-dark": geo_lines,
    "outlines-composition-light": outlines_light,
    "pattern-dots-subtle-light": lambda w, h: dots(w, h, W, C["offwhite_line"]),
    "pattern-dots-subtle-dark": lambda w, h: dots(w, h, G, C["graphite_line"]),
    "giant-modules-dark": giant_mark,
    "giant-modules-light": lambda w, h: giant_mark(w, h, W, C["offwhite_surface"]),
    "blue-block-dark": blue_block,
}


def build():
    for name, fn in BGS.items():
        for w, h in SIZES:
            save(f"07_BACKGROUNDS/SVG/bg-{name}-{w}x{h}.svg", w, h, fn(w, h), "Фон",
                 pngs=[(f"07_BACKGROUNDS/PNG/bg-{name}-{w}x{h}.png", w)])
    return len(BGS)
