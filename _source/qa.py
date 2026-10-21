"""Контроль качества: SVG валиден и векторный, цвета из палитры, кириллица есть в шрифте,
PNG прозрачные где нужно, размеры верные, ничего не вылезает за viewBox, нет дублей."""
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

from PIL import Image

from kit import KIT, C, face, JOBS

ALLOWED = {v.upper() for v in C.values()} | {"#000", "#FFFFFF", "#8A8D91", "#5A5D60"}
SERVICE = {"#FF3B30"}  # только в гайде безопасных зон
OPAQUE_DIRS = ("07_BACKGROUNDS", "08_SOCIAL_TEMPLATES", "10_PREVIEWS")
OPAQUE_NAMES = ("avatar-upload", "cta-end-screen", "loader-sequence")


def run():
    rep = {"svg": 0, "png": 0, "errors": [], "warnings": []}
    err, warn = rep["errors"], rep["warnings"]
    cmap = face(400).tt.getBestCmap()
    svgs = [p for p in KIT.rglob("*.svg") if "_source" not in p.parts]
    for p in svgs:
        rep["svg"] += 1
        s = p.read_text(encoding="utf-8")
        try:
            ET.fromstring(s.encode("utf-8"))
        except ET.ParseError as e:
            err.append(f"SVG не парсится: {p.relative_to(KIT)}: {e}")
            continue
        if not re.search(r'viewBox="0 0 [\d.]+ [\d.]+"', s):
            err.append(f"нет viewBox: {p.name}")
        if "<image" in s:
            err.append(f"растр внутри SVG: {p.name}")
        for col in set(re.findall(r'#[0-9A-Fa-f]{6}\b', s)):
            c = col.upper()
            if c in SERVICE and "guide-safe" in p.name:
                continue
            if c not in ALLOWED:
                err.append(f"цвет вне палитры {c}: {p.name}")
        for t in re.findall(r"<text[^>]*>(.*?)</text>", s, re.S):
            t = re.sub(r"<[^>]+>", "", t)
            t = t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"')
            miss = {ch for ch in t if ord(ch) not in cmap and not ch.isspace()}
            if miss:
                err.append(f"нет глифов {miss}: {p.name}")
        if "<text" in s and 'font-family="Manrope"' not in s:
            err.append(f"не Manrope: {p.name}")

    hashes = defaultdict(list)
    expected = {str(png): (w, h) for _, png, w, h in JOBS}
    for p in KIT.rglob("*.png"):
        if "_source" in p.parts:
            continue
        rep["png"] += 1
        rel = str(p.relative_to(KIT)).replace("\\", "/")
        im = Image.open(p)
        exp = expected.get(str(p))
        if exp and im.size != exp:
            err.append(f"размер {im.size} ≠ {exp}: {rel}")
        opaque_expected = rel.startswith(OPAQUE_DIRS) or any(n in rel for n in OPAQUE_NAMES) or "solid" in rel
        if im.mode != "RGBA":
            if not opaque_expected:
                err.append(f"нет альфа-канала: {rel}")
            continue
        a = im.getchannel("A")
        lo, hi = a.getextrema()
        if hi == 0:
            err.append(f"пустой PNG: {rel}")
        if not opaque_expected and lo == 255:
            err.append(f"фон не прозрачный: {rel}")
        if opaque_expected and lo < 255 and rel.startswith(("07_", "08_")):
            err.append(f"фон с дырами прозрачности: {rel}")
        if not rel.startswith(("10_", "09_EXTRA_ELEMENTS/PNG/favicon")):
            hashes[hashlib.md5(p.read_bytes()).hexdigest()].append(rel)
    for files in hashes.values():
        if len(files) > 1:
            warn.append("одинаковые PNG: " + ", ".join(files))
    rep.update(overflow=check_overflow(svgs, err))
    (KIT / "_source" / "qa-report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1), encoding="utf-8")
    print("QA-отчёт: _source/qa-report.json")
    print(f"QA: SVG {rep['svg']}, PNG {rep['png']}, ошибок {len(err)}, предупреждений {len(warn)}")
    for e in err[:30]:
        print("  !", e)
    for w in warn[:10]:
        print("  ~", w)
    return rep


def check_overflow(svgs, err):
    """Геометрия не выходит за viewBox (учитывая половину обводки). Проверяем в Chromium через getBBox."""
    from playwright.sync_api import sync_playwright
    from render import BASE
    n = 0
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        page = b.new_page()
        page.set_content(BASE)
        for p in svgs:
            if p.parts[-3] in ("07_BACKGROUNDS", "08_SOCIAL_TEMPLATES") or "08_SOCIAL_TEMPLATES" in p.parts or "cta-end-screen" in p.name:
                continue
            s = re.sub(r"^<\?xml[^>]*>\s*", "", p.read_text(encoding="utf-8"))
            r = page.evaluate("""s => { const c=document.getElementById('c'); c.innerHTML=s; const v=c.firstElementChild;
                let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;
                for (const el of v.children){ if(!el.getBBox||el.tagName==='title'||el.tagName==='text') continue; const bb=el.getBBox(); const m=el.getCTM&&el.getCTM();
                  const sw=parseFloat(getComputedStyle(el).strokeWidth)||0; const k=m?m.a:1;
                  const pts=[[bb.x,bb.y],[bb.x+bb.width,bb.y+bb.height]].map(([x,y])=>m?[m.a*x+m.c*y+m.e, m.b*x+m.d*y+m.f]:[x,y]);
                  x0=Math.min(x0,pts[0][0]);y0=Math.min(y0,pts[0][1]);x1=Math.max(x1,pts[1][0]);y1=Math.max(y1,pts[1][1]); }
                const vb=v.viewBox.baseVal, sc=1;
                return [x0/sc,y0/sc,x1/sc,y1/sc,vb.width,vb.height]; }""", s)
            x0, y0, x1, y1, w, h = r
            tol = 1.5
            if x0 < -tol or y0 < -tol or x1 > w + tol or y1 > h + tol:
                err.append(f"выходит за viewBox [{x0:.0f},{y0:.0f},{x1:.0f},{y1:.0f}] при {w:g}×{h:g}: {p.relative_to(KIT)}")
            n += 1
        b.close()
    return n
