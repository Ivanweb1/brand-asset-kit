"""Ролик R050 «Сайт парфюма за 10 000 ₽ — и за 100 000 ₽» (~10,4 с, без голоса, без автора).

Серия «10к vs 100к»: устройство и тайминги — как у R049 (r049_budget.py), меняются тексты и записи экранов.
Кринж — дефолтный сайт духов по одному запросу (Desktop/cringe-screens/perfume), вау — экран MIRRA (R045).

Исходники:
  work/r050/cringe-full.png   — полный скриншот кринж-экрана (cringe-screens/tools/fullpage.mjs perfume …)
  work-perfume/frames         — кадры MIRRA 1770×1060, 30 к/с (perfume_record.py)

    python r050_budget_perfume.py              # -> example-r050-budget-perfume/final.mp4, cover.jpg
    python r050_budget_perfume.py peek 1 3 6   # кадры work/r050/peek_<t>.png
"""
import sys, pathlib, functools
import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r049_budget as B
from r049_budget import OFF, BLUE, GRAPH, FPS, BW, VH, S_CR, S_WOW, T_NOTE

B.WORK = B.K / "work" / "r050"
B.OUT = HERE / "example-r050-budget-perfume"
WOW_DIR = HERE / "work-perfume" / "frames"

B.CHAT[:] = [
    (0.10, "in", "Нужен сайт для бренда духов, бюджет 10к", "18:02"),
    (0.80, "out", "Держите", "18:20"),
    (3.60, "in", "Ой… вообще-то бюджет 100к", "18:23"),
    (4.20, "out", "Тогда так", "18:24"),
    (8.50, "in", "Куда предоплату?", "18:31"),
]
B.HOOK[:] = [("Сайт парфюма за 10 000 ₽ —", OFF, GRAPH), ("и за 100 000 ₽", BLUE, OFF)]
B.CAPS[0] = (0.0, S_CR[0] - 0.2, B.HOOK)

# время в вау-сцене → время записи MIRRA: капля и спираль, быстро мимо статичного флакона, ноты
WOW_T = [0.0, 1.7, 2.3, 3.6]
SRC_T = [1.4, 4.9, 7.5, 8.9]


@functools.lru_cache(maxsize=8)
def wow_src(i):
    n = len(list(WOW_DIR.glob("f*.jpg")))
    im = Image.open(WOW_DIR / f"f{min(i, n - 1):04d}.jpg").convert("RGB")
    w = round(im.width * VH / im.height); im = im.resize((w, VH), Image.LANCZOS)   # 1770×1060 → по высоте, обрезка по бокам
    x = (w - BW) // 2
    return im.crop((x, 0, x + BW, VH))


def wow_frame(t):
    src = float(np.interp(t, WOW_T, SRC_T))
    return B.browser_frame(wow_src(int(src * FPS)), "mirra-parfum.ru", t, S_WOW[1] - S_WOW[0])


def cringe_frame(t):
    d = S_CR[1] - S_CR[0]; pg = B.cringe_page()
    off = int(B.ss(B.prog(t, 0.35, d - 0.5)) * 1050)              # листаем до карточек ароматов
    return B.browser_frame(pg.crop((0, off, BW, off + VH)), "parfum-site.ru", t, d)


B.wow_src = lambda i: wow_src(int(8.6 * FPS)) if i == int(7.6 * FPS) else wow_src(i)   # кадр для обложки — ноты
B.wow_frame = wow_frame
B.cringe_frame = cringe_frame

if __name__ == "__main__":
    if sys.argv[1:2] == ["peek"]:
        B.main([float(s) for s in sys.argv[2:]])
    else:
        B.main()
