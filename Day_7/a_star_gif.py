"""GIF of the search in a_star_plot.py: Dijkstra (left) and A* (right) expand
the grid step by step. Top: the map seen from above. Bottom: the same cells as
3D bars, bar height = cost g of the cheapest way from S found so far."""
import heapq, math
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LightSource, Normalize
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

# --- same map and search as a_star_plot.py ---
G = np.zeros((30, 40), bool)  # True = obstacle, 10 cm cells
G[[0, -1]] = G[:, [0, -1]] = G[4:27, 20] = True  # border walls, inner wall
S, T = (15, 5), (15, 35)  # start, target as (row, column)
N8 = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b]


def plan(h):
    """plan() from a_star_plot.py, plus a log with one entry per heap pop:
    (n, [(m, cost, n), ...] for every neighbour m whose way got cheaper)."""
    g, parent, todo = {S: 0.0}, {S: None}, [(h(S), S)]
    log = []
    while todo:
        _, n = heapq.heappop(todo)
        improved = []
        log.append((n, improved))
        if n == T: break
        for a, b in N8:
            m = (n[0] + a, n[1] + b)
            cost = g[n] + math.hypot(a, b)
            if not G[m] and cost < g.get(m, math.inf):
                g[m], parent[m] = cost, n
                heapq.heappush(todo, (cost + h(m), m))
                improved.append((m, cost, n))
    return g, parent, log


def trace(parent, n):
    """Way back from n to S, as an array of (row, column), S first."""
    path = [n]
    while parent[path[-1]] is not None:
        path.append(parent[path[-1]])
    return np.array(path[::-1])


def snapshots(log, every):
    """Search state after every `every` expansions. A pop of a cell that was
    already expanded is a stale heap entry: it changes nothing, so skip it."""
    cost = np.full(G.shape, np.nan)  # NaN = not touched yet
    cost[S] = 0.0
    closed = np.zeros(G.shape, bool)  # expanded cells
    parent, shots, k = {S: None}, [], 0

    def shot(n, done):
        return cost.copy(), closed.copy(), trace(parent, n), k, done

    shots.append(shot(S, False))
    for n, improved in log:
        if closed[n]:
            continue
        closed[n] = True
        for m, c, p in improved:
            cost[m], parent[m] = c, p
        k += 1
        if n == T or k % every == 0:
            shots.append(shot(n, n == T))
    return shots


