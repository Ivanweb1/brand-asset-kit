"""Ролик «ИИ-агент отвечает на заявки» (аватар HeyGen, релиз «тестииаватара») — формат «До / После».

Копия шаблона before_after.py: сетка, панель, карточки, субтитры, тайминги анимаций те же,
поменяны тексты и привязки к словам E.wt(i). Слова и куски — $REEL_WORK/edit.json.

Сцены:
  куски 0–1   полный кадр, хук: «Заплатили за заявку» → «Клиент ушёл к конкуренту»
  куски 2     панель: «САМОЕ ОБИДНОЕ — дело может быть не в рекламе»
  куски 3–7   карточки: «ДО · ВРУЧНУЮ» (заявка, занят, не заметил, час, два) и пустая заготовка «клиент у конкурентов»
  кусок 8     крупный план: «Платите за привлечение — теряете из-за долгого ответа»
  кусок 9     панель: «ВСЁ ЭТО МОЖНО — автоматизировать» + тумблер ручной → авто
  куски 10–11 карточки: «ДО · ВРУЧНУЮ» / «ПОСЛЕ · ИИ-АГЕНТ» (заявка, ответ сразу, детали, менеджеру)
  куски 12–13 крупный план, призыв: «Напишите в директ» + «„заявка“»
"""
import os, sys
from story import *
from reel import _down

THEME = sys.argv[1] if len(sys.argv) > 1 else "light"
th = THEMES[THEME]
S = [E.seg_t(k) for k in range(len(E.FR))] + [E.DUR]
PB = 840
CWD, CH, CGAP = 370, 460, 20
LX, RX, CY0 = M, M + CWD + CGAP, 330
ROWS_L = [("leads", "Заявка", 20), ("team", "Занят", 26), ("notifications", "Не заметил", 30), ("time", "Час, два…", 33)]
ROWS_R = [("leads", "Заявка", 58), ("chatbot", "Ответ сразу", 59), ("tasks", "Детали", 63), ("team", "Менеджеру", 66)]
T_AGENT = E.wt(58)                    # «ИИ-агент»: тема уходит, карточки «до / после»


def open_state(t, t0):
    return ss(prog(t, t0, 0.5))


def split_state(t):
    if S[2] <= t < S[8]: return open_state(t, S[2])
    if S[9] <= t < S[12]: return open_state(t, S[9])
    return 0.0


def z_full(t):
    k = E.seg_of(int(t * FPS))
    if k <= 1: return 1.10 + 0.06 * (1 - eout(prog(t, 0, 0.8))) + 0.04 * ss(t / S[2])
    if k == 8: return 1.34 + 0.03 * prog(t, S[8], S[9] - S[8])
    return 1.34 + 0.03 * prog(t, S[12], E.DUR - S[12])


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
def fit_text(text, size, weight, color, maxw):
    while True:
        s_ = text_sprite(text, size, weight, color)
        if s_.shape[1] <= maxw or size <= 20: return s_
        size -= 1


@functools.lru_cache(None)
def row(name, label, blue):
    w, h = CWD - 40, 70
    b = rrect(w, h, 18, (61, 132, 255) if blue else (255, 255, 255), None if blue else th["line"], 0 if blue else 2)
    rgb = b[..., :3].copy()
    blit(rgb, icon(name, 40, "on-dark" if blue else th["icon"]), 16, 15)
    tx = fit_text(label, 28, "Bold", OFF if blue else th["text"], w - 70 - 90)
    blit(rgb, tx, 70, (h - tx.shape[0]) / 2 - 2)
    return np.concatenate([rgb, b[..., 3:4]], 2)


@functools.lru_cache(None)
def mini_toggle(on):
    t = rrect(56, 32, 16, OFF if on else th["surf"], None if on else th["muted"], 0 if on else 2)
    rgb = t[..., :3].copy()
    k = rrect(22, 22, 8, BLUE if on else th["muted"]); blit(rgb, k, 29 if on else 5, 5)
    return np.concatenate([rgb, t[..., 3:4]], 2)


@functools.lru_cache(None)
def lost_client():
    """Содержимое пустой заготовки «после», пока говорят про ручную работу: клиент ушёл к конкурентам."""
    ic = icon("clients", 86, th["icon"])
    return ic, [text_sprite(l, 34, "Bold", th["muted"]) for l in ("Клиент", "у конкурентов")]


