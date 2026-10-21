"""Ядро генератора: токены, логотип из оригинального SVG, текст (редактируемый и в кривых), запись файлов."""
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

SRC = Path(__file__).resolve().parent
KIT = SRC.parent
T = json.loads((SRC / "tokens.json").read_text(encoding="utf-8"))
C = T["color"]
FAMILY = T["font"]["family"]
WEIGHTS = {400: "Regular", 500: "Medium", 600: "SemiBold", 700: "Bold", 800: "ExtraBold"}

# ---------------------------------------------------------------- логотип
_orig = (SRC / "logo-mark.original.svg").read_text(encoding="utf-8")
LOGO_PATHS = re.findall(r'<path d="([^"]+)"', _orig)
LOGO_DOTS = [tuple(float(v) for v in m) for m in
             re.findall(r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)" rx="([\d.]+)"(?! fill)', _orig)]
_blue = re.search(r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)" rx="([\d.]+)" fill="#1769FF"', _orig)
LOGO_ACCENT = tuple(float(v) for v in _blue.groups())
LOGO_GRID = 390.0
assert len(LOGO_PATHS) == 3 and len(LOGO_DOTS) == 4, "оригинальный знак не распознан"


def logo(x, y, size, main=None, accent=None, opacity=None, gid=None):
    """Знак строго по оригинальной геометрии, масштаб size (сторона квадрата)."""
    main = main or C["graphite"]
    accent = accent or C["blue"]
    s = size / LOGO_GRID
    op = f' opacity="{opacity}"' if opacity is not None else ""
    idattr = f' id="{gid}"' if gid else ""
    paths = "".join(f'<path d="{d}"/>' for d in LOGO_PATHS)
    dots = "".join(f'<rect x="{r[0]:g}" y="{r[1]:g}" width="{r[2]:g}" height="{r[3]:g}" rx="{r[4]:g}"/>' for r in LOGO_DOTS)
    a = LOGO_ACCENT
    return (f'<g{idattr} transform="translate({x:g} {y:g}) scale({s:.6g})"{op}>'
            f'<g fill="{main}" fill-rule="evenodd">{paths}</g>'
            f'<g fill="{main}">{dots}</g>'
            f'<rect x="{a[0]:g}" y="{a[1]:g}" width="{a[2]:g}" height="{a[3]:g}" rx="{a[4]:g}" fill="{accent}"/></g>')


# ---------------------------------------------------------------- шрифт
class Face:
    def __init__(self, weight):
        path = SRC / "fonts" / f"Manrope-{WEIGHTS[weight]}.ttf"
        blob = hb.Blob.from_file_path(str(path))
        self.hbfont = hb.Font(hb.Face(blob))
        self.tt = TTFont(str(path))
        self.upem = self.tt["head"].unitsPerEm
        self.gs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()

    def shape(self, s):
        buf = hb.Buffer()
        buf.add_str(s)
        buf.guess_segment_properties()
        hb.shape(self.hbfont, buf, {"kern": True, "liga": True})
        return buf.glyph_infos, buf.glyph_positions


_faces = {}


def face(w):
    if w not in _faces:
        _faces[w] = Face(w)
    return _faces[w]


def measure(s, size, weight=400, ls=0.0):
    """Ширина строки в px; ls — трекинг в em (как CSS letter-spacing)."""
    if not s:
        return 0.0
    f = face(weight)
    _, pos = f.shape(s)
    adv = sum(p.x_advance for p in pos) * size / f.upem
    return adv + ls * size * len(s)


def _norm_spans(spans, fill):
    if isinstance(spans, str):
        return [(spans, fill)]
    return [(t, f or fill) for t, f in spans]


def text(x, y, spans, size, weight=400, fill=None, anchor="start", ls=0.0, outline=False, opacity=None, tid=None):
    """Одна строка. spans — строка или [(текст, цвет)]. outline=True — текст в кривых."""
    fill = fill or C["graphite"]
    spans = _norm_spans(spans, fill)
    full = "".join(t for t, _ in spans)
    w = measure(full, size, weight, ls)
    # трекинг добавляется и после последней буквы — компенсируем при выключке
    trail = ls * size
    if anchor == "middle":
        x0 = x - (w - trail) / 2
    elif anchor == "end":
        x0 = x - (w - trail)
    else:
        x0 = x
    op = f' opacity="{opacity}"' if opacity is not None else ""
    idattr = f' id="{tid}"' if tid else ""
    if not outline:
        lsattr = f' letter-spacing="{ls * size:.2f}"' if ls else ""
        if len(spans) == 1:
            return (f'<text{idattr} x="{x0:.2f}" y="{y:.2f}" font-family="{FAMILY}" font-size="{size:g}" '
                    f'font-weight="{weight}" fill="{spans[0][1]}"{lsattr}{op}>{escape(full)}</text>')
        inner = "".join(f'<tspan fill="{f}">{escape(t)}</tspan>' for t, f in spans)
        return (f'<text{idattr} x="{x0:.2f}" y="{y:.2f}" font-family="{FAMILY}" font-size="{size:g}" '
                f'font-weight="{weight}"{lsattr}{op}>{inner}</text>')
    f = face(weight)
    sc = size / f.upem
    cx = x0
    out = []
    for t, col in spans:
        infos, pos = f.shape(t)
        pen = SVGPathPen(f.gs)
        for info, p in zip(infos, pos):
            gname = f.order[info.codepoint]
            tp = TransformPen(pen, (sc, 0, 0, -sc, cx + p.x_offset * sc, y - p.y_offset * sc))
            f.gs[gname].draw(tp)
            cx += p.x_advance * sc + ls * size
        d = pen.getCommands()
        if d:
            out.append(f'<path d="{d}" fill="{col}"/>')
    label = escape(full).replace('"', "&quot;")
    return f'<g{idattr} data-text="{label}"{op}>' + "".join(out) + "</g>"


def rich(x, y, parts, size, weight=800, fill=None, ls=-0.03, chip=None, chip_fg=None):
    """Строка с фирменным выделением. parts: [(текст, режим)], режим None | 'blue' | 'chip'.
    'chip' — слово на синей плашке: главный приём бренда для ключевого слова."""
    fill = fill or C["graphite"]
    chip = chip or C["blue"]
    chip_fg = chip_fg or C["offwhite"]
    px, out, cx = size * 0.16, "", x
    for t, mode in parts:
        if mode == "chip":
            cx += px  # плашка начинается ровно по колонке текста или с отступом от предыдущего слова
            w = measure(t, size, weight, ls) - ls * size
            out += rect(cx - px, y - cap(size) - size * 0.13, w + 2 * px, cap(size) + size * 0.37, size * 0.2, chip)
            out += text(cx, y, t, size, weight, chip_fg, ls=ls)
            cx += w + px * 2
        else:
            out += text(cx, y, t, size, weight, C["blue"] if mode == "blue" else fill, ls=ls)
            cx += measure(t, size, weight, ls)
    return out


def rich_width(parts, size, weight=800, ls=-0.03):
    px, w = size * 0.16, 0
    for t, mode in parts:
        w += measure(t, size, weight, ls) + (px * 3 if mode == "chip" else 0)
    return w


def lines(x, y, rows, size, weight=400, fill=None, lh=1.2, **kw):
    """Несколько строк с межстрочным lh. rows — список строк/spans."""
    return "".join(text(x, y + i * size * lh, r, size, weight, fill, **kw) for i, r in enumerate(rows))


def cap(size):
    """Высота прописной Manrope ≈ 0.72 кегля — для вертикальной центровки."""
    return size * 0.72


# ---------------------------------------------------------------- примитивы
def rect(x, y, w, h, r=0, fill="none", stroke=None, sw=0, extra=""):
    st = f' stroke="{stroke}" stroke-width="{sw:g}"' if stroke else ""
    return f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{r:g}" fill="{fill}"{st}{extra}/>'


def line(x1, y1, x2, y2, stroke, sw, cap_="round", dash=None, extra=""):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1:g}" y1="{y1:g}" x2="{x2:g}" y2="{y2:g}" stroke="{stroke}" stroke-width="{sw:g}" '
            f'stroke-linecap="{cap_}"{da}{extra}/>')


