"""ПРОБНЫЙ формат (не утверждён, для справки). Запуск: REEL_WORK=work python3 alt/circle.py [dark|light] [caps]"""
"""V2 «Кругляш» — tight cut. Usage: python3 v2s.py dark|light [caps]"""
import sys
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from story import *

THEME = sys.argv[1] if len(sys.argv) > 1 else "dark"
CAPS = "caps" in sys.argv
th = THEMES[THEME]
T_CIRC = E.seg_t(4)                       # 'Во-первых' -> speaker goes into the circle
CX, CY, R = 540, 1130, 240


def z_full(t):
    k = E.seg_of(int(t * FPS))
    if k <= 2: return 1.10 + 0.06 * (1 - eout(prog(t, 0, 0.8))) + 0.05 * ss(t / E.seg_t(3))
    if k == 3: return 1.34 + 0.03 * prog(t, E.seg_t(3), 1.0)
    return 1.12


@functools.lru_cache(None)
def background():
    bg = np.zeros((H, W, 3), np.uint8); bg[:] = th["bg"]
    for x in range(0, W + 1, 72): cv2.line(bg, (x, 0), (x, H), th["grid"], 2)
    for y in range(12, H + 1, 72): cv2.line(bg, (0, y), (W, y), th["grid"], 2)
    g = np.zeros((H, W), np.float32); cv2.circle(g, (CX, CY), 1, 1.0, -1)
    g = cv2.GaussianBlur(g, (0, 0), 240); g = g / g.max() * (0.20 if THEME == "dark" else 0.10)
    return (bg * (1 - g[..., None]) + np.array(BLUE) * g[..., None]).astype(np.uint8)


def render(i, t, src):
    c = ss(prog(t, T_CIRC, 0.55))
    if c <= 0.001:
        fr = speaker_frame(src, i, lambda s: camera(s, z_full(t), 540, 870))
    else:
        fr = background().copy()
        rr = lerp(1150, R, eout(c)); cx = lerp(540, CX, c); cy = lerp(900, CY, c)
        k = min(1.0, rr / 540)
        cam = speaker_frame(src, i, lambda s: camera(s, lerp(z_full(t), 1.45 + 0.04 * ss(prog(t, T_CIRC, 9)), c), 540, 900))
        M_ = np.float32([[k, 0, cx - 540 * k], [0, k, cy - 900 * k]])
        warped = cv2.warpAffine(cam, M_, (W, H), flags=cv2.INTER_LINEAR)
        mask = np.zeros((H, W), np.float32)
        cv2.circle(mask, (int(cx * 4), int(cy * 4)), int(rr * 4), 1.0, -1, cv2.LINE_AA, shift=2)
        m = mask[..., None]
        fr = (fr * (1 - m) + warped * m).astype(np.uint8)
        if c > 0.5:
            ring = BLUE if THEME == "light" else OFF
            cv2.circle(fr, (int(cx * 4), int(cy * 4)), int((rr + 4) * 4), ring, 6, cv2.LINE_AA, shift=2)
        # scenes
        if t < E.seg_t(10) + 0.1:
            slogan(fr, t, THEME, SAFE_TOP + 40, E.seg_t(10) - 0.12)
        else:
            a = 1.0
            processes(fr, t, THEME, SAFE_TOP)
        # slogan leaves just before 'То есть'
    # full-frame graphics (top zone)
    if t < T_CIRC + 0.1:
        a, o = appear(t, E.wt(4) - 0.15, 0.35, E.seg_t(2) - 0.25)
        np_ = name_plate("dark" if THEME == "dark" else "light")
        blit(fr, np_, W / 2 - np_.shape[1] / 2, SAFE_TOP + 20 + 24 * o, alpha=a)
        t_out = E.seg_t(3) - 0.2
        stack_centered(fr, [(bar("Новое направление", THEME), E.wt(15) - 0.05, t_out),
                            (bar("автоматизации", THEME, blue=True), E.wt(17) - 0.05, t_out),
                            (bar("бизнес-процессов", THEME), E.wt(18) - 0.05, t_out)], SAFE_TOP + 20, t)
        q = bar("Что это такое?", THEME, size=76)
        a, o = appear(t, E.wt(19) - 0.05, 0.3, T_CIRC - 0.1, 0.15)
        blit(fr, q, W / 2 - q.shape[1] / 2, SAFE_TOP + 20 + 24 * o, alpha=a)
        if CAPS and c < 0.5: captions(fr, t, 1180)
    # slogan exit: fade the whole content zone before the process scene
    return fr


def _slogan_exit(t): return None


sfx = [("sfx-pop.mp3", E.wt(4) - 0.15, 0.18), ("sfx-pop.mp3", E.wt(17) - 0.05, 0.2),
       ("sfx-click.mp3", T_CIRC, 0.25)] + [("sfx-pop.mp3", E.wt(j) - 0.04, 0.16) for j in (25, 28)] + \
      [("sfx-pop.mp3", E.wt(34) + 0.1 + 0.16 * k, 0.12) for k in range(4)] + [("sfx-click.mp3", E.wt(42), 0.3)]

if __name__ == "__main__":
    name = f"reel_v2{'b' if THEME == 'light' else 'a'}_circle_{THEME}{'_caps' if CAPS else ''}.mp4"
    os.makedirs(f"{WORK}/out", exist_ok=True)
    encode_story(f"{WORK}/out/{name}", render, sfx)
