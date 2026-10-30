"""Ролик R011 «Зачем бизнесу автоматизировать процессы» (аватар HeyGen) — формат «список из трёх пунктов».

Основа — r003_report.py: панель, сетка, субтитры, камера и тайминги анимаций те же,
вместо карточек «до / после» — три строки списка. Слова и куски — $REEL_WORK/edit.json.

Сцены:
  кусок 0      полный кадр, хук: «Зачем бизнесу / автоматизировать / процессы в 2026 году?»
  куски 1–9    панель «ЗАЧЕМ АВТОМАТИЗИРОВАТЬ»: строки «Деньги / Скорость / Ошибки» появляются на
               «Первое / Второе / Третье», текущая синяя; подпись строки — на словах пояснения,
               тумблер строки включается на ключевом слове
  куски 10–11  крупный план, призыв: «Напишите в директ» + «„АУДИТ“»
"""
import os, sys
from story import *

THEME = sys.argv[1] if len(sys.argv) > 1 else "light"
th = THEMES[THEME]
S = [E.seg_t(k) for k in range(len(E.FR))] + [E.DUR]
PB = 840
RW, RH, RGAP, RY0 = CW, 122, 14, 408

# (иконка, заголовок, подпись — только сказанное, слово появления строки, заголовка, подписи, тумблера)
ITEMS = [("money", "Деньги", "Работу делает система", 7, 8, 14, 18),
         ("time", "Скорость", "Задачи не теряются", 19, 20, 21, 23),
         ("errors", "Ошибки", "Система не путает цифры", 26, 27, 28, 33)]
T_IN = [E.wt(it[3]) - 0.05 for it in ITEMS]


def push(t, t0, amt, d=0.5):
    """Плавный наезд на слове: зум растёт на amt за d секунд с замедлением в конце."""
    return amt * ss(prog(t, t0, d))


def split_state(t):
    if S[1] <= t < S[10]: return ss(prog(t, S[1], 0.5))
    return 0.0


def z_full(t):
    if t < S[1]: return 1.10 + 0.06 * (1 - eout(prog(t, 0, 0.8))) + 0.04 * ss(t / S[1])
    # призыв: крупный план, наезд на «разберу», дальше медленный дрейф до конца
    return 1.34 + 0.03 * prog(t, S[10], E.DUR - S[10]) + push(t, E.wt(39) - 0.05, 0.12) + 0.04 * prog(t, E.wt(40), E.DUR - E.wt(40))


@functools.lru_cache(None)
def panel():
    p = rrect(W, H, 48, th["bg"]); rgb = p[..., :3].copy()
    for x in range(0, W + 1, 72): cv2.line(rgb, (x, 0), (x, H), th["grid"], 2)
    for y in range(0, H + 1, 72): cv2.line(rgb, (0, y), (W, y), th["grid"], 2)
    return np.concatenate([rgb, p[..., 3:4]], 2)


@functools.lru_cache(None)
def row_bg(blue):
    if blue: return rrect(RW, RH, 30, BLUE)
    return rrect(RW, RH, 30, (255, 255, 255), th["line"], 2)


@functools.lru_cache(None)
def row_tile(name, blue):
    b = rrect(78, 78, 22, (61, 132, 255) if blue else th["surf"], None if blue else th["line"], 0 if blue else 2)
    rgb = b[..., :3].copy()
    blit(rgb, icon(name, 46, "on-dark" if blue else th["icon"]), 16, 16)
    return np.concatenate([rgb, b[..., 3:4]], 2)


@functools.lru_cache(None)
def row_title(text, blue): return text_sprite(text, 46, "ExtraBold", OFF if blue else th["text"])


@functools.lru_cache(None)
def row_sub(text, blue): return text_sprite(text, 28, "SemiBold", (214, 228, 255) if blue else th["muted"])


@functools.lru_cache(None)
def mini_toggle(on, blue):
    if on:
        t = rrect(64, 36, 18, OFF if blue else BLUE)
        rgb = t[..., :3].copy(); k = rrect(26, 26, 9, BLUE if blue else OFF); blit(rgb, k, 33, 5)
    else:
        t = rrect(64, 36, 18, (61, 132, 255) if blue else th["surf"], OFF if blue else th["muted"], 2)
        rgb = t[..., :3].copy(); k = rrect(26, 26, 9, OFF if blue else th["muted"]); blit(rgb, k, 5, 5)
    return np.concatenate([rgb, t[..., 3:4]], 2)


