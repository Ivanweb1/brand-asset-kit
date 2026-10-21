"""Рендер SVG → PNG через Chromium (Playwright) с прозрачным фоном и настоящим Manrope."""
import base64
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

SRC = Path(__file__).resolve().parent
FONT = base64.b64encode((SRC / "fonts" / "Manrope-Variable.ttf").read_bytes()).decode()
BASE = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:'Manrope';src:url(data:font/ttf;base64,{FONT}) format('truetype');font-weight:200 800;}}
html,body{{margin:0;padding:0;background:transparent;}}
#c{{position:absolute;left:0;top:0;line-height:0;}} #c svg{{display:block;}}
</style></head><body><div id="c"></div>
<div style="font-family:Manrope;position:absolute;left:-9999px"><b>Ая</b><span style="font-weight:800">Ая</span></div>
</body></html>"""


def _sized(svg, w, h):
    svg = re.sub(r"^<\?xml[^>]*>\s*", "", svg)
    return re.sub(r'<svg([^>]*?) width="[^"]+" height="[^"]+"', rf'<svg\1 width="{w}" height="{h}"', svg, count=1)


def render(jobs, log=print):
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(device_scale_factor=1)
        page.set_content(BASE)
        page.evaluate("document.fonts.ready")
        cache = {}
        for i, (svg_path, png_path, w, h) in enumerate(jobs):
            if svg_path not in cache:
                cache[svg_path] = svg_path.read_text(encoding="utf-8")
            page.set_viewport_size({"width": w, "height": h})
            page.evaluate("s => { document.getElementById('c').innerHTML = s; return document.fonts.ready.then(()=>1); }",
                          _sized(cache[svg_path], w, h))
            png_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(png_path), clip={"x": 0, "y": 0, "width": w, "height": h}, omit_background=True)
            if i % 100 == 0:
                log(f"  png {i}/{len(jobs)}")
        b.close()
