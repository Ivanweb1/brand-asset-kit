"""Шаблон формата «До / После» (утверждён 25.10.2026). Сцены привязаны к словам ролика через E.wt(i) —
для нового ролика меняются тексты и индексы слов, сетка, тайминги анимаций и стиль остаются.

«До / После»: top panel with two cards — manual mode vs system — speaker in the lower half."""
import os, sys
from story import *

THEME = sys.argv[1] if len(sys.argv) > 1 else "light"
th = THEMES[THEME]
S = [E.seg_t(k) for k in range(len(E.FR))] + [E.DUR]
PB = 840
CWD, CH, CGAP = 370, 460, 20
LX, RX, CY0 = M, M + CWD + CGAP, 330
ROWS = [("reports", "Отчёты"), ("tasks", "Документы"), ("sales", "КП"), ("money", "Расчёты")]


def split_state(t):
    if S[2] <= t < S[3]: return ss(prog(t, S[2], 0.5))
    if t >= S[4]: return ss(prog(t, S[4], 0.45))
    return 0.0


def z_full(t):
    k = E.seg_of(int(t * FPS))
    if k <= 2: return 1.10 + 0.06 * (1 - eout(prog(t, 0, 0.8))) + 0.04 * ss(t / S[3])
    return 1.34 + 0.03 * prog(t, S[3], 1.0)


@functools.lru_cache(None)
def panel():
    p = rrect(W, H, 48, th["bg"]); rgb = p[..., :3].copy()
    for x in range(0, W + 1, 72): cv2.line(rgb, (x, 0), (x, H), th["grid"], 2)
    for y in range(0, H + 1, 72): cv2.line(rgb, (0, y), (W, y), th["grid"], 2)
    return np.concatenate([rgb, p[..., 3:4]], 2)


@functools.lru_cache(None)
def card(blue):
    if blue: return rrect(CWD, CH, 36, BLUE)
    return rrect(CWD, CH, 36, th["surf"], th["line"], 2)


@functools.lru_cache(None)
def card_head(text, blue): return text_sprite(text, 26, "Bold", OFF if blue else th["muted"])


@functools.lru_cache(None)
def card_word(text, blue):
    size = 62
    while True:
        s_ = text_sprite(text, size, "ExtraBold", OFF if blue else th["text"])
        if s_.shape[1] <= CWD - 48: return s_
        size -= 2


@functools.lru_cache(None)
def big_icon(name, blue):
    t = rrect(150, 150, 38, (255, 255, 255) if not blue else (61, 132, 255), None if blue else th["line"], 0 if blue else 2)
    rgb = t[..., :3].copy(); blit(rgb, icon(name, 86, "on-dark" if blue else th["icon"]), 75, 75, anchor="c")
    return np.concatenate([rgb, t[..., 3:4]], 2)


@functools.lru_cache(None)
def row(k, blue):
    w, h = CWD - 40, 70
    b = rrect(w, h, 18, (61, 132, 255) if blue else (255, 255, 255), None if blue else th["line"], 0 if blue else 2)
    rgb = b[..., :3].copy()
    blit(rgb, icon(ROWS[k][0], 40, "on-dark" if blue else th["icon"]), 16, 15)
    tx = text_sprite(ROWS[k][1], 28, "Bold", OFF if blue else th["text"]); blit(rgb, tx, 70, (h - tx.shape[0]) / 2 - 2)
    return np.concatenate([rgb, b[..., 3:4]], 2)


@functools.lru_cache(None)
def mini_toggle(on):
    t = rrect(56, 32, 16, OFF if on else th["surf"], None if on else th["muted"], 0 if on else 2)
    rgb = t[..., :3].copy()
    k = rrect(22, 22, 8, BLUE if on else th["muted"]); blit(rgb, k, 29 if on else 5, 5)
    return np.concatenate([rgb, t[..., 3:4]], 2)


@functools.lru_cache(None)
def arrow_badge():
    b = rrect(84, 84, 26, GRAPH); rgb = b[..., :3].copy()
    cv2.line(rgb, (24 * 4, 42 * 4), (58 * 4, 42 * 4), OFF, 5, cv2.LINE_AA, shift=2)
    cv2.polylines(rgb, [np.array([[46, 30], [60, 42], [46, 54]]) * 4], False, OFF, 5, cv2.LINE_AA, shift=2)
    return np.concatenate([rgb, b[..., 3:4]], 2)


