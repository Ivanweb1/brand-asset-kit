"""01_LOGO — знак, локапы, подложки, аватарки, водяные знаки. Текст в логотипах всегда в кривых."""
from kit import C, logo, text, rect, save

G, W, B = C["graphite"], C["offwhite"], C["blue"]
FULL = [256, 512, 1024, 2048]
DESC = ["АВТОМАТИЗАЦИЯ", "БИЗНЕС-ПРОЦЕССОВ"]


def pngs(name, sizes=FULL):
    return [(f"01_LOGO/PNG/{name}-{s}.png", s) for s in sizes]


def mark(name, main, accent, title, sizes=FULL, opacity=None):
    save(f"01_LOGO/SVG/{name}.svg", 390, 390, logo(0, 0, 390, main, accent, opacity), title, pngs=pngs(name, sizes))


def descriptor(x, y, size, fill):
    return (text(x, y, DESC[0], size, 500, fill, ls=0.28, outline=True)
            + text(x, y + size * 1.55, DESC[1], size, 500, fill, ls=0.28, outline=True))


def lockup_h(fill, main, accent):
    # знак 390; дескриптор центрирован по высоте знака
    s = 46
    block = s * 0.72 + s * 1.55
    y0 = (390 - block) / 2 + s * 0.72
    from kit import measure
    w = 390 + 96 + measure(DESC[1], s, 500, 0.28) - 0.28 * s
    return w, logo(0, 0, 390, main, accent) + descriptor(390 + 96, y0, s, fill)


def lockup_v(fill, main, accent):
    s = 30
    from kit import measure
    tw = measure(DESC[1], s, 500, 0.28) - 0.28 * s
    w = max(390, tw)
    h = 390 + 70 + s * 0.72 + s * 1.55 + s * 0.24
    return w, h, logo(0, 0, 390, main, accent) + descriptor(0, 390 + 70 + s * 0.72, s, fill)


def plate(shape, bg, main, accent):
    k = 1000
    if shape == "square":
        base = rect(0, 0, k, k, k * 0.2333, bg)
        m = 560
    elif shape == "circle":
        base = f'<circle cx="{k / 2}" cy="{k / 2}" r="{k / 2}" fill="{bg}"/>'
        m = 480
    else:  # upload: квадрат без скругления, соцсети сами обрежут в круг
        base = rect(0, 0, k, k, 0, bg)
        m = 460
    return base + logo((k - m) / 2, (k - m) / 2, m, main, accent)


def build():
    mark("logo-mark-primary", G, B, "Знак — основной, для светлого фона")
    mark("logo-mark-inverse", W, B, "Знак — инверсный, для тёмного фона")
    mark("logo-mark-mono-white", W, W, "Знак — одноцветный светлый")
    mark("logo-mark-mono-graphite", G, G, "Знак — одноцветный графитовый")

    for tone, fill, main in (("light-bg", G, G), ("dark-bg", W, W)):
        w, body = lockup_h(fill, main, B)
        save(f"01_LOGO/SVG/logo-lockup-horizontal-{tone}.svg", round(w), 390, body, "Логотип с дескриптором, горизонтальный",
             pngs=[(f"01_LOGO/PNG/logo-lockup-horizontal-{tone}-{s}.png", s) for s in (1024, 2048)])
        w, h, body = lockup_v(fill, main, B)
        save(f"01_LOGO/SVG/logo-lockup-vertical-{tone}.svg", round(w), round(h), body, "Логотип с дескриптором, вертикальный",
             pngs=[(f"01_LOGO/PNG/logo-lockup-vertical-{tone}-{s}.png", s) for s in (1024, 2048)])

    for shape in ("square", "circle", "upload"):
        for tone, bg, main in (("light", W, G), ("dark", G, W), ("blue", B, W)):
            if tone == "blue":
                if shape != "square":
                    continue
                # на синей подложке синий модуль растворился бы — используем утверждённый одноцветный светлый знак
                body = plate(shape, bg, W, W)
            else:
                body = plate(shape, bg, main, B)
            name = {"square": "logo-app-icon", "circle": "logo-avatar-circle", "upload": "logo-avatar-upload"}[shape]
            save(f"01_LOGO/SVG/{name}-{tone}.svg", 1000, 1000, body, "Знак на подложке",
                 pngs=[(f"01_LOGO/PNG/{name}-{tone}-{s}.png", s) for s in (256, 512, 1024)])

    # водяные знаки: компактные, полупрозрачность уже «запечена»
    mark("watermark-mark-white-70", W, W, "Водяной знак, светлый 70%", sizes=[128, 256, 512], opacity=0.7)
    mark("watermark-mark-graphite-60", G, G, "Водяной знак, графитовый 60%", sizes=[128, 256, 512], opacity=0.6)
    w, body = lockup_h(W, W, B)
    save("01_LOGO/SVG/watermark-lockup-white-70.svg", round(w), 390, f'<g opacity="0.7">{body}</g>', "Водяной знак с дескриптором",
         pngs=[("01_LOGO/PNG/watermark-lockup-white-70-512.png", 512), ("01_LOGO/PNG/watermark-lockup-white-70-1024.png", 1024)])
