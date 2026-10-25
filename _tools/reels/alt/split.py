"""ПРОБНЫЙ формат (не утверждён, для справки). Запуск: REEL_WORK=work python3 alt/split.py [dark|light] [caps]"""
"""V3 «Сплит» — tight cut. Usage: python3 v3s.py dark|light [caps]"""
import sys
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from story import *

THEME = sys.argv[1] if len(sys.argv) > 1 else "dark"
CAPS = "caps" in sys.argv
th = THEMES[THEME]
SPLIT = 940
S1, S1_END, S2 = E.seg_t(2), E.seg_t(3), E.seg_t(4)    # split on 'что моя компания', off for 'Что это такое?', on again


def split_state(t):
    if S1 <= t < S1_END: return ss(prog(t, S1, 0.5))
    if t >= S2: return ss(prog(t, S2, 0.45))
    return 0.0


def z_full(t):
    k = E.seg_of(int(t * FPS))
    if k <= 2: return 1.10 + 0.06 * (1 - eout(prog(t, 0, 0.8))) + 0.04 * ss(t / E.seg_t(3))
    return 1.34 + 0.03 * prog(t, E.seg_t(3), 1.0)


def z_split(t): return 1.26 + 0.05 * ss(prog(t, S2, E.DUR - S2)) if t >= S2 else 1.26


@functools.lru_cache(None)
def panel():
    p = rrect(W, H, 48, th["bg"]); rgb = p[..., :3].copy()
    for x in range(0, W + 1, 72): cv2.line(rgb, (x, 0), (x, H), th["grid"], 2)
    for y in range(0, H + 1, 72): cv2.line(rgb, (0, y), (W, y), th["grid"], 2)
    return np.concatenate([rgb, p[..., 3:4]], 2)


PB = 930        # panel bottom when open: graphics live in the top half, clear of the right-hand rail


def render(i, t, src):
    s = split_state(t)
    if s <= 0.001:
        fr = speaker_frame(src, i, lambda f: camera(f, z_full(t), 540, 870))
    else:
        pb = lerp(0, PB, s)
        z = lerp(z_full(t), 1.22 + 0.04 * ss(prog(t, S2, E.DUR - S2)), s)
        rt = int(max(0, pb - 50)); rh = H - rt
        fr = np.empty((H, W, 3), np.uint8); fr[:] = th["bg"]
        fr[rt:] = speaker_frame(src, i, lambda f: camera(f, z, 540, lerp(870, 1250, s) - rt, W, rh))
        blit(fr, panel(), 0, pb - H + 1)
        off = pb - PB
        if t < S1_END:
            cp = caps("МОЯ КОМПАНИЯ ЗАПУСКАЕТ", THEME)
            a, o = appear(t, E.wt(13) - 0.1)
            blit(fr, cp, W / 2 - cp.shape[1] / 2, SAFE_TOP + 20 + off + 14 * o, alpha=a)
            inv = "light" if THEME == "dark" else "dark"
            stack_centered(fr, [(bar("Новое направление", inv), E.wt(15) - 0.05, None),
                                (bar("автоматизации", THEME, blue=True), E.wt(17) - 0.05, None),
                                (bar("бизнес-процессов", inv), E.wt(18) - 0.05, None)], SAFE_TOP + 75 + off, t)
        elif t < E.seg_t(10) + 0.1:
            slogan(fr, t, THEME, SAFE_TOP + 70 + off, E.seg_t(10) - 0.12)
        else:
            processes(fr, t, THEME, SAFE_TOP + 10 + off)
        if CAPS and s >= 0.5: captions(fr, t, 1440)
    if s < 0.5:
        a, o = appear(t, E.wt(4) - 0.15, 0.35, E.seg_t(2) - 0.25)
        np_ = name_plate(THEME)
        blit(fr, np_, W / 2 - np_.shape[1] / 2, SAFE_TOP + 20 + 24 * o, alpha=a)
        q = bar("Что это такое?", THEME, size=76)
        a, o = appear(t, E.wt(19) - 0.05, 0.3, S2 - 0.1, 0.15)
        blit(fr, q, W / 2 - q.shape[1] / 2, SAFE_TOP + 20 + 24 * o, alpha=a)
        if CAPS: captions(fr, t, 1180)
    return fr


sfx = [("sfx-pop.mp3", E.wt(4) - 0.15, 0.18), ("sfx-click.mp3", S1, 0.22), ("sfx-pop.mp3", E.wt(17) - 0.05, 0.2),
       ("sfx-click.mp3", S2, 0.22)] + [("sfx-pop.mp3", E.wt(j) - 0.04, 0.16) for j in (25, 28)] + \
      [("sfx-pop.mp3", E.wt(34) + 0.1 + 0.16 * k, 0.12) for k in range(4)] + [("sfx-click.mp3", E.wt(42), 0.3)]

if __name__ == "__main__":
    name = f"reel_v3{'b' if THEME == 'light' else 'a'}_split_{THEME}{'_caps' if CAPS else ''}.mp4"
    os.makedirs(f"{WORK}/out", exist_ok=True)
    encode_story(f"{WORK}/out/{name}", render, sfx)
