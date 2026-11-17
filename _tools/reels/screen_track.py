"""Трекинг экрана монитора в видео с телефона (R055: «Грань» на мониторе IMG_7839).

1. Углы экрана в первом кадре: самая большая светлая область (экран светится), стороны уточняются
   прямыми по перепаду яркости «экран → чёрная рамка».
2. Движение камеры: точки на стене и рамке вокруг экрана (не внутри экрана, не ниже клавиатуры —
   там руки), каждая точка ищется заново от первого кадра (LK с подсказкой из прошлого кадра) — без
   накопления дрейфа. Гомография кадр0 → кадр t, углы = H · углы0, затем лёгкое сглаживание.

    python screen_track.py VIDEO.mp4 OUT.json [--debug DIR]
"""
import argparse, json, pathlib
import cv2, numpy as np


def screen_quad(fr):
    g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
    m = (g > 60).astype(np.uint8) * 255
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((9, 9), np.uint8))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    c = max(cs, key=cv2.contourArea)
    hull = cv2.convexHull(c)
    q = cv2.approxPolyDP(hull, 0.02 * cv2.arcLength(hull, True), True).reshape(-1, 2).astype(np.float32)
    if len(q) != 4:
        rect = cv2.minAreaRect(c); q = cv2.boxPoints(rect).astype(np.float32)
    s = q.sum(1); d = q[:, 0] - q[:, 1]
    q = np.float32([q[s.argmin()], q[d.argmax()], q[s.argmax()], q[d.argmin()]])   # TL TR BR BL
    return refine(g, q)


def refine(g, q, band=14):
    """Каждая сторона — прямая по точкам максимального перепада яркости поперёк стороны."""
    gx = cv2.Sobel(cv2.GaussianBlur(g, (3, 3), 0).astype(np.float32), cv2.CV_32F, 1, 0)
    gy = cv2.Sobel(cv2.GaussianBlur(g, (3, 3), 0).astype(np.float32), cv2.CV_32F, 0, 1)
    c = q.mean(0); lines = []
    for i in range(4):
        a, b = q[i], q[(i + 1) % 4]
        t = (b - a) / np.linalg.norm(b - a); n = np.float32([-t[1], t[0]])
        if np.dot(c - a, n) < 0: n = -n                       # нормаль внутрь экрана
        pts = []
        for u in np.linspace(0.08, 0.92, 60):
            p = a + (b - a) * u; best, bv = None, 0
            for k in np.arange(-band, band + 0.5, 0.5):
                x, y = p + n * k
                if not (1 <= x < g.shape[1] - 1 and 1 <= y < g.shape[0] - 1): continue
                v = gx[int(y), int(x)] * n[0] + gy[int(y), int(x)] * n[1]     # рост яркости внутрь
                if v > bv: bv, best = v, (x, y)
            if best is not None and bv > 40: pts.append(best)
        pts = np.float32(pts)
        vx, vy, x0, y0 = cv2.fitLine(pts, cv2.DIST_HUBER, 0, 0.01, 0.01).ravel()
        lines.append((np.float32([x0, y0]), np.float32([vx, vy])))
    out = []
    for i in range(4):                                          # угол = пересечение соседних сторон
        (p1, d1), (p2, d2) = lines[i - 1], lines[i]
        A = np.float32([[d1[0], -d2[0]], [d1[1], -d2[1]]]); s = np.linalg.solve(A, p2 - p1)
        out.append(p1 + d1 * s[0])
    return np.float32(out)


def track_edges(video, init, debug=None):
    """Каждый кадр: стороны экрана заново по перепаду «рамка → экран», старт — углы прошлого кадра."""
    cap = cv2.VideoCapture(str(video)); quads = []; q = np.float32(init); jumps = []
    while True:
        ok, fr = cap.read()
        if not ok: break
        g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
        try:
            nq = refine(g, q, band=10)
            jump = float(np.abs(nq - q).max())
            if quads and jump > 12: nq = q                     # выброс — держим прошлый
            jumps.append(jump)
        except Exception:
            nq = q
        q = nq; quads.append(q.copy())
    q = np.float32(quads)
    k = np.float32([1, 2, 3, 4, 3, 2, 1]); k /= k.sum()
    pad = np.concatenate([q[:1].repeat(3, 0), q, q[-1:].repeat(3, 0)])
    qs = sum(k[i] * pad[i:i + len(q)] for i in range(7))
    if debug: _debug(video, qs, debug)
    print(f"кадров {len(qs)}, шаг углов median {np.median(jumps):.2f} max {max(jumps):.2f} px; "
          f"сдвиг от кадра 0 max {float(np.abs(qs - qs[0]).max()):.1f} px")
    print("угол0:", np.round(qs[0], 1).tolist())
    return qs


