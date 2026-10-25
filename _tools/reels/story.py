"""Story graphics synced to the transcript. Layout rule: 72 px side margins, everything centred
or spanning the full 936 px content width; content stays inside the Reels safe zone (y 300..1250)."""
from reel import *
import edit as E

M = 160; CW = W - 2 * M          # symmetric margins = width of the Reels like/comment rail
SAFE_TOP = 340            # Instagram header covers ~330 px
CAP_W = 560               # captions live in the lower half: keep clear of the like/comment rail


THEMES = {
    "dark": dict(bg=GRAPH, surf=SURF, line=LINE, text=OFF, muted=MUTED, plate=GRAPH, plate_text=OFF,
                 grid=(28, 31, 35), icon="on-dark", logo_main=OFF),
    "light": dict(bg=OFF, surf=(234, 232, 226), line=(213, 210, 202), text=GRAPH, muted=(95, 100, 107),
                  plate=OFF, plate_text=GRAPH, grid=(232, 230, 224), icon="on-light", logo_main=GRAPH),
}


# ---------- frame source with small cache (reads forward only) ----------
class Source:
    def __init__(self, path=f"{WORK}/src.mp4"):
        self.p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                  stdout=subprocess.PIPE, bufsize=10 ** 8)
        self.n = SRC_W * SRC_H * 3; self.next = 0; self.cache = {}

    def get(self, f):
        while self.next <= f:
            b = self.p.stdout.read(self.n)
            if len(b) < self.n: break
            self.cache[self.next] = np.frombuffer(b, np.uint8).reshape(SRC_H, SRC_W, 3); self.next += 1
            keep = {E.FR[j][1] + d for j in range(len(E.FR)) for d in range(3)}
            for old in [k for k in self.cache if k < self.next - 70 and k not in keep]: del self.cache[old]
        return self.cache[min(f, self.next - 1)]


def speaker_frame(src, i, cam):
    """Source frame for output i, with a 2-frame dissolve after each cut to hide micro jumps.
    cam(frame) -> rendered region."""
    f, k = E.src_frame(i)
    img = cam(src.get(f))
    d = i - E.OUT_START[k]
    if k > 0 and d < 2:
        prev_end = E.FR[k - 1][1]
        a = (d + 1) / 3.0
        img2 = cam(src.get(prev_end + d))
        img = (img.astype(np.float32) * a + img2.astype(np.float32) * (1 - a)).astype(np.uint8)
    return img