@functools.lru_cache(None)
def toggle_plain(p):
    """Фирменный тумблер «РЕЖИМ ручной → авто» без нижней подписи (её нет в речи)."""
    S_ = SS; w, h = 640, 196
    im = Image.new("RGBA", (w * S_, h * S_), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w * S_ - 1, h * S_ - 1], 30 * S_, fill=GRAPH + (238,))
    tw, th_, tx, ty = 220, 116, 52, 40
    col = tuple(int(lerp(a, b, p)) for a, b in zip(SURF, BLUE))
    d.rounded_rectangle([tx * S_, ty * S_, (tx + tw) * S_, (ty + th_) * S_], 30 * S_, fill=col + (255,),
                        outline=(tuple(int(lerp(a, b, p)) for a, b in zip((90, 95, 102), BLUE)) + (255,)), width=3 * S_)
    kw = 84; kx = lerp(tx + 16, tx + tw - 16 - kw, p); ky = ty + (th_ - kw) / 2
    kc = tuple(int(lerp(a, b, p)) for a, b in zip((154, 158, 164), OFF))
    d.rounded_rectangle([kx * S_, ky * S_, (kx + kw) * S_, (ky + kw) * S_], 20 * S_, fill=kc + (255,))
    d.text(((tx + tw + 50) * S_, (ty + 8) * S_), "РЕЖИМ", font=font("Bold", 30 * S_), fill=MUTED + (255,))
    word = "ручной" if p < 0.5 else "авто"
    d.text(((tx + tw + 48) * S_, (ty + 40) * S_), word, font=font("Bold", 64 * S_),
           fill=(OFF if p < 0.5 else (120, 170, 255)) + (255,))
    return np.array(_down(im))


def cards(fr, t, off, phase):
    """phase 1 — разговор о ручной работе (правая карточка пустая), phase 2 — ИИ-агент (правая синяя)."""
    t0 = E.wt(19) - 0.1 if phase == 1 else T_AGENT - 0.1
    a_in = prog(t, t0, 0.4)
    if a_in <= 0: return
    y = CY0 + off + 30 * (1 - eout(a_in)); a = min(1, a_in * 3)
    # левая карточка: «ДО · ВРУЧНУЮ»
    blit(fr, card(False), LX, y, alpha=a)
    h = card_head("ДО · ВРУЧНУЮ", False); blit(fr, h, LX + CWD / 2 - h.shape[1] / 2, y + 36, alpha=a)
    for k, (ic, lb, wi) in enumerate(ROWS_L):
        tk = E.wt(wi) - 0.05 if phase == 1 else t0 + 0.08 * k
        pr = prog(t, tk, 0.32)
        if pr <= 0: continue
        ry = y + 96 + k * 92
        blit(fr, row(ic, lb, False), LX + 20, ry + 10 * (1 - eout(pr)), alpha=a * min(1, pr * 3))
        blit(fr, mini_toggle(False), LX + CWD - 20 - 76, ry + 19, alpha=a * min(1, pr * 3))
    # правая карточка
    if phase == 1:
        blit(fr, dashed_frame(CWD, CH, THEME), RX, y, alpha=a)
        pl = prog(t, E.wt(36) - 0.05, 0.35)
        if pl > 0:
            ic, tx = lost_client()
            blit(fr, ic, RX + CWD / 2, y + 170, alpha=min(1, pl * 3), anchor="c", scale=0.8 + 0.2 * eback(pl))
            for n, ln in enumerate(tx):
                blit(fr, ln, RX + CWD / 2 - ln.shape[1] / 2, y + 236 + n * 42 + 12 * (1 - eout(pl)), alpha=min(1, pl * 3))
    else:
        fill = ss(prog(t, T_AGENT - 0.1, 0.4))
        blit(fr, dashed_frame(CWD, CH, THEME), RX, y, alpha=a * (1 - fill))
        blit(fr, card(True), RX, y, alpha=a * fill)
        h = card_head("ПОСЛЕ · ИИ-АГЕНТ", True); blit(fr, h, RX + CWD / 2 - h.shape[1] / 2, y + 36, alpha=a * fill)
        for k, (ic, lb, wi) in enumerate(ROWS_R):
            tk = E.wt(wi) + (0.2 if k == 0 else -0.05)
            pr = prog(t, tk, 0.32)
            if pr <= 0: continue
            ry = y + 96 + k * 92
            blit(fr, row(ic, lb, True), RX + 20, ry + 10 * (1 - eout(pr)), alpha=min(1, pr * 3))
            pt = prog(t, tk + 0.15, 0.25)
            if pt > 0: blit(fr, mini_toggle(True), RX + CWD - 20 - 76, ry + 19, alpha=min(1, pt * 3))
    pa = prog(t, (E.wt(36) if phase == 1 else T_AGENT) - 0.08, 0.35)
    if pa > 0:
        blit(fr, arrow_badge(), W / 2, CY0 + off + CH / 2, alpha=min(1, pa * 3), scale=0.6 + 0.4 * eback(pa), anchor="c")


@functools.lru_cache(None)
def arrow_badge():
    b = rrect(84, 84, 26, GRAPH); rgb = b[..., :3].copy()
    cv2.line(rgb, (24 * 4, 42 * 4), (58 * 4, 42 * 4), OFF, 5, cv2.LINE_AA, shift=2)
    cv2.polylines(rgb, [np.array([[46, 30], [60, 42], [46, 54]]) * 4], False, OFF, 5, cv2.LINE_AA, shift=2)
    return np.concatenate([rgb, b[..., 3:4]], 2)


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


def two_bars(fr, t, top, bottom, t_top, t_bot, t_out, size=64):
    y = 310
    for text, blue, tin in [(top, False, t_top), (bottom, True, t_bot)]:
        b = fit_bar(text, blue, size)
        a, o = appear(t, tin, 0.35, t_out, 0.15)
        blit(fr, b, W / 2 - b.shape[1] / 2, y + 24 * o, alpha=a)
        y += b.shape[0] + 14