def draw_row(fr, k, t, off, alpha):
    name, title, sub, w_in, w_title, w_sub, w_tg = ITEMS[k]
    t_in = T_IN[k]
    a_in = prog(t, t_in, 0.4)
    if a_in <= 0: return
    # синяя, пока о ней говорят; при появлении следующей строки — белая
    b = 1.0 if k == len(ITEMS) - 1 else 1 - ss(prog(t, T_IN[k + 1], 0.3))
    a = min(1, a_in * 3) * alpha
    x = M; y = RY0 + k * (RH + RGAP) + off + 24 * (1 - eout(a_in))
    for blue, w_ in ((False, 1 - b), (True, b)):
        if w_ <= 0.01: continue
        aa = a * w_
        blit(fr, row_bg(blue), x, y, alpha=aa)
        blit(fr, row_tile(name, blue), x + 22, y + (RH - 78) / 2, alpha=aa)
        has_sub = prog(t, E.wt(w_sub) - 0.05, 0.3)
        ttl = row_title(title, blue)
        ty_c = y + (RH - ttl.shape[0]) / 2 - 2                       # заголовок по центру строки
        ty_s = y + 18                                                  # заголовок над подписью
        ty = lerp(ty_c, ty_s, eout(has_sub))
        pt = prog(t, E.wt(w_title) - 0.08, 0.3)
        if pt > 0: blit(fr, ttl, x + 124, ty + 10 * (1 - eout(pt)), alpha=aa * min(1, pt * 3))
        if has_sub > 0:
            sp = row_sub(sub, blue)
            blit(fr, sp, x + 126, y + 72 + 8 * (1 - eout(has_sub)), alpha=aa * min(1, has_sub * 3))
        on = prog(t, E.wt(w_tg) + 0.05, 0.12) > 0.5
        blit(fr, mini_toggle(on, blue), x + RW - 24 - 64, y + (RH - 36) / 2, alpha=aa)


@functools.lru_cache(None)
def shade():
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
            if wd[-1] in ".?:—" or j == len(E.WORDS) - 1: CAP_CHUNKS.append(cur); cur = []; w = 0
    for ci, ch in enumerate(CAP_CHUNKS):
        t0 = E.wt(ch[0]); t1 = E.wt(CAP_CHUNKS[ci + 1][0]) if ci + 1 < len(CAP_CHUNKS) else E.DUR + 1
        if not (t0 - 0.03 <= t < t1 - 0.03): continue
        cur = max([j for j in ch if E.wt(j) <= t + 0.03] or [ch[0]])
        sp = [cap_soft(E.WORDS[j][0], j <= cur) for j in ch]
        tw = sum(s_.shape[1] for s_ in sp) + 12 * (len(sp) - 1); x = W / 2 - tw / 2
        p = eout(prog(t, t0 - 0.03, 0.14))
        for s_ in sp: blit(fr, s_, x, y + 8 * (1 - p), alpha=p); x += s_.shape[1] + 12


@functools.lru_cache(None)
def fit_bar(text, blue, size=64):
    while True:
        b = bar(text, THEME, size=size, blue=blue)
        if b.shape[1] <= CW or size <= 36: return b
        size -= 2


def bars(fr, t, items, t_out, size=64):
    y = 340
    for text, blue, tin in items:
        b = fit_bar(text, blue, size)
        a, o = appear(t, tin, 0.35, t_out, 0.15)
        blit(fr, b, W / 2 - b.shape[1] / 2, y + 24 * o, alpha=a)
        y += b.shape[0] + 14


def render(i, t, src):
    s = split_state(t)
    if s <= 0.001:
        fr = speaker_frame(src, i, lambda f: camera(f, z_full(t), 540, 870))
    else:
        pb = lerp(0, PB, s)
        # наезды на подписях пунктов, чтобы между строками кадр не стоял
        z = lerp(1.14, 1.22 + 0.04 * ss(prog(t, S[1], S[10] - S[1])) + push(t, E.wt(15) - 0.05, 0.03)
                 + push(t, E.wt(24) - 0.05, 0.03) + push(t, E.wt(30) - 0.05, 0.03), s)
        rt = int(max(0, pb - 50)); rh = H - rt
        fr = np.empty((H, W, 3), np.uint8); fr[:] = th["bg"]
        fr[rt:] = speaker_frame(src, i, lambda f: camera(f, z, 540, lerp(870, 1190, s) - rt, W, rh))
        blit(fr, panel(), 0, pb - H + 1)
        off = pb - PB
        cp = caps("ЗАЧЕМ АВТОМАТИЗИРОВАТЬ", THEME); a, o = appear(t, S[1] + 0.15, 0.32)
        blit(fr, cp, W / 2 - cp.shape[1] / 2, 360 + off + 12 * o, alpha=a)
        for k in range(len(ITEMS)): draw_row(fr, k, t, off, 1.0)
    if s < 0.5:
        if t < S[1]:
            bars(fr, t, [("Зачем бизнесу", False, E.wt(0) - 0.05),
                         ("автоматизировать", True, E.wt(2) - 0.1),
                         ("процессы в 2026 году?", True, E.wt(3) - 0.1)], S[1] - 0.2, size=60)
        elif t >= S[10]:
            bars(fr, t, [("Напишите в директ", False, E.wt(35) - 0.1), ("«АУДИТ»", True, E.wt(36) - 0.1)], None, size=72)
    fr = (fr.astype(np.float32) * (1 - shade())).astype(np.uint8)
    soft_captions(fr, t)
    return fr


sfx = [("sfx-pop.mp3", max(0.05, E.wt(0) - 0.05), 0.14), ("sfx-pop.mp3", E.wt(3) - 0.1, 0.16),
       ("sfx-click.mp3", S[1], 0.2)] + \
      [("sfx-pop.mp3", T_IN[k], 0.16) for k in range(len(ITEMS))] + \
      [("sfx-click.mp3", E.wt(it[6]) + 0.05, 0.3) for it in ITEMS] + \
      [("sfx-pop.mp3", E.wt(35) - 0.1, 0.14), ("sfx-pop.mp3", E.wt(36) - 0.1, 0.18)]

if __name__ == "__main__":
    os.makedirs(f"{WORK}/out", exist_ok=True)
    encode_story(f"{WORK}/out/reel_r011_why_{THEME}.mp4", render, sfx)
