"""10_PREVIEWS (контакт-листы, каталог) и 00_BRAND_GUIDE (руководство HTML + PDF)."""
import html
import json
import shutil
from pathlib import Path

from kit import KIT, SRC, C, T
from sheet import contact_sheet

G, W, B = C["graphite"], C["offwhite"], C["blue"]


def _g(pattern):
    return sorted(KIT.glob(pattern))


def sheets():
    S = [
        ("sheet-01-logo.png", _g("01_LOGO/SVG/*.svg"), dict(cell=(360, 300), bg="#8A8D91")),
        ("sheet-02-elements-on-dark.png", _g("02_GRAPHIC_ELEMENTS/SVG/*-on-dark.svg") + _g("02_GRAPHIC_ELEMENTS/SVG/*-any-bg.svg"), dict(cell=(320, 260), bg=G)),
        ("sheet-02-elements-on-light.png", _g("02_GRAPHIC_ELEMENTS/SVG/*-on-light.svg"), dict(cell=(320, 260), bg=W)),
        ("sheet-03-icons-light.png", _g("03_ICONS/SVG/*-on-light-accent.svg") + _g("03_ICONS/SVG/*-tile-light.svg"), dict(cell=(180, 170), bg=W)),
        ("sheet-03-icons-dark.png", _g("03_ICONS/SVG/*-on-dark-accent.svg") + _g("03_ICONS/SVG/*-tile-dark.svg"), dict(cell=(180, 170), bg=G)),
        ("sheet-04-labels.png", [p for p in _g("04_LABELS/SVG/*.svg") if "empty" not in p.name], dict(cell=(460, 300), bg="#8A8D91")),
        ("sheet-04-labels-empty.png", _g("04_LABELS/SVG/*-empty.svg"), dict(cell=(460, 300), bg="#8A8D91")),
        ("sheet-05-typography-dark.png", _g("05_TYPOGRAPHY/SVG_outlined/*-on-dark.svg"), dict(cell=(460, 280), bg=G)),
        ("sheet-05-typography-light.png", _g("05_TYPOGRAPHY/SVG_outlined/*-on-light.svg"), dict(cell=(460, 280), bg=W)),
        ("sheet-06-overlays.png", _g("06_VIDEO_OVERLAYS/SVG/*.svg"), dict(cell=(380, 700), bg="#5A5D60")),
        ("sheet-07-backgrounds.png", [p for p in _g("07_BACKGROUNDS/SVG/*.svg")], dict(cell=(300, 400), bg="#8A8D91")),
        ("sheet-08-posts.png", _g("08_SOCIAL_TEMPLATES/SVG/*-post-1080x1350.svg"), dict(cell=(460, 620), bg="#8A8D91")),
        ("sheet-08-stories.png", _g("08_SOCIAL_TEMPLATES/SVG/*-story-1080x1920.svg"), dict(cell=(380, 700), bg="#8A8D91")),
        ("sheet-08-carousels.png", _g("08_SOCIAL_TEMPLATES/SVG/carousel-*/*-1080x1350.svg"), dict(cell=(330, 450), bg="#8A8D91")),
        ("sheet-09-extras-on-dark.png", [p for p in _g("09_EXTRA_ELEMENTS/SVG/x-*.svg") if "on-light" not in p.name and "animated" not in p.name], dict(cell=(320, 240), bg=G)),
        ("sheet-09-extras-on-light.png", _g("09_EXTRA_ELEMENTS/SVG/x-*-on-light.svg"), dict(cell=(320, 240), bg=W)),
    ]
    for name, svgs, kw in S:
        contact_sheet(f"10_PREVIEWS/{name}", svgs, width=2400, **kw)


SECTIONS = [
    ("01_LOGO", "Логотип", "01_LOGO/PNG/*-1024.png"),
    ("02_GRAPHIC_ELEMENTS", "Графические элементы", "02_GRAPHIC_ELEMENTS/PNG/*.png"),
    ("03_ICONS", "Иконки", "03_ICONS/PNG/256/*.png"),
    ("04_LABELS", "Плашки", "04_LABELS/PNG/1x/*.png"),
    ("05_TYPOGRAPHY", "Типографика", "05_TYPOGRAPHY/PNG/*.png"),
    ("06_VIDEO_OVERLAYS", "Оверлеи Reels / Shorts", "06_VIDEO_OVERLAYS/PNG/*.png"),
    ("07_BACKGROUNDS", "Фоны", "07_BACKGROUNDS/PNG/*.png"),
    ("08_SOCIAL_TEMPLATES", "Шаблоны соцсетей", "08_SOCIAL_TEMPLATES/PNG/**/*.png"),
    ("09_EXTRA_ELEMENTS", "Дополнительные элементы", "09_EXTRA_ELEMENTS/PNG/*.*"),
]


