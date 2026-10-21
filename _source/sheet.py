"""Контакт-листы: раскладывает SVG секции на одном листе (векторно), затем рендер в PNG."""
import re

from kit import save, text, C

_inner = re.compile(r"^.*?<svg[^>]*>", re.S)


def contact_sheet(rel_out, svgs, width=2400, cell=None, gap=24, bg="#8A8D91", title=None, max_item_h=None, label=True):
    """svgs: список Path. cell=(w,h) — сетка с вписыванием; иначе — ряды по натуральному размеру."""
    parts, x, y, rowh = [], gap, gap, 0
    if title:
        parts.append(text(gap, gap + 40, title, 44, 800, C["offwhite"]))
        y += 80
    for p in svgs:
        src = p.read_text(encoding="utf-8")
        m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', src)
        w, h = float(m.group(1)), float(m.group(2))
        inner = _inner.sub("", src, count=1).replace("</svg>", "")
        inner = re.sub(r"<title>.*?</title>", "", inner)
        if cell:
            cw, ch = cell
            k = min((cw - 24) / w, (ch - 56) / h)
            dw, dh = w * k, h * k
            if x + cw > width:
                x, y = gap, y + ch + gap
            ox, oy = x + (cw - dw) / 2, y + (ch - 40 - dh) / 2
            parts.append(f'<rect x="{x}" y="{y}" width="{cw}" height="{ch}" rx="14" fill="#000" fill-opacity="0.08"/>')
            parts.append(f'<svg x="{ox:.1f}" y="{oy:.1f}" width="{dw:.1f}" height="{dh:.1f}" viewBox="0 0 {w:g} {h:g}">{inner}</svg>')
            if label:
                parts.append(text(x + 12, y + ch - 14, p.stem[:44], 15, 500, C["offwhite"], opacity=0.85))
            x += cw + gap
            rowh = ch
        else:
            k = min(1, (max_item_h or h) / h)
            dw, dh = w * k, h * k
            if x + dw > width - gap:
                x, y, rowh = gap, y + rowh + gap, 0
            parts.append(f'<svg x="{x:.1f}" y="{y:.1f}" width="{dw:.1f}" height="{dh:.1f}" viewBox="0 0 {w:g} {h:g}">{inner}</svg>')
            x += dw + gap
            rowh = max(rowh, dh)
    H = y + rowh + gap
    return save("_source/_cache/" + rel_out.split("/")[-1].replace(".png", ".svg"), width, round(H), "".join(parts), bg=bg,
                pngs=[(rel_out, width)], section="10_PREVIEWS")