def topic(fr, t, off, cap, lines, t_cap, t_lines, t_out, toggle_at=None):
    n = len(lines)
    block = 34 + 22 + n * 66 + (220 if toggle_at is not None else 0)
    y0 = SAFE_TOP + (PB - SAFE_TOP - block) / 2 + off            # по центру видимой части панели
    cp = caps(cap, THEME); a, o = appear(t, t_cap, 0.32, t_out, 0.2)
    blit(fr, cp, W / 2 - cp.shape[1] / 2, y0 + 12 * o, alpha=a)
    for n_, (ln, blue, tl) in enumerate(lines):
        ttl = text_sprite(ln, 58, "ExtraBold", BLUE if blue else th["text"])
        a, o = appear(t, t_lines if tl is None else tl, 0.32, t_out, 0.2)
        blit(fr, ttl, W / 2 - ttl.shape[1] / 2, y0 + 56 + n_ * 66 + 16 * o, alpha=a)
    if toggle_at is not None:
        tg = toggle_plain(round(ss(prog(t, toggle_at, 0.3)), 2))
        a, o = appear(t, t_cap + 0.1, 0.32, t_out, 0.2)
        blit(fr, tg, W / 2 - tg.shape[1] / 2, y0 + 56 + n * 66 + 24 + 20 * o, alpha=a)


def render(i, t, src):
    s = split_state(t)
    if s <= 0.001:
        fr = speaker_frame(src, i, lambda f: camera(f, z_full(t), 540, 870))
    else:
        pb = lerp(0, PB, s)
        t_in = S[2] if t < S[8] else S[9]
        t_end = S[8] if t < S[8] else S[12]
        z = lerp(1.14 if t < S[8] else 1.34, 1.22 + 0.04 * ss(prog(t, t_in, t_end - t_in)), s)
        rt = int(max(0, pb - 50)); rh = H - rt
        fr = np.empty((H, W, 3), np.uint8); fr[:] = th["bg"]
        fr[rt:] = speaker_frame(src, i, lambda f: camera(f, z, 540, lerp(870, 1190, s) - rt, W, rh))
        blit(fr, panel(), 0, pb - H + 1)
        off = pb - PB
        if t < S[8]:
            if t < S[3] + 0.3:
                topic(fr, t, off, "САМОЕ ОБИДНОЕ", [("Дело может быть", False, E.wt(12) - 0.1),
                                                    ("не в рекламе", True, E.wt(16) - 0.1)],
                      S[2] + 0.25, None, S[3] - 0.15)
            cards(fr, t, off, 1)
        else:
            if t < T_AGENT + 0.3:
                topic(fr, t, off, "ВСЁ ЭТО МОЖНО", [("Автоматизировать", False, E.wt(56) - 0.1)],
                      S[9] + 0.2, None, T_AGENT - 0.2, toggle_at=E.wt(57) + 0.25)
            cards(fr, t, off, 2)
    if s < 0.5:
        if t < S[2]:
            two_bars(fr, t, "Заплатили за заявку", "Клиент ушёл к конкуренту", E.wt(1) - 0.1, E.wt(5) - 0.1, S[2] - 0.2)
        elif S[8] <= t < S[9]:
            two_bars(fr, t, "Платите за привлечение", "Теряете из-за долгого ответа", E.wt(42) - 0.1, E.wt(48) - 0.1,
                     S[9] - 0.15, size=58)
        elif t >= S[12]:
            two_bars(fr, t, "Напишите в директ", "«Заявка»", E.wt(69) - 0.1, E.wt(72) - 0.1, None, size=72)
    fr = (fr.astype(np.float32) * (1 - shade())).astype(np.uint8)
    soft_captions(fr, t)
    return fr


sfx = [("sfx-pop.mp3", E.wt(1) - 0.1, 0.14), ("sfx-pop.mp3", E.wt(5) - 0.1, 0.16),
       ("sfx-click.mp3", S[2], 0.2), ("sfx-pop.mp3", E.wt(19) - 0.1, 0.16), ("sfx-pop.mp3", E.wt(36) - 0.08, 0.14),
       ("sfx-pop.mp3", E.wt(48) - 0.1, 0.14),
       ("sfx-click.mp3", S[9], 0.2), ("sfx-click.mp3", E.wt(57) + 0.25, 0.4), ("sfx-pop.mp3", T_AGENT - 0.1, 0.18)] + \
      [("sfx-click.mp3", E.wt(wi) + (0.35 if k == 0 else 0.1), 0.22) for k, (_, _, wi) in enumerate(ROWS_R)] + \
      [("sfx-pop.mp3", E.wt(69) - 0.1, 0.14), ("sfx-pop.mp3", E.wt(72) - 0.1, 0.18)]

if __name__ == "__main__":
    os.makedirs(f"{WORK}/out", exist_ok=True)
    encode_story(f"{WORK}/out/reel_ai_agent_{THEME}.mp4", render, sfx)