def cards(fr, t, off):
    t_proc = S[10]
    for side, x, blue, head1, head2, word, ic, tw in [
            ("L", LX, False, "СНАЧАЛА", "ДО · ВРУЧНУЮ", "процесс", "process", E.wt(25)),
            ("R", RX, True, "ПОТОМ", "ПОСЛЕ · СИСТЕМА", "технология", "automation", E.wt(27))]:
        p = prog(t, tw - 0.08, 0.4)
        if p <= 0: continue
        y = CY0 + off + 30 * (1 - eout(p)); a = min(1, p * 3)
        sw = eout(prog(t, t_proc - 0.1, 0.35))            # slogan -> process list
        if side == "R":
            # 'после' card: blue for the slogan, an empty dashed slot while he talks about manual work,
            # fills blue again when the automated rows arrive
            fill = (1 - sw) + sw * ss(prog(t, E.wt(45) - 0.15, 0.4))
            blit(fr, dashed_frame(CWD, CH, THEME), x, y, alpha=a * (1 - fill))
            blit(fr, card(True), x, y, alpha=a * fill)
            blue = fill > 0.5
        else:
            blit(fr, card(False), x, y, alpha=a)
        # slogan content
        if sw < 1:
            h1 = card_head(head1, blue); blit(fr, h1, x + CWD / 2 - h1.shape[1] / 2, y + 40, alpha=a * (1 - sw))
            bi = big_icon(ic, blue); blit(fr, bi, x + CWD / 2, y + 195, alpha=a * (1 - sw), anchor="c",
                                          scale=0.8 + 0.2 * eback(prog(t, tw, 0.35)))
            wd = card_word(word, blue)
            pw = prog(t, (E.wt(26) if side == "L" else E.wt(28)) - 0.05, 0.3)
            blit(fr, wd, x + CWD / 2 - wd.shape[1] / 2, y + 300 + 16 * (1 - eout(pw)), alpha=a * (1 - sw) * min(1, pw * 3))
        # process content
        if sw > 0:
            h2 = card_head(head2, blue); blit(fr, h2, x + CWD / 2 - h2.shape[1] / 2, y + 36, alpha=a * sw)
            for k in range(4):
                tk = (E.wt(32) + 0.16 * k) if side == "L" else (E.wt(45) + 0.12 * k)
                pr = prog(t, tk, 0.32)
                if pr <= 0: continue
                ry = y + 96 + k * 92
                blit(fr, row(k, blue), x + 20, ry + 10 * (1 - eout(pr)), alpha=sw * min(1, pr * 3))
                tg_t = (E.wt(42) + 0.1 * k) if side == "L" else (E.wt(47) + 0.1 * k)
                pt = prog(t, tg_t, 0.25)
                if pt > 0:
                    blit(fr, mini_toggle(blue), x + CWD - 20 - 76, ry + 19, alpha=sw * min(1, pt * 3))
    pa = prog(t, E.wt(27) - 0.08, 0.35)
    if pa > 0:
        blit(fr, arrow_badge(), W / 2, CY0 + off + CH / 2, alpha=min(1, pa * 3), scale=0.6 + 0.4 * eback(pa), anchor="c")


@functools.lru_cache(None)
def shade():
    """Light bottom gradient: keeps captions readable and the Instagram UI calm."""
    y = np.arange(H, dtype=np.float32)
    a = np.clip((y - 1150) / (H - 1150), 0, 1) ** 1.4 * 0.7
    return a[:, None, None]


@functools.lru_cache(None)
def cap_soft(text, on):
    return text_sprite(text, 46, "SemiBold" if not on else "Bold", OFF if on else (196, 198, 202))


CAP_CHUNKS = None


