import heapq, math  # heapq: priority queue, math: hypot, dist and inf
import numpy as np
G = np.zeros((30, 40), bool)  # map of 30 x 40 cells, 10 cm each, True = obstacle
G[[0, -1]] = G[:, [0, -1]] = G[4:27, 20] = True  # border walls, so no bounds check, and the inner wall
S, T = (15, 5), (15, 35)  # start and target, each as (row, column)
N8 = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b]  # the 8 steps, (0, 0) is left out
def plan(h):  # h is a function: h(m) guesses the remaining cost from cell m to T
    g = {S: 0.0}  # g[m]: cost of the cheapest way from S to m found so far
    parent = {S: None}  # parent[m]: the cell this cheapest way comes from
    todo = [(h(S), S)]  # open list, a heap of (f, cell) with f = g + h, smallest f on top
    while todo:
        _, n = heapq.heappop(todo)  # take the open cell n with the smallest f
        if n == T: break  # target taken off the heap: g[T] is the cost of the path
        for a, b in N8:  # visit all 8 neighbours m of n
            m = (n[0] + a, n[1] + b)
            cost = g[n] + math.hypot(a, b)  # way to m through n: step 1 straight, 1.41 diagonal
            if not G[m] and cost < g.get(m, math.inf):  # m is free and this way is cheaper
                g[m], parent[m] = cost, n  # remember the better way to m
                heapq.heappush(todo, (cost + h(m), m))  # m waits with f = g(m) + h(m)
    return g, parent  # costs of all touched cells and the way back to S
import matplotlib.pyplot as plt
def path_to(parent):  # walk the way back from T to S
    path = [T]
    while parent[path[-1]] is not None:  # only S has no parent
        path.append(parent[path[-1]])  # one cell back
    return path[::-1]  # reverse it: S first, T last
# a lambda is a short function: lambda m: 0 means h(m) = 0 for all m
dijkstra = plan(lambda m: 0)  # no guess, f = g: Dijkstra
astar = plan(lambda m: math.dist(m, T))  # straight line to T: A*
for name, (g, parent) in (('Dijkstra', dijkstra), ('A*', astar)):
    print(name, round(g[T], 2), len(g))  # path cost, touched cells
g, parent = astar  # plot the A* result
path = np.array(path_to(parent))  # one (row, column) per cell
rows, cols = np.array(list(g)).T  # all cells A* has touched
plt.imshow(G, cmap='Greys')  # walls black, free cells white
plt.plot(cols, rows, 's', color='lightsteelblue')  # touched
plt.plot(path[:, 1], path[:, 0], '.-', color='tab:orange', lw=3)
plt.title(f'A*: cost {g[T]:.2f}, {len(g)} cells touched')
plt.show()  # x is the column, y the row, row 0 at the top