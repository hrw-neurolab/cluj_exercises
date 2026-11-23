import heapq, math, numpy as np
G = np.zeros((30, 40), bool)  # True = obstacle, 10 cm cells
G[[0, -1]] = G[:, [0, -1]] = G[4:27, 20] = True  # walls
S, T = (15, 5), (15, 35)  # start, target
N8 = [(a, b) for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b]
def plan(h):
    g, parent, todo = {S: 0.0}, {S: None}, [(h(S), S)]
    while todo:
        _, n = heapq.heappop(todo)
        if n == T: break
        for a, b in N8:  # 8 neighbours
            m = (n[0] + a, n[1] + b)
            cost = g[n] + math.hypot(a, b)
            if not G[m] and cost < g.get(m, math.inf):
                g[m], parent[m] = cost, n
                heapq.heappush(todo, (cost + h(m), m))
    return round(g[T], 2), len(g)
print(plan(lambda m: 0), plan(lambda m: math.dist(m, T)))
