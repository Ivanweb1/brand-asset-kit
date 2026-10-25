"""Быстрый просмотр кадров без полного рендера:
    REEL_WORK=work python3 peek.py before_after 1.6,9.6,17.3 light
Сохраняет полосу кадров в work/out/peek.png; с флагом --zones накладывает зоны интерфейса Reels."""
import sys, importlib, os
MOD, TS, REST = sys.argv[1], sys.argv[2], [a for a in sys.argv[3:] if a != "--zones"]
ZONES = "--zones" in sys.argv
sys.argv = [sys.argv[0]] + REST
mod = importlib.import_module(MOD)
from story import *
from zonecheck import overlay
src = Source(); tiles = []
for t in sorted(float(x) for x in TS.split(",")):
    i = min(E.NFRAMES - 1, int(round(t * FPS))); fr = mod.render(i, i / FPS, src)
    if ZONES: fr = overlay(fr)
    tiles.append(cv2.resize(fr, (360, 640), interpolation=cv2.INTER_AREA))
os.makedirs(f"{WORK}/out", exist_ok=True)
Image.fromarray(np.concatenate(tiles, 1)).save(f"{WORK}/out/peek.png"); print(f"{WORK}/out/peek.png")
