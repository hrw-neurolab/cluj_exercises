import numpy as np
W = np.zeros((40, 40), bool)  # true world, 10 cm cells
W[[0, -1]] = W[:, [0, -1]] = W[20, :25] = True  # walls
L = np.zeros(W.shape)  # log odds, 0 means unknown
for r0, c0 in [(6, 6), (6, 20), (6, 33), (20, 32), (33, 32)]:
    for a in np.linspace(0, 2 * np.pi, 180, endpoint=False):
        s = max(abs(np.sin(a)), abs(np.cos(a)))
        for k in range(1, int(30 * s)):  # 3 m beam
            r = round(r0 + k * np.sin(a) / s)
            c = round(c0 + k * np.cos(a) / s)
            if W[r, c]:
                L[r, c] += 0.85  # hit: occupied
                break
            L[r, c] -= 0.4  # beam passed: free
P = 1 - 1 / (1 + np.exp(L))  # log odds to probability
print((P > 0.65).sum(), (P < 0.25).sum(), (L == 0).sum())


# --- Plot, not on the slide: draw the map that the 16 lines above computed ---
def plot(P, L, poses=((6, 6), (6, 20), (6, 33), (20, 32), (33, 32))):
    """Show p(occupied) per cell: white free, black wall, grey 0.5 unknown."""
    import matplotlib.pyplot as plt
    plt.imshow(P, cmap='gray_r', vmin=0, vmax=1)  # row 0 at the top
    plt.colorbar(label='p(occupied)')
    rows, cols = zip(*poses)
    plt.plot(cols, rows, 'o--', color='tab:orange')  # x = column, y = row
    plt.title(f'{(P > 0.65).sum()} walls, {(P < 0.25).sum()} free, '
              f'{(L == 0).sum()} unknown')
    plt.show()


# --- GIF, not on the slide: same update, but the robot drives the route and
#     scans every 10 cm, so the map can be watched while it is being built ---
POSES = ((6, 6), (6, 20), (6, 33), (20, 32), (33, 32))


def scan(L, r0, c0):
    """One 360° scan from (r0, c0) into L, exactly as above; returns the
    beam end points as rows (r, c, hit)."""
    ends = []
    for a in np.linspace(0, 2 * np.pi, 180, endpoint=False):
        s = max(abs(np.sin(a)), abs(np.cos(a)))
        hit = False
        for k in range(1, int(30 * s)):  # 3 m beam
            r = round(r0 + k * np.sin(a) / s)
            c = round(c0 + k * np.cos(a) / s)
            if W[r, c]:
                L[r, c] += 0.85  # hit: occupied
                hit = True
                break
            L[r, c] -= 0.4  # beam passed: free
        ends.append((r, c, hit))
    return np.array(ends, float)


def drive(poses, step=1.0):
    """Robot positions every `step` cells along the polyline through poses."""
    pts = [np.array(poses[0], float)]
    for p, q in zip(poses[:-1], poses[1:]):
        p, q = np.array(p, float), np.array(q, float)
        n = int(np.ceil(np.hypot(*(q - p)) / step))
        pts += [p + (q - p) * i / n for i in range(1, n + 1)]
    return np.array(pts)


def animate(poses=POSES, fname='grid_map.gif', fps=6, hold=12):
    """Drive, scan, record the map after every scan and save it as a GIF."""
    from pathlib import Path
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation
    from matplotlib.patches import Polygon

    path = drive(poses)
    Lt = np.zeros(W.shape)  # fresh map, everything unknown
    hist = [(path[0], Lt.copy(), None)]  # frame 0: before the first scan
    for r0, c0 in path:
        ends = scan(Lt, r0, c0)
        hist.append(((r0, c0), Lt.copy(), ends))
    Ls = np.stack([h[1] for h in hist])
    Ps = 1 - 1 / (1 + np.exp(Ls))
    walls = (Ps > 0.65).sum((1, 2))
    free = (Ps < 0.25).sum((1, 2))
    unknown = (Ls == 0).sum((1, 2))
    seg = np.hypot(*np.diff(path, axis=0).T) * 0.1  # 10 cm cells -> m
    dist = np.r_[0, 0, np.cumsum(seg)]  # per frame, frame 0 = frame 1 = start
    n = len(path)

    fig, (axm, axn) = plt.subplots(1, 2, figsize=(11, 5), dpi=100,
                                   gridspec_kw={'width_ratios': [1, 1]})
    im = axm.imshow(Ps[0], cmap='gray_r', vmin=0, vmax=1)  # row 0 at the top
    fig.colorbar(im, ax=axm, label='p(occupied)', fraction=0.046, pad=0.03)
    axm.plot(path[:, 1], path[:, 0], ':', color='tab:orange', lw=1)  # route
    fan = axm.add_patch(Polygon(np.zeros((3, 2)), fc=(1, 0, 0, 0.04),
                                ec=(1, 0, 0, 0.5), lw=0.8))  # seen by this scan
    hits, = axm.plot([], [], '.', ms=4, color='tab:red', label='hits')
    trail, = axm.plot([], [], '-', color='tab:orange', lw=2, label='driven')
    bot, = axm.plot([], [], 'o', ms=9, mfc='tab:orange', mec='k')
    ticks = range(0, W.shape[0], 10)
    axm.set_xticks(ticks, [f'{t / 10:g}' for t in ticks])
    axm.set_yticks(ticks, [f'{t / 10:g}' for t in ticks])
    axm.set_xlabel('x [m]'); axm.set_ylabel('y [m]')
    axm.legend(loc='lower left', fontsize=8)

    axn.plot(dist, walls, color='k', label='wall  (p > 0.65)')
    axn.plot(dist, free, color='tab:blue', label='free  (p < 0.25)')
    axn.plot(dist, unknown, color='tab:gray', label='unknown  (L = 0)')
    cursor = axn.axvline(0, color='tab:red', lw=1.5)
    axn.set_xlim(0, dist[-1]); axn.set_ylim(0, W.size)
    axn.set_xlabel('distance driven [m]'); axn.set_ylabel('cells')
    axn.legend(loc='center right', fontsize=8)
    axn.grid(alpha=0.3)

    def frame(k):
        (r0, c0), _, ends = hist[k]
        i = max(k - 1, 0)  # index into path
        im.set_data(Ps[k])
        trail.set_data(path[:i + 1, 1], path[:i + 1, 0])
        bot.set_data([c0], [r0])
        if ends is None:
            fan.set_xy(np.zeros((3, 2)))
            hits.set_data([], [])
        else:
            fan.set_xy(ends[:, [1, 0]])
            hit = ends[:, 2] == 1
            hits.set_data(ends[hit, 1], ends[hit, 0])
        cursor.set_xdata([dist[k]] * 2)
        axm.set_title(f'Scan {k:2d}/{n}   s = {dist[k]:4.1f} m',
                      family='monospace')
        axn.set_title(f'{walls[k]:4d} wall  {free[k]:4d} free  '
                      f'{unknown[k]:4d} unknown', family='monospace')
        return ()

    frames = list(range(len(hist))) + [len(hist) - 1] * hold  # pause at end
    ani = FuncAnimation(fig, frame, frames=frames, interval=1000 / fps)
    fig.tight_layout()
    out = Path(__file__).with_name(fname)
    ani.save(out, writer='pillow', fps=fps, dpi=100)
    plt.close(fig)
    print(f'saved {out}')


animate()  # writes grid_map.gif next to this file
plot(P, L)