def soft_captions(fr, t, y=1526, maxw=560):
    global CAP_CHUNKS
    if CAP_CHUNKS is None:
        CAP_CHUNKS = []; cur = []; w = 0
        for j, (wd, _) in enumerate(E.WORDS):
            ww = cap_soft(wd, True).shape[1]
            if cur and w + 12 + ww > maxw: CAP_CHUNKS.append(cur); cur = []; w = 0
            cur.append(j); w += (12 if len(cur) > 1 else 0) + ww
            if wd[-1] in ".?:" or j == len(E.WORDS) - 1: CAP_CHUNKS.append(cur); cur = []; w = 0
    for ci, ch in enumerate(CAP_CHUNKS):
        t0 = E.wt(ch[0]); t1 = E.wt(CAP_CHUNKS[ci + 1][0]) if ci + 1 < len(CAP_CHUNKS) else E.DUR + 1
        if not (t0 - 0.03 <= t < t1 - 0.03): continue
        cur = max([j for j in ch if E.wt(j) <= t + 0.03] or [ch[0]])
        sp = [cap_soft(E.WORDS[j][0], j <= cur) for j in ch]
        tw = sum(s_.shape[1] for s_ in sp) + 12 * (len(sp) - 1); x = W / 2 - tw / 2
        p = eout(prog(t, t0 - 0.03, 0.14))
        for s_ in sp: blit(fr, s_, x, y + 8 * (1 - p), alpha=p); x += s_.shape[1] + 12


def render(i, t, src):
    s = split_state(t)
    if s <= 0.001:
        fr = speaker_frame(src, i, lambda f: camera(f, z_full(t), 540, 870))
    else:
        pb = lerp(0, PB, s)
        z = lerp(z_full(t), 1.22 + 0.04 * ss(prog(t, S[4], E.DUR - S[4])), s)
        rt = int(max(0, pb - 50)); rh = H - rt
        fr = np.empty((H, W, 3), np.uint8); fr[:] = th["bg"]
        fr[rt:] = speaker_frame(src, i, lambda f: camera(f, z, 540, lerp(870, 1190, s) - rt, W, rh))
        blit(fr, panel(), 0, pb - H + 1)
        off = pb - PB
        if t < S[3]:
            cp = caps("НОВОЕ НАПРАВЛЕНИЕ", THEME); a, o = appear(t, S[2] + 0.25)
            blit(fr, cp, W / 2 - cp.shape[1] / 2, 300 + off + 12 * o, alpha=a)
            a, o = appear(t, E.wt(17) - 0.1)
            for n, ln in enumerate(["Автоматизация", "бизнес-процессов"]):
                ttl = text_sprite(ln, 58, "ExtraBold", th["text"])
                blit(fr, ttl, W / 2 - ttl.shape[1] / 2, 340 + n * 66 + off + 16 * o, alpha=a)
            tg = toggle_widget(ss(prog(t, E.wt(17) + 0.25, 0.3)))
            a, o = appear(t, S[2] + 0.35)
            blit(fr, tg, W / 2 - tg.shape[1] / 2, 500 + off + 20 * o, alpha=a)
        else:
            cp = caps("НАШ СЛОГАН", THEME); a, o = appear(t, E.wt(23) - 0.1, 0.3, S[10] - 0.1)
            blit(fr, cp, W / 2 - cp.shape[1] / 2, 288 + off + 10 * o, alpha=a)
            cards(fr, t, off)
    if s < 0.5:
        a, o = appear(t, E.wt(4) - 0.15, 0.35, S[2] - 0.25)
        np_ = name_plate(THEME); blit(fr, np_, W / 2 - np_.shape[1] / 2, 310 + 24 * o, alpha=a)
        q = bar("Что это такое?", THEME, size=76)
        a, o = appear(t, E.wt(19) - 0.05, 0.3, S[4] - 0.1, 0.15)
        blit(fr, q, W / 2 - q.shape[1] / 2, 310 + 24 * o, alpha=a)
    fr = (fr.astype(np.float32) * (1 - shade())).astype(np.uint8)
    soft_captions(fr, t)
    return fr


sfx = [("sfx-pop.mp3", E.wt(4) - 0.15, 0.16), ("sfx-click.mp3", S[2], 0.2), ("sfx-click.mp3", E.wt(17) + 0.25, 0.4),
       ("sfx-click.mp3", S[4], 0.2), ("sfx-pop.mp3", E.wt(25) - 0.08, 0.16), ("sfx-pop.mp3", E.wt(27) - 0.08, 0.18)] + \
      [("sfx-pop.mp3", E.wt(32) + 0.16 * k, 0.1) for k in range(4)] + [("sfx-click.mp3", E.wt(42), 0.22),
                                                                        ("sfx-click.mp3", E.wt(47), 0.3)]

if __name__ == "__main__":
    os.makedirs(f"{WORK}/out", exist_ok=True)
    encode_story(f"{WORK}/out/reel_before_after_{THEME}.mp4", render, sfx)
