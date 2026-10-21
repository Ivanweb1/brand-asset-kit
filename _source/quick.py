"""Быстрый рендер одной секции для итераций: python quick.py social|overlays|labels|bg"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import kit, sheet, catalog
from kit import KIT
from render import render
sec = sys.argv[1]
mod = {"social": "build_social", "overlays": "build_overlays", "labels": "build_labels", "bg": "build_bg", "elements": "build_elements", "posters": "build_posters"}[sec]
__import__(mod).build()
render(kit.JOBS)
kit.JOBS.clear()
g = lambda p: sorted(KIT.glob(p))
S = {"social": [("sheet-08-posts.png", g("08_SOCIAL_TEMPLATES/SVG/*-post-1080x1350.svg"), (460, 620)),
                ("sheet-08-stories.png", g("08_SOCIAL_TEMPLATES/SVG/*-story-1080x1920.svg"), (380, 700)),
                ("sheet-08-carousels.png", g("08_SOCIAL_TEMPLATES/SVG/carousel-*/*-1080x1350.svg"), (330, 450))],
     "overlays": [("sheet-06-overlays.png", g("06_VIDEO_OVERLAYS/SVG/*.svg"), (380, 700))],
     "labels": [("sheet-04-labels.png", [p for p in g("04_LABELS/SVG/*.svg") if "empty" not in p.name], (460, 300))],
     "bg": [("sheet-07-backgrounds.png", g("07_BACKGROUNDS/SVG/*1080x1350.svg"), (300, 400))],
     "posters": [("sheet-08-posters.png", g("08_SOCIAL_TEMPLATES/SVG/posters/*-a-poster.svg"), (440, 640))],
     "elements": [("sheet-02-elements-on-dark.png", g("02_GRAPHIC_ELEMENTS/SVG/*-on-dark.svg"), (320, 260))]}[sec]
for name, svgs, cell in S:
    sheet.contact_sheet(f"10_PREVIEWS/{name}", svgs, width=2400, cell=cell, bg="#5A5D60")
render(kit.JOBS)
