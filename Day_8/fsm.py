T = {  # (state, event): next state
    ("IDLE", "order"): "TO_PICKUP",
    ("TO_PICKUP", "arrived"): "LOADING",
    ("TO_PICKUP", "failed"): "TO_DOCK",
    ("LOADING", "loaded"): "TO_DROPOFF",
    ("LOADING", "timeout"): "TO_DOCK",
    ("TO_DROPOFF", "arrived"): "TO_DOCK",
    ("TO_DROPOFF", "failed"): "TO_DOCK",
    ("TO_DOCK", "arrived"): "IDLE",
}
def run(events, state="IDLE"):
    for e in events:
        nxt = T.get((state, e), state)  # no transition: stay
        print(f"{state:10} {e:8} -> {nxt}")
        state = nxt
    return state
run(["order", "arrived", "loaded", "battery", "arrived", "arrived"])
