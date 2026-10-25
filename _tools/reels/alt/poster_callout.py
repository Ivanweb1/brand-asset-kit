"""ПРОБНЫЙ формат (не утверждён, для справки). Запуск: REEL_WORK=work python3 alt/poster_callout.py [dark|light] [caps]"""
"""P6 «Выноска на постер»: on 'наш слоган' the camera flies to the real poster on the wall
(sharp 4K crop), brand brackets + underlines land on the words; word-synced captions throughout."""
import sys
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from story import *

THEME = "dark"
S = [E.seg_t(k) for k in range(len(E.FR))] + [E.DUR]
FACE_P, FACE_Q = (600.0, 945.0), (540.0, 880.0)
POST_P, POST_Q, POST_Z = (370.0, 785.0), (540.0, 820.0), 2.6
HI_X0, HI_Y0 = 100.0, 380.0          # base-frame origin of poster_hi.mp4 (2 hi px per base px)
U_IN, U_OUT = E.wt(23) - 0.12, S[10] - 0.45


class HiSource(Source):
    def __init__(self):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", f"{WORK}/poster_hi.mp4", "-f", "rawvideo",
                                   "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, bufsize=10 ** 8)
        self.n = 1200 * 1840 * 3; self.next = 0; self.cache = {}

    def get(self, f):
        while self.next <= f:
            b = self.p.stdout.read(self.n)
            if len(b) < self.n: break
            self.cache[self.next] = np.frombuffer(b, np.uint8).reshape(1840, 1200, 3); self.next += 1
            for old in [k for k in self.cache if k < self.next - 10]: del self.cache[old]
        return self.cache[min(f, self.next - 1)]


HI = None


def z_full(t):
    k = E.seg_of(int(t * FPS))
    if k == 3: return 1.36 + 0.03 * prog(t, S[3], 1.0)
    return 1.10 + 0.06 * (1 - eout(prog(t, 0, 0.8))) + 0.05 * ss(prog(t, S[4] if t > S[4] else 0, 8))


def view(t):
    u = ss(prog(t, U_IN, 0.75)) * (1 - ss(prog(t, U_OUT, 0.55)))
    z0 = z_full(t)
    z = math.exp(lerp(math.log(z0), math.log(POST_Z), u))
    P = (lerp(FACE_P[0], POST_P[0], u), lerp(FACE_P[1], POST_P[1], u))
    Q = (lerp(FACE_Q[0], POST_Q[0], u), lerp(FACE_Q[1], POST_Q[1], u))
    return u, z, P, Q


def cam_lo(src, z, P, Q):
    s = 0.75 * z
    x0 = Q[0] - s * P[0] * 4 / 3; y0 = Q[1] - s * P[1] * 4 / 3
    x0 = min(0, max(W - s * SRC_W, x0)); y0 = min(0, max(H - s * SRC_H, y0))
    return cv2.warpAffine(src, np.float32([[s, 0, x0], [0, s, y0]]), (W, H), flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)


def cam_hi(hi, z, P, Q):
    s = z / 2
    x0 = Q[0] + z * (HI_X0 - P[0]); y0 = Q[1] + z * (HI_Y0 - P[1])
    return cv2.warpAffine(hi, np.float32([[s, 0, x0], [0, s, y0]]), (W, H), flags=cv2.INTER_AREA,
                          borderMode=cv2.BORDER_REPLICATE)


def to_out(bx, by): return ((bx - POST_P[0]) * POST_Z + POST_Q[0], (by - POST_P[1]) * POST_Z + POST_Q[1])


