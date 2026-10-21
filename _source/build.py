"""Полная пересборка комплекта: python build.py  (из папки _source).
Флаги: --no-png — только SVG; --no-zip — без архива."""
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import kit
from kit import KIT, SRC
import build_logo, build_elements, build_icons, build_labels, build_type, build_overlays, build_bg, build_social, build_extras
import qa
import catalog

OUT_DIRS = ["01_LOGO", "02_GRAPHIC_ELEMENTS", "03_ICONS", "04_LABELS", "05_TYPOGRAPHY", "06_VIDEO_OVERLAYS",
            "07_BACKGROUNDS", "08_SOCIAL_TEMPLATES", "09_EXTRA_ELEMENTS", "10_PREVIEWS"]


def make_zip():
    import zipfile
    z = KIT.parent / "BRAND_ASSET_KIT.zip"
    skip = ("_cache", "__pycache__", "_test")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(KIT.rglob("*")):
            if p.is_file() and not any(s in p.parts for s in skip) and p.name != "qa-report.json":
                zf.write(p, Path("BRAND_ASSET_KIT") / p.relative_to(KIT))
    print("ZIP:", z, f"{z.stat().st_size / 1e6:.1f} МБ")


def main():
    t0 = time.time()
    for d in OUT_DIRS + ["_source/_cache"]:
        shutil.rmtree(KIT / d, ignore_errors=True)
    counts = {
        "logo": build_logo.build() or None,
        "elements": build_elements.build(),
        "icons": build_icons.build(),
        "labels": build_labels.build(),
        "typography": build_type.build(),
        "overlays": build_overlays.build(),
        "backgrounds": build_bg.build(),
        "social": build_social.build(),
        "extras": build_extras.build(),
    }
    catalog.sheets()
    print("SVG:", kit.STATS)
    if "--no-png" not in sys.argv:
        from render import render
        print(f"Рендер {len(kit.JOBS)} PNG…")
        render(kit.JOBS)
        build_extras.post_render()
    report = qa.run()
    catalog.build_catalog(counts, report)
    catalog.build_guide()
    if "--no-zip" not in sys.argv:
        make_zip()
    print(f"Готово за {time.time() - t0:.0f} с")


if __name__ == "__main__":
    main()