def _debug(video, qs, debug):
    d = pathlib.Path(debug); d.mkdir(parents=True, exist_ok=True)
    cap = cv2.VideoCapture(str(video))
    for i in range(len(qs)):
        ok, fr = cap.read()
        if i % 30: continue
        cv2.polylines(fr, [np.round(qs[i] * 4).astype(np.int32)], True, (0, 0, 255), 1, cv2.LINE_AA, 2)
        for x, y in qs[i]:
            x, y = int(x), int(y); crop = fr[max(0, y - 40):y + 40, max(0, x - 40):x + 40]
        cv2.imwrite(str(d / f"t{i:04d}.jpg"), fr)


def track(video, debug=None):
    cap = cv2.VideoCapture(str(video)); ok, f0 = cap.read()
    q0 = screen_quad(f0)
    g0 = cv2.cvtColor(f0, cv2.COLOR_BGR2GRAY)
    mask = np.zeros_like(g0)
    big = q0.mean(0) + (q0 - q0.mean(0)) * 1.35
    cv2.fillPoly(mask, [big.astype(np.int32)], 255)
    cv2.fillPoly(mask, [(q0.mean(0) + (q0 - q0.mean(0)) * 0.985).astype(np.int32)], 0)   # без содержимого экрана
    ymax = int(max(q0[2, 1], q0[3, 1])) + 10
    mask[ymax:] = 0                                              # клавиатура и руки
    mask[: max(0, int(min(q0[0, 1], q0[1, 1])) - 420)] = 0
    p0 = cv2.goodFeaturesToTrack(g0, 600, 0.01, 8, mask=mask)
    prev = p0.copy(); quads = [q0.tolist()]; inl = []
    lk = dict(winSize=(31, 31), maxLevel=4, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 40, 0.01))
    while True:
        ok, fr = cap.read()
        if not ok: break
        g = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
        p1, st, _ = cv2.calcOpticalFlowPyrLK(g0, g, p0, prev.copy(), flags=cv2.OPTFLOW_USE_INITIAL_FLOW, **lk)
        good = st.ravel() == 1
        H, m = cv2.findHomography(p0[good], p1[good], cv2.RANSAC, 2.0)
        inl.append(int(m.sum()))
        prev = np.where(good[:, None, None], p1, prev)
        quads.append(cv2.perspectiveTransform(q0[None], H)[0].tolist())
    q = np.float32(quads)
    k = np.float32([1, 4, 6, 4, 1]); k /= k.sum()               # сглаживание дрожания трекинга
    pad = np.concatenate([q[:1].repeat(2, 0), q, q[-1:].repeat(2, 0)])
    qs = sum(k[i] * pad[i:i + len(q)] for i in range(5))
    if debug:
        d = pathlib.Path(debug); d.mkdir(parents=True, exist_ok=True)
        cap = cv2.VideoCapture(str(video))
        for i in range(len(qs)):
            ok, fr = cap.read()
            if i % 30: continue
            cv2.polylines(fr, [qs[i].astype(np.int32)], True, (0, 0, 255), 2)
            cv2.imwrite(str(d / f"t{i:04d}.jpg"), fr)
    print(f"кадров {len(qs)}, точек {len(p0)}, inliers min {min(inl)} / median {int(np.median(inl))}")
    print("угол0:", np.round(q0, 1).tolist())
    print("макс. сдвиг углов, px:", float(np.abs(qs - qs[0]).max()))
    return qs


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("out"); ap.add_argument("--debug")
    ap.add_argument("--init", help="углы первого кадра x,y×4: TL TR BR BL — трекинг по краям экрана")
    a = ap.parse_args()
    if a.init:
        v = [float(s) for s in a.init.split(",")]
        qs = track_edges(a.video, np.float32(v).reshape(4, 2), a.debug)
    else:
        qs = track(a.video, a.debug)
    pathlib.Path(a.out).write_text(json.dumps(np.round(qs, 3).tolist()))