def _svg_for(png: Path):
    rel = png.relative_to(KIT)
    parts = list(rel.parts)
    name = png.stem.replace("@2x", "")
    sec = parts[0]
    cands = list((KIT / sec).rglob(name + ".svg"))
    if not cands and sec == "01_LOGO":
        cands = list((KIT / sec).rglob(name.rsplit("-", 1)[0] + ".svg"))
    if sec == "05_TYPOGRAPHY":
        cands = list((KIT / sec / "SVG_editable-text").glob(name + ".svg"))
    return cands[0].relative_to(KIT).as_posix() if cands else None


def build_catalog(counts, report):
    cards, nav = [], []
    totals = {}
    for sec, title, pat in SECTIONS:
        files = sorted(p for p in KIT.glob(pat) if p.suffix in (".png", ".gif"))
        totals[sec] = len(files)
        nav.append(f'<a href="#{sec}">{html.escape(title)}<span>{len(files)}</span></a>')
        items = []
        for p in files:
            rel = p.relative_to(KIT).as_posix()
            svg = _svg_for(p) if p.suffix == ".png" else None
            dark = any(k in p.name for k in ("on-dark", "dark-bg", "inverse", "mono-white", "white-70", "-dark-", "tile-dark")) and "light" not in p.name.split("on-")[-1][:5]
            links = f'<a href="../{rel}">PNG</a>' + (f' · <a href="../{svg}">SVG</a>' if svg else "")
            items.append(f'<figure class="{"d" if dark else "l"}" data-name="{html.escape(p.stem)}"><div class="im"><img loading="lazy" src="../{rel}" alt=""></div>'
                         f'<figcaption><b>{html.escape(p.stem)}</b><small>{links}</small></figcaption></figure>')
        cards.append(f'<section id="{sec}"><h2>{html.escape(title)} <em>{len(files)}</em></h2><div class="grid">{"".join(items)}</div></section>')
    sheets_ = "".join(f'<a href="{p.name}"><img loading="lazy" src="{p.name}" alt=""><span>{p.stem}</span></a>' for p in _g("10_PREVIEWS/sheet-*.png"))
    page = CATALOG_HTML.replace("%NAV%", "".join(nav)).replace("%CARDS%", "".join(cards)).replace("%SHEETS%", sheets_)
    page = page.replace("%SVG%", str(report["svg"])).replace("%PNG%", str(report["png"])).replace("%ERR%", str(len(report["errors"])))
    (KIT / "10_PREVIEWS" / "catalog.html").write_text(page, encoding="utf-8")
    (SRC / "_cache").mkdir(exist_ok=True)
    (SRC / "_cache" / "totals.json").write_text(json.dumps(totals, ensure_ascii=False), encoding="utf-8")


