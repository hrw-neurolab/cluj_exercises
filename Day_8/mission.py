from bt import R, seq, fb, cond, do, goto
DOCK, PICKUP, DROPOFF = 0, 3, 8
mission = seq(
    fb(cond(lambda w: w["battery"] > 30), seq(goto(DOCK), do(battery=100))),
    fb(cond(lambda w: w["loaded"]), seq(goto(PICKUP), do(loaded=True))),
    fb(cond(lambda w: w["delivered"]), seq(goto(DROPOFF), do(delivered=True))),
    goto(DOCK),
)
w = dict(pos=0, battery=70, loaded=False, delivered=False)
route, status = "", R
while status == R:
    status = mission(w)
    route += str(w["pos"])
    print(w["battery"])
print(route, status, w["battery"])