def path(d, stroke=None, sw=0, fill="none", extra=""):
    st = f' stroke="{stroke}" stroke-width="{sw:g}" stroke-linecap="round" stroke-linejoin="round"' if stroke else ""
    return f'<path d="{d}" fill="{fill}"{st}{extra}/>'


def heavy_frame(x, y, s, fill):
    """Контурный модуль в пропорциях знака: обводка 38/180, радиусы 42/16."""
    k = s / 180
    o, i, sw = 42 * k, 16 * k, 38 * k
    a, b = x + sw, y + sw
    c = s - 2 * sw
    d = (f"M{x + o:.2f} {y:.2f}H{x + s - o:.2f}A{o:.2f} {o:.2f} 0 0 1 {x + s:.2f} {y + o:.2f}V{y + s - o:.2f}"
         f"A{o:.2f} {o:.2f} 0 0 1 {x + s - o:.2f} {y + s:.2f}H{x + o:.2f}A{o:.2f} {o:.2f} 0 0 1 {x:.2f} {y + s - o:.2f}"
         f"V{y + o:.2f}A{o:.2f} {o:.2f} 0 0 1 {x + o:.2f} {y:.2f}Z"
         f"M{a + i:.2f} {b:.2f}A{i:.2f} {i:.2f} 0 0 0 {a:.2f} {b + i:.2f}V{b + c - i:.2f}A{i:.2f} {i:.2f} 0 0 0 {a + i:.2f} {b + c:.2f}"
         f"H{a + c - i:.2f}A{i:.2f} {i:.2f} 0 0 0 {a + c:.2f} {b + c - i:.2f}V{b + i:.2f}A{i:.2f} {i:.2f} 0 0 0 {a + c - i:.2f} {b:.2f}Z")
    return f'<path d="{d}" fill="{fill}" fill-rule="evenodd"/>'


def dot(x, y, s, fill):
    """Малый модуль в пропорциях знака: скругление 12/50."""
    return rect(x, y, s, s, s * 0.24, fill)


# ---------------------------------------------------------------- файлы
JOBS = []  # (svg_path, png_path, width, height)
STATS = {}


def svg_doc(w, h, body, title="", bg=None):
    bgr = f'<rect width="{w:g}" height="{h:g}" fill="{bg}"/>' if bg else ""
    t = f"<title>{escape(title)}</title>" if title else ""
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:g}" height="{h:g}" viewBox="0 0 {w:g} {h:g}">'
            f'{t}{bgr}{body}</svg>\n')


def save(rel_svg, w, h, body, title="", bg=None, pngs=None, section=None):
    """Пишет SVG и ставит PNG в очередь рендера. pngs — список (rel_png, ширина_px)."""
    p = KIT / rel_svg
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(svg_doc(w, h, body, title, bg), encoding="utf-8")
    for rel_png, pw in pngs or []:
        ph = round(h * pw / w)
        JOBS.append((p, KIT / rel_png, pw, ph))
    sec = section or rel_svg.split("/")[0]
    STATS[sec] = STATS.get(sec, 0) + 1
    return p