CATALOG_HTML = """<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Brand Asset Kit — каталог</title>
<style>
@font-face{font-family:Manrope;src:url(../00_BRAND_GUIDE/fonts/Manrope-Variable.ttf);font-weight:200 800}
:root{--g:#111315;--w:#F5F4F0;--b:#1769FF;--s:#1B1E21;--l:#2C3035;--m:#9A9EA4}
*{box-sizing:border-box}body{margin:0;background:var(--g);color:var(--w);font-family:Manrope,system-ui,sans-serif}
header{padding:48px 40px 24px;display:flex;gap:28px;align-items:center;flex-wrap:wrap}
header img{width:64px;height:64px}header h1{margin:0;font-size:40px;font-weight:800;letter-spacing:-.02em}
header p{margin:4px 0 0;color:var(--m);font-size:15px}
nav{position:sticky;top:0;z-index:5;background:rgba(17,19,21,.92);backdrop-filter:blur(8px);padding:14px 40px;display:flex;gap:8px;flex-wrap:wrap;border-bottom:1px solid var(--l)}
nav a{color:var(--w);text-decoration:none;font-weight:600;font-size:14px;padding:8px 12px;border-radius:10px;background:var(--s)}
nav a span{color:var(--b);margin-left:6px}nav a:hover{background:var(--l)}
.tools{margin-left:auto;display:flex;gap:6px;align-items:center}
.tools button{font:600 13px Manrope;border:1px solid var(--l);background:transparent;color:var(--w);padding:7px 11px;border-radius:9px;cursor:pointer}
.tools button.on{background:var(--b);border-color:var(--b)}
.tools input{font:500 14px Manrope;background:var(--s);border:1px solid var(--l);color:var(--w);border-radius:9px;padding:8px 12px;width:180px}
section{padding:32px 40px}h2{font-size:28px;font-weight:800;margin:0 0 20px}h2 em{font-style:normal;color:var(--b)}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px}
figure{margin:0;border-radius:16px;overflow:hidden;background:var(--s);border:1px solid var(--l)}
.im{height:190px;display:flex;align-items:center;justify-content:center;padding:18px}
.im img{max-width:100%;max-height:100%;object-fit:contain}
body.auto figure.l .im{background:var(--w)}body.auto figure.d .im{background:#000}
body.light .im{background:var(--w)}body.dark .im{background:#000}
body.check .im{background:repeating-conic-gradient(#c9c9c9 0 25%,#fff 0 50%) 0 0/20px 20px}
figcaption{padding:10px 12px;font-size:12px;display:flex;flex-direction:column;gap:4px}
figcaption b{font-weight:600;word-break:break-all}figcaption small{color:var(--m)}figcaption a{color:var(--b)}
.sheets{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
.sheets a{color:var(--m);text-decoration:none;font-size:12px}.sheets img{width:100%;height:200px;object-fit:cover;object-position:top;border-radius:12px;display:block;margin-bottom:6px}
@media(max-width:600px){header,section,nav{padding-left:16px;padding-right:16px}.grid{grid-template-columns:repeat(2,1fr)}.tools{margin-left:0}}
</style></head><body class="auto">
<header><img src="../01_LOGO/PNG/logo-mark-inverse-256.png" alt=""><div><h1>Brand Asset Kit</h1>
<p>SVG: %SVG% · PNG: %PNG% · ошибок QA: %ERR% · фон превью переключается справа</p></div></header>
<nav>%NAV%<a href="#sheets">Контакт-листы</a><div class="tools"><input id="q" placeholder="Поиск по имени"><button data-m="auto" class="on">Авто</button><button data-m="light">Светлый</button><button data-m="dark">Тёмный</button><button data-m="check">Прозрачность</button></div></nav>
%CARDS%<section id="sheets"><h2>Контакт-листы</h2><div class="sheets">%SHEETS%</div></section>
<script>
document.querySelectorAll('.tools button').forEach(b=>b.onclick=()=>{document.body.className=b.dataset.m;document.querySelectorAll('.tools button').forEach(x=>x.classList.toggle('on',x===b))});
document.getElementById('q').oninput=e=>{const v=e.target.value.toLowerCase();document.querySelectorAll('figure').forEach(f=>f.style.display=f.dataset.name.includes(v)?'':'none')};
</script></body></html>"""


def build_guide():
    gd = KIT / "00_BRAND_GUIDE"
    (gd / "fonts").mkdir(parents=True, exist_ok=True)
    for f in (SRC / "fonts").glob("*"):
        shutil.copy(f, gd / "fonts" / f.name)
    shutil.copy(SRC / "tokens.json", gd / "design-tokens.json")
    shutil.copy(SRC / "logo-mark.original.svg", gd / "logo-mark.original.svg")
    css = "\n".join(f"  --{k.replace('_', '-')}: {v};" for k, v in C.items())
    (gd / "design-tokens.css").write_text(
        f":root {{\n{css}\n  --font: 'Manrope', system-ui, sans-serif;\n"
        + "".join(f"  --radius-{k}: {v}px;\n" for k, v in T["radius"].items()) + "}\n", encoding="utf-8")
    page = (SRC / "guide_template.html").read_text(encoding="utf-8")
    (gd / "brand-guide.html").write_text(page, encoding="utf-8")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.goto((gd / "brand-guide.html").as_uri())
        pg.wait_for_load_state("networkidle")
        pg.evaluate("document.fonts.ready")
        pg.pdf(path=str(gd / "brand-guide.pdf"), width="1280px", height="800px", print_background=True,
               margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        pg.set_viewport_size({"width": 1280, "height": 800})
        pg.screenshot(path=str(KIT / "10_PREVIEWS" / "brand-guide-cover.png"))
        b.close()
