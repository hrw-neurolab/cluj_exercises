S, F, R = "SUCCESS", "FAILURE", "RUNNING"
def node(stop, *kids):  # stop = S: Sequence, stop = F: Fallback
    def tick(w):
        for k in kids:
            if (s := k(w)) != stop: return s
        return stop
    return tick
seq, fb = (lambda *k: node(S, *k)), (lambda *k: node(F, *k))
def cond(test):  # Condition: SUCCESS or FAILURE, never RUNNING
    return lambda w: S if test(w) else F
def do(**change):  # instant Action: change the world, SUCCESS
    return lambda w: w.update(change) or S
def goto(x):  # Action: one cell per tick, RUNNING until there
    def tick(w):
        if w["pos"] == x: return S
        w["pos"] += 1 if x > w["pos"] else -1
        w["battery"] -= 5
        return R
    return tick