@functools.lru_cache(None)
def bracket(size=46, th_=7):
    im = np.zeros((size, size, 4), np.uint8)
    cv2.line(im, (th_ // 2, th_ // 2), (size - 1, th_ // 2), BLUE + (255,), th_)
    cv2.line(im, (th_ // 2, th_ // 2), (th_ // 2, size - 1), BLUE + (255,), th_)
    return im


def brackets(fr, x0, y0, x1, y1, a, grow):
    b = bracket(); pad = 18 * (1 - grow) + 14
    for img, x, y in [(b, x0 - pad, y0 - pad), (b[:, ::-1], x1 + pad - b.shape[1], y0 - pad),
                      (b[::-1], x0 - pad, y1 + pad - b.shape[0]), (b[::-1, ::-1], x1 + pad - b.shape[1], y1 + pad - b.shape[0])]:
        blit(fr, np.ascontiguousarray(img), x, y, alpha=a)


@functools.lru_cache(None)
def backdrop(w, h): return rrect(w, h, 36, GRAPH + (232,))


def render(i, t, src):
    global HI
    if HI is None: HI = HiSource()
    u, z, P, Q = view(t)
    f, k = E.src_frame(i)
    fr = speaker_frame(src, i, lambda s_: cam_lo(s_, z, P, Q))
    if u > 0.75:
        hi = cam_hi(HI.get(max(0, f - 360)), z, P, Q)
        a = ss((u - 0.75) / 0.25)
        fr = (fr * (1 - a) + hi * a).astype(np.uint8)
    # --- poster call-out
    if u > 0.9:
        a = ss((u - 0.9) / 0.1)
        (x0, y0), (x1, y1) = to_out(230, 670), to_out(380, 904)
        brackets(fr, x0, y0, x1, y1, a, eout(prog(t, U_IN + 0.75, 0.35)))
        cp = caps("НАШ СЛОГАН", THEME, OFF)
        pl = rrect(cp.shape[1] + 40, cp.shape[0] + 20, 14, BLUE)
        blit(fr, pl, W / 2 - pl.shape[1] / 2, SAFE_TOP + 40, alpha=a); blit(fr, cp, W / 2 - cp.shape[1] / 2, SAFE_TOP + 50, alpha=a)
        for (ly, tw) in [(760, E.wt(26)), (826, E.wt(28))]:
            p = eout(prog(t, tw - 0.05, 0.35))
            if p > 0:
                (ux0, uy), (ux1, _) = to_out(250, ly), to_out(362, ly)
                fill_rect(fr, ux0, uy + 4, ux0 + (ux1 - ux0) * p, uy + 13, BLUE, alpha=a)
    # --- talking-head moments
    a, o = appear(t, E.wt(4) - 0.15, 0.35, S[2] - 0.25)
    np_ = name_plate(THEME); blit(fr, np_, W / 2 - np_.shape[1] / 2, SAFE_TOP + 20 + 24 * o, alpha=a)
    t_out = S[3] - 0.2
    stack_centered(fr, [(bar("Новое направление", THEME), E.wt(15) - 0.05, t_out),
                        (bar("автоматизации", THEME, blue=True), E.wt(17) - 0.05, t_out),
                        (bar("бизнес-процессов", THEME), E.wt(18) - 0.05, t_out)], SAFE_TOP + 20, t)
    q = bar("Что это такое?", THEME, size=76)
    a, o = appear(t, E.wt(19) - 0.05, 0.3, S[4] - 0.1, 0.15)
    blit(fr, q, W / 2 - q.shape[1] / 2, SAFE_TOP + 20 + 24 * o, alpha=a)
    if t >= S[10] - 0.2:
        a = eout(prog(t, S[10] - 0.1, 0.35))
        bd = backdrop(840, 520); blit(fr, bd, W / 2 - 420, SAFE_TOP - 10 + 20 * (1 - a), alpha=a)
        processes(fr, t, THEME, SAFE_TOP + 22)
    captions(fr, t, 1240)
    return fr


sfx = [("sfx-pop.mp3", E.wt(4) - 0.15, 0.16), ("sfx-pop.mp3", E.wt(17), 0.16), ("sfx-click.mp3", U_IN + 0.7, 0.3),
       ("sfx-pop.mp3", E.wt(26), 0.12), ("sfx-pop.mp3", E.wt(28), 0.14), ("sfx-click.mp3", S[10] - 0.1, 0.2)] + \
      [("sfx-pop.mp3", E.wt(34) + 0.1 + 0.16 * k, 0.1) for k in range(4)] + [("sfx-click.mp3", E.wt(42), 0.25)]

if __name__ == "__main__":
    os.makedirs(f"{WORK}/out", exist_ok=True)
    encode_story(f"{WORK}/out/reel_p6_poster_callout.mp4", render, sfx)