def encode_story(out, render, sfx, captions=None):
    audio = E.build_audio()
    ins = ["-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", audio]
    fl = []; labs = []
    for j, (f, t, v) in enumerate(sfx):
        ins += ["-i", f"{K}/11_MOTION/{f}"]; ms = int(t * 1000)
        fl.append(f"[{j + 2}:a]aformat=sample_rates=48000:channel_layouts=stereo,volume={v},adelay={ms}|{ms}[s{j}]")
        labs.append(f"[s{j}]")
    fl.append(f"[1:a]{''.join(labs)}amix=inputs={1 + len(labs)}:normalize=0:duration=first,alimiter=limit=0.95[a]")
    cmd = ["ffmpeg", "-v", "error", "-y", *ins, "-filter_complex", ";".join(fl), "-map", "0:v", "-map", "[a]",
           "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-profile:v", "high", "-pix_fmt", "yuv420p",
           "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE); src = Source()
    for i in range(E.NFRAMES):
        p.stdin.write(np.ascontiguousarray(render(i, i / FPS, src), np.uint8).tobytes())
    p.stdin.close(); p.wait(); print("done", out)


# ---------- animation helper ----------
def appear(t, t0, d=0.32, t1=None, d1=0.22):
    """(alpha, offset01) for an element that enters at t0 and leaves at t1."""
    p = eout(prog(t, t0, d)); q = ein(prog(t, t1, d1)) if t1 is not None else 0.0
    return p * (1 - q), (1 - p) + q


# ---------- sprites ----------
@functools.lru_cache(None)
def name_plate(theme):
    th = THEMES[theme]
    tile = 92
    name = text_sprite("Иван", 56, "Bold", th["plate_text"])
    role = text_sprite("Креативный директор", 32, "Medium", th["muted"])
    h = 24 + name.shape[0] - 8 + role.shape[0] + 18
    w = 26 + tile + 24 + max(name.shape[1], role.shape[1]) + 34
    bg = rrect(w, h, 30, th["plate"] + (240,))
    rgb = bg[..., :3].copy()
    t = rrect(tile, tile, 24, BLUE); blit(rgb, t, 26, (h - tile) / 2)
    blit(rgb, logo(56, OFF, OFF), 26 + tile / 2, h / 2, anchor="c")          # original mark
    blit(rgb, name, 26 + tile + 24, 18); blit(rgb, role, 26 + tile + 24, 18 + name.shape[0] - 8)
    return np.concatenate([rgb, bg[..., 3:4]], 2)


@functools.lru_cache(None)
def bar(text, theme, size=64, blue=False):
    th = THEMES[theme]
    if blue: return plate(text, size, "Bold", fg=OFF, bg=BLUE)
    return plate(text, size, "Bold", fg=th["plate_text"], bg=th["plate"])


@functools.lru_cache(None)
def word_sprite(text, size, color, weight="ExtraBold"):
    return text_sprite(text, size, weight, color)


def stack_centered(fr, items, y, t, gap=14, cx=W / 2):
    """items: list of (sprite, t_in, t_out). Each centred on cx."""
    for spr, t0, t1 in items:
        a, o = appear(t, t0, 0.3, t1, 0.2)
        blit(fr, spr, cx - spr.shape[1] / 2, y + 26 * o, alpha=a)
        y += spr.shape[0] + gap
    return y


# ---------- process tiles scene ----------
PROC = [("reports", "Отчёты"), ("tasks", "Документы"), ("sales", "КП"), ("money", "Расчёты")]
TILE = 150; TGAP = (CW - 4 * TILE - 2 * 22) // 3


def tile_x(k): return M + 22 + k * (TILE + TGAP)


@functools.lru_cache(None)
def proc_tile(k, theme, manual=False):
    th = THEMES[theme]
    b = rrect(TILE, TILE, 40, th["surf"], th["line"], 2)
    rgb = b[..., :3].copy()
    blit(rgb, icon(PROC[k][0], 78, th["icon"]), TILE / 2, TILE / 2, anchor="c")
    return np.concatenate([rgb, b[..., 3:4]], 2)


@functools.lru_cache(None)
def proc_label(k, theme): return text_sprite(PROC[k][1], 30, "SemiBold", THEMES[theme]["text"])


@functools.lru_cache(None)
def manual_chip(theme):
    th = THEMES[theme]
    w, h = 148, 46
    b = rrect(w, h, 23, th["bg"], th["muted"], 2); rgb = b[..., :3].copy()
    # mini toggle (off)
    tg = rrect(38, 22, 11, th["surf"], th["muted"], 2); blit(rgb, tg, 13, 12)
    k = rrect(14, 14, 5, th["muted"]); blit(rgb, k, 17, 16)
    tx = text_sprite("ручной", 24, "Bold", th["muted"]); blit(rgb, tx, 60, (h - tx.shape[0]) / 2 - 1)
    return np.concatenate([rgb, b[..., 3:4]], 2)


@functools.lru_cache(None)
def dashed_frame(w, h, theme):
    th = THEMES[theme]
    im = np.zeros((h, w, 4), np.uint8)
    r = 36; col = th["muted"] + (255,)
    # dashed rounded rect: sample the outline and draw dashes
    pts = []
    def arc(cx, cy, a0, a1):
        for a in np.linspace(a0, a1, 24): pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    arc(w - r - 2, r + 2, -math.pi / 2, 0); pts.append((w - 2, h - r - 2))
    arc(w - r - 2, h - r - 2, 0, math.pi / 2); pts.append((r + 2, h - 2))
    arc(r + 2, h - r - 2, math.pi / 2, math.pi); pts.append((2, r + 2))
    arc(r + 2, r + 2, math.pi, 1.5 * math.pi); pts.append((w - r - 2, 2))
    # resample by length
    P = np.array(pts); seg = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    L = seg[-1]; dash, gap = 14, 10; s = 0.0
    while s < L:
        e = min(L, s + dash)
        a = np.array([np.interp(s, seg, P[:, 0]), np.interp(s, seg, P[:, 1])])
        b = np.array([np.interp(e, seg, P[:, 0]), np.interp(e, seg, P[:, 1])])
        cv2.line(im, tuple((a * 4).astype(int)), tuple((b * 4).astype(int)), col, 2, cv2.LINE_AA, shift=2)
        s += dash + gap
    return im


@functools.lru_cache(None)
def caps(text, theme, color=None): return text_sprite(text, 28, "Bold", color or THEMES[theme]["muted"])


@functools.lru_cache(None)
def big_line(text, theme, size=74, blue=False):
    if blue: return plate(text, size, "ExtraBold", fg=OFF, bg=BLUE, padx=26, pady=10, r=22)
    return text_sprite(text, size, "ExtraBold", THEMES[theme]["text"])


def slogan(fr, t, theme, y, t_out=99):
    """'Наш слоган: Сначала процесс, потом технология' — words land exactly when spoken."""
    th = THEMES[theme]
    fo = 1 - ein(prog(t, t_out, 0.2))
    if fo <= 0: return
    a, o = appear(t, E.wt(23) - 0.05); a *= fo
    cp = caps("НАШ СЛОГАН", theme); blit(fr, cp, W / 2 - cp.shape[1] / 2, y + 16 * o, alpha=a)
    y1 = y + 60
    w1 = big_line("Сначала", theme); w2 = big_line("процесс,", theme)
    w3 = big_line("потом", theme); w4 = big_line("технология", theme, blue=True)
    sp = 26
    def row(words, yy, hrow):
        # the row re-centres smoothly as each word lands, so the line is always balanced
        vis = [eout(prog(t, ti - 0.04, 0.3)) for _, ti in words]
        widths = [s_.shape[1] for s_, _ in words]
        cur = widths[0] * (vis[0] > 0) + sum((sp + widths[j]) * vis[j] for j in range(1, len(words)))
        x = W / 2 - cur / 2
        for j, (spr, ti) in enumerate(words):
            p = eback(prog(t, ti - 0.04, 0.32))
            if p > 0:
                blit(fr, spr, x + spr.shape[1] / 2, yy + hrow / 2, alpha=fo * min(1, prog(t, ti - 0.04, 0.12)),
                     scale=0.85 + 0.15 * p, anchor="c")
            x += (spr.shape[1] + sp) * (vis[j] if j else 1)
    h1 = w1.shape[0]; h2 = w4.shape[0]
    row([(w1, E.wt(25)), (w2, E.wt(26))], y + 60, h1)
    row([(w3, E.wt(27)), (w4, E.wt(28))], y + 60 + h1 + 18, h2)


def processes(fr, t, theme, y, t_end=99):
    """Header + dashed 'company' frame + four process tiles; then they get marked 'ручной'."""
    th = THEMES[theme]
    hdr1 = caps("ШАГ 1 · РАЗБИРАЕМ ПРОЦЕССЫ", theme, BLUE)
    hdr2 = text_sprite("Что делается вручную?", 46, "ExtraBold", th["text"])
    hdr0 = text_sprite("Процессы внутри компании", 46, "ExtraBold", th["text"])
    a, o = appear(t, E.seg_t(10))
    blit(fr, hdr1, W / 2 - hdr1.shape[1] / 2, y + 14 * o, alpha=a)
    sw = prog(t, E.wt(39) - 0.05, 0.3)             # header swap at 'что находится'
    a0, o0 = appear(t, E.wt(31), 0.3)
    blit(fr, hdr0, W / 2 - hdr0.shape[1] / 2, y + 46 + 20 * o0 - 20 * eout(sw), alpha=a0 * (1 - eout(sw)))
    if sw > 0: blit(fr, hdr2, W / 2 - hdr2.shape[1] / 2, y + 46 + 20 * (1 - eout(sw)), alpha=eout(sw))
    fy = y + 125; fh = TILE + 172
    fa = eout(prog(t, E.wt(34) - 0.1, 0.4))
    blit(fr, dashed_frame(CW, fh, theme), M, fy, alpha=fa)
    for k in range(4):
        tk = E.wt(34) + 0.1 + 0.16 * k
        p = prog(t, tk, 0.36)
        if p <= 0: continue
        cx = tile_x(k) + TILE / 2; cy = fy + 24 + TILE / 2
        blit(fr, proc_tile(k, theme), cx, cy, alpha=min(1, p * 3), scale=0.6 + 0.4 * eback(p), anchor="c")
        lb = proc_label(k, theme)
        blit(fr, lb, cx - lb.shape[1] / 2, fy + 24 + TILE + 12, alpha=eout(prog(t, tk + 0.1, 0.3)))
        pm = prog(t, E.wt(42) + 0.1 * k, 0.3)            # 'ручном' -> chips
        if pm > 0:
            ch = manual_chip(theme)
            blit(fr, ch, cx, fy + 28 + TILE + 74, alpha=min(1, pm * 2), scale=0.7 + 0.3 * eback(pm), anchor="c")
    # 'менеджеры' -> person chip, centred under the frame
    pm = prog(t, E.wt(45) - 0.05, 0.35)
    if pm > 0:
        mg = manager_chip(theme)
        blit(fr, mg, W / 2, fy + fh + 2, alpha=min(1, pm * 2), scale=0.8 + 0.2 * eback(pm), anchor="c")
    return fy + fh


@functools.lru_cache(None)
def manager_chip(theme):
    th = THEMES[theme]
    tx = text_sprite("Менеджеры делают вручную", 28, "Bold", th["text"])
    w = 30 + 44 + 14 + tx.shape[1] + 30; h = 72
    b = rrect(w, h, 36, th["surf"], th["line"], 2); rgb = b[..., :3].copy()
    blit(rgb, icon("team", 44, th["icon"]), 30, (h - 44) / 2)
    blit(rgb, tx, 30 + 44 + 14, (h - tx.shape[0]) / 2 - 2)
    return np.concatenate([rgb, b[..., 3:4]], 2)


# ---------- captions (karaoke, current word on a blue plate) ----------
def caption_chunks():
    """Greedy by rendered width so a line never reaches the right-hand rail."""
    chunks = []; cur = []; width = 0
    for j, (w, t) in enumerate(E.WORDS):
        ww = cap_word(w, True).shape[1]
        if cur and width + 4 + ww > CAP_W:
            chunks.append(cur); cur = []; width = 0
        cur.append(j); width += (4 if len(cur) > 1 else 0) + ww
        if w[-1] in ".,?:" or j == len(E.WORDS) - 1:
            chunks.append(cur); cur = []; width = 0
    return chunks




@functools.lru_cache(None)
def cap_word(text, active):
    if active: return plate(text, 52, "ExtraBold", fg=OFF, bg=BLUE, padx=14, pady=6, r=14)
    s = text_sprite(text, 52, "ExtraBold", OFF)
    # soft shadow for legibility on video
    a = s[..., 3].astype(np.float32)
    sh = cv2.GaussianBlur(a, (0, 0), 6) * 0.55
    pad = np.zeros((s.shape[0] + 24, s.shape[1] + 24, 4), np.float32)
    pad[12:-12, 12:-12, :3] = s[..., :3]; pad[12:-12, 12:-12, 3] = a
    shadow = np.zeros_like(pad); shadow[..., 3] = cv2.GaussianBlur(np.pad(a, 12), (0, 0), 7) * 0.6
    outa = pad[..., 3:4] / 255 + shadow[..., 3:4] / 255 * (1 - pad[..., 3:4] / 255)
    rgb = pad[..., :3] * (pad[..., 3:4] / 255) / np.maximum(outa, 1e-6)
    return np.concatenate([rgb, outa * 255], 2).clip(0, 255).astype(np.uint8)


CHUNKS = None


def captions(fr, t, y):
    global CHUNKS
    if CHUNKS is None: CHUNKS = caption_chunks()
    for ci, ch in enumerate(CHUNKS):
        t0 = E.wt(ch[0]); t1 = E.wt(CHUNKS[ci + 1][0]) if ci + 1 < len(CHUNKS) else E.DUR + 1
        if not (t0 - 0.02 <= t < t1 - 0.02): continue
        cur = max([j for j in ch if E.wt(j) <= t + 0.02] or [ch[0]])
        sprs = [cap_word(E.WORDS[j][0], j == cur) for j in ch]
        gap = 4; tw = sum(s.shape[1] for s in sprs) + gap * (len(sprs) - 1)
        x = W / 2 - tw / 2
        p = eout(prog(t, t0 - 0.02, 0.16))
        hmax = max(s.shape[0] for s in sprs)
        for s in sprs:
            blit(fr, s, x, y + (hmax - s.shape[0]) / 2 + 14 * (1 - p), alpha=p); x += s.shape[1] + gap
