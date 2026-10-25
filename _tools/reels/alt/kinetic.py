"""ПРОБНЫЙ формат (не утверждён, для справки). Запуск: REEL_WORK=work python3 alt/kinetic.py [dark|light] [caps]"""
"""P4 «Кинетическая типографика»: key phrases fill the screen word by word, short returns to the speaker."""
import sys
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from story import *

THEME = sys.argv[1] if len(sys.argv) > 1 else "dark"
th = THEMES[THEME]
UP_W = 760          # text width allowed in the upper half
LOW_W = 560         # ... and in the lower half (like/comment rail on the right)


@functools.lru_cache(None)
def word(text, size, blue=False, maxw=UP_W):
    while True:
        s = plate(text, size, "ExtraBold", fg=OFF, bg=BLUE, padx=24, pady=8, r=22) if blue else \
            text_sprite(text, size, "ExtraBold", th["text"])
        if s.shape[1] <= maxw or size < 40: return s
        size -= 4


@functools.lru_cache(None)
def cover():
    bg = np.zeros((H, W, 3), np.uint8); bg[:] = th["bg"]
    for x in range(0, W + 1, 72): cv2.line(bg, (x, 0), (x, H), th["grid"], 2)
    for y in range(12, H + 1, 72): cv2.line(bg, (0, y), (W, y), th["grid"], 2)
    return bg


def cover_y(t, t_in, t_out):
    """Panel slides up over the speaker, holds, slides on up and away."""
    if t < t_in or t > t_out + 0.32: return None
    p = ss(prog(t, t_in, 0.3)); q = ss(prog(t, t_out, 0.3))
    return H * (1 - p) - H * q


def lines(fr, t, items, yc, gap=10, fade_out=None, cap=None):
    """items: (text, size, blue, t_in). Block centred on yc; a line that lands in the lower half
    (y > 920, where the like/comment rail is) is refitted to LOW_W."""
    spr = [word(tx, sz, bl) for tx, sz, bl, _ in items]
    for _ in range(2):
        hs = [s_.shape[0] for s_ in spr]; y = yc - (sum(hs) + gap * (len(hs) - 1)) / 2
        for k, (tx, sz, bl, _) in enumerate(items):
            if y + hs[k] > 920: spr[k] = word(tx, sz, bl, LOW_W)
            y += hs[k] + gap
    hs = [s_.shape[0] for s_ in spr]; y = yc - (sum(hs) + gap * (len(hs) - 1)) / 2
    fo = 1 - ein(prog(t, fade_out, 0.18)) if fade_out else 1
    if cap:
        c_, tc = cap; a, _ = appear(t, tc)
        blit(fr, c_, W / 2 - c_.shape[1] / 2, y - 64, alpha=a * fo)
    for s_, (_, _, _, ti), h in zip(spr, items, hs):
        p = prog(t, ti - 0.04, 0.3)
        if p > 0:
            blit(fr, s_, W / 2, y + h / 2 + 18 * (1 - eout(p)), alpha=fo * min(1, p * 4),
                 scale=0.88 + 0.12 * eback(p), anchor="c")
        y += h + gap


S = [E.seg_t(k) for k in range(len(E.FR))] + [E.DUR]


def z_full(t):
    k = E.seg_of(int(t * FPS))
    if k == 3: return 1.36 + 0.03 * prog(t, S[3], 1.0)
    if k >= 10: return 1.16 + 0.05 * ss(prog(t, S[10], 3.2))
    return 1.10 + 0.06 * (1 - eout(prog(t, 0, 0.8))) + 0.04 * ss(t / 7.8)


def render(i, t, src):
    fr = speaker_frame(src, i, lambda f: camera(f, z_full(t), 540, 880))
    # --- speaker scenes: name, question, 'разбираем процессы'
    a, o = appear(t, E.wt(4) - 0.15, 0.35, S[2] - 0.3)
    np_ = name_plate(THEME); blit(fr, np_, W / 2 - np_.shape[1] / 2, SAFE_TOP + 20 + 24 * o, alpha=a)
    q = bar("Что это такое?", THEME, size=76)
    a, o = appear(t, E.wt(19) - 0.05, 0.3, S[4] - 0.1, 0.15)
    blit(fr, q, W / 2 - q.shape[1] / 2, SAFE_TOP + 20 + 24 * o, alpha=a)
    if S[10] - 0.1 <= t < S[11] + 0.2:
        inv = "light" if THEME == "dark" else "dark"
        stack_centered(fr, [(bar("Разбираем", inv, size=70), E.wt(33) - 0.05, S[11] - 0.05),
                            (bar("внутри компании", inv, size=70), E.wt(34) - 0.05, S[11] - 0.05),
                            (bar("процессы", THEME, size=70, blue=True), E.wt(38) - 0.05, S[11] - 0.05)],
                       SAFE_TOP + 20, t)
    # --- type scenes on a full cover
    for (t_in, t_out, scene) in [(S[2] - 0.05, S[3] - 0.3, 1), (S[4] - 0.05, S[10] - 0.3, 2), (S[11] - 0.12, 99, 3)]:
        y0 = cover_y(t, t_in, t_out)
        if y0 is None: continue
        y0 = int(round(y0)); c = cover()
        a0, a1 = max(0, y0), min(H, y0 + H)
        if a1 <= a0: continue
        canvas = c.copy()
        YC = 860
        if scene == 1:
            lines(canvas, t, [("новое", 120, False, E.wt(15)), ("направление", 120, False, E.wt(16)),
                              ("автоматизации", 112, True, E.wt(17)), ("бизнес-процессов", 104, False, E.wt(18))], 760,
                  cap=(caps("МОЯ КОМПАНИЯ ЗАПУСКАЕТ", THEME), E.wt(13) - 0.1))
        elif scene == 2:
            lines(canvas, t, [("Сначала", 150, False, E.wt(25)), ("процесс,", 150, False, E.wt(26)),
                              ("потом", 150, False, E.wt(27)), ("технология", 140, True, E.wt(28))], YC,
                  cap=(caps("НАШ СЛОГАН", THEME), E.wt(23) - 0.05))
        else:
            sw = E.wt(44) - 0.1
            lines(canvas, t, [("Что находится", 110, False, E.wt(39)), ("в ручном", 130, False, E.wt(41)),
                              ("режиме?", 130, True, E.wt(43))], YC, fade_out=sw)
            if t >= sw:
                lines(canvas, t, [("Что менеджеры", 110, False, max(sw + 0.05, E.wt(44))),
                                  ("делают", 130, False, E.wt(46)), ("вручную", 140, True, E.wt(47))], YC)
        fr[a0:a1] = canvas[a0 - y0:a1 - y0]
    return fr


sfx = [("sfx-pop.mp3", E.wt(4) - 0.15, 0.16), ("sfx-click.mp3", S[2], 0.2), ("sfx-pop.mp3", E.wt(17), 0.18),
       ("sfx-click.mp3", S[4], 0.2), ("sfx-pop.mp3", E.wt(28), 0.18), ("sfx-pop.mp3", E.wt(38), 0.15),
       ("sfx-click.mp3", S[11] - 0.1, 0.2), ("sfx-pop.mp3", E.wt(43), 0.15), ("sfx-pop.mp3", E.wt(47), 0.18)]

if __name__ == "__main__":
    os.makedirs(f"{WORK}/out", exist_ok=True)
    encode_story(f"{WORK}/out/reel_p4_kinetic_{THEME}.mp4", render, sfx)