def animate(fname='a_star_search.gif', every=7, fps=8, hold=32):
    runs = [('Dijkstra  (h = 0)', plan(lambda m: 0)),
            ('A*  (h = straight line to T)', plan(lambda m: math.dist(m, T)))]
    shots = [snapshots(log, every) for _, (_, _, log) in runs]
    vmax = max(max(g.values()) for _, (g, _, _) in runs)
    cmap, norm = plt.get_cmap('viridis'), Normalize(0, vmax)
    inner = G.copy()  # only the inner wall is drawn in 3D
    inner[[0, -1]] = inner[:, [0, -1]] = False
    wall_h = 0.25 * vmax
    light = LightSource(azdeg=340, altdeg=45)  # from the front left, above

    def colors(cost, closed):
        """RGBA per cell: closed = cost colour, open list = paler, else white."""
        rgba = cmap(norm(np.nan_to_num(cost)))
        is_open = ~np.isnan(cost) & ~closed
        rgba[is_open, :3] = 0.45 * rgba[is_open, :3] + 0.55
        rgba[np.isnan(cost)] = 1.0
        rgba[G] = (0.25, 0.25, 0.25, 1.0)
        return rgba

    fig = plt.figure(figsize=(12, 10), dpi=80)
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 1.25], hspace=0.05,
                          wspace=0.08, left=0.04, right=0.9, top=0.92,
                          bottom=0.08)
    ax2 = [fig.add_subplot(gs[0, i]) for i in range(2)]
    ax3 = [fig.add_subplot(gs[1, i], projection='3d') for i in range(2)]
    fig.suptitle('Shortest path search: Dijkstra vs A*', fontsize=15)
    cax = fig.add_axes([0.92, 0.25, 0.015, 0.5])
    fig.colorbar(ScalarMappable(norm, cmap), cax=cax,
                 label='cost g from S  (1 per straight step, 1.41 diagonal)')
    fig.legend(handles=[
        Patch(color=cmap(0.6), label='expanded (closed)'),
        Patch(color=0.45 * np.array(cmap(0.6)[:3]) + 0.55,
              label='open list (waiting in heap)'),
        Patch(color=(0.25, 0.25, 0.25), label='wall'),
        Line2D([], [], color='tab:red', lw=1.2,
               label='best way to the cell being expanded'),
        Line2D([], [], color='tab:orange', lw=3, label='shortest path S → T')],
        loc='lower center', ncol=5, fontsize=9, frameon=False)

    ims, cur, best = [], [], []
    for ax in ax2:
        ims.append(ax.imshow(np.ones(G.shape + (4,)), interpolation='nearest'))
        cur.append(ax.plot([], [], '-', color='tab:red', lw=1.2)[0])
        best.append(ax.plot([], [], '.-', color='tab:orange', lw=3)[0])
        ax.plot(S[1], S[0], 'o', ms=9, mfc='limegreen', mec='k')
        ax.plot(T[1], T[0], '*', ms=15, mfc='tab:red', mec='k')
        ax.text(S[1], S[0] - 1.6, 'S', ha='center', fontweight='bold')
        ax.text(T[1], T[0] - 1.6, 'T', ha='center', fontweight='bold')
        ax.set_xlabel('column'); ax.set_ylabel('row')

    def frame(i):
        for j, (name, (g, _, _)) in enumerate(runs):
            cost, closed, path, k, done = shots[j][min(i, len(shots[j]) - 1)]
            rgba = colors(cost, closed)
            touched = (~np.isnan(cost)).sum()

            ims[j].set_data(rgba)
            cur[j].set_data(path[:, 1], path[:, 0])
            best[j].set_data(path[:, 1], path[:, 0]) if done else \
                best[j].set_data([], [])
            cur[j].set_visible(not done)
            status = f'done, cost {g[T]:.2f}' if done else 'searching'
            ax2[j].set_title(f'{name}\n{k:4d} expanded  {touched:4d} touched'
                             f'   {status}', family='monospace', fontsize=10)

            ax = ax3[j]
            ax.cla()
            ax.computed_zorder = False  # path line always on top of the bars
            sel = ~np.isnan(cost) | inner
            r, c = np.nonzero(sel)
            dz = np.where(inner[sel], wall_h, np.nan_to_num(cost[sel])) + 0.05
            ax.bar3d(c - 0.4, r - 0.4, 0, 0.8, 0.8, dz, color=rgba[sel],
                     shade=True, lightsource=light, zorder=1)
            x0, x1, y0, y1 = 0.5, G.shape[1] - 1.5, 0.5, G.shape[0] - 1.5
            ax.plot([x0, x1, x1, x0, x0], [y0, y0, y1, y1, y0], 0,
                    color='0.4', lw=1, zorder=0)  # inside of the border walls
            if done:
                ax.plot(path[:, 1], path[:, 0], cost[tuple(path.T)] + 0.3,
                        color='tab:orange', lw=3, zorder=5)
            ax.scatter(*S[::-1], 0.3, s=60, c='limegreen', ec='k', zorder=6)
            ax.scatter(*T[::-1], (g[T] if done else 0) + 0.3, s=150,
                       marker='*', c='tab:red', ec='k', zorder=6)
            ax.set_xlim(0, G.shape[1] - 1)
            ax.set_ylim(G.shape[0] - 1, 0)  # row 0 at the back, like the map
            ax.set_zlim(0, vmax)
            ax.set_box_aspect((G.shape[1], G.shape[0], 18), zoom=1.15)
            ax.view_init(elev=32, azim=-100)
            ax.set_xlabel('column'); ax.set_ylabel('row')
            ax.set_zlabel('cost g')
        return ()

    n = max(len(s) for s in shots)
    frames = list(range(n)) + [n - 1] * hold  # pause on the result
    ani = FuncAnimation(fig, frame, frames=frames, interval=1000 / fps)
    out = Path(__file__).with_name(fname)
    ani.save(out, writer='pillow', fps=fps)
    plt.close(fig)
    for name, (g, _, _) in runs:
        print(name, round(g[T], 2), len(g))  # path cost, touched cells
    print(f'saved {out}')


if __name__ == '__main__':
    animate()
