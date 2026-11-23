"""Part 1: the robot on the corridor, as plain Python functions.

The agent in llm_robot_agent.py runs these functions when the LLM asks for
them. The LLM never sees this code, only the descriptions in
tool_descriptions.py.
"""

# The corridor is a row of cells. Three of the cells are stations.
STATIONS = {"dock": 0, "pickup": 3, "dropoff": 8}
BATTERY_PER_CELL = 5  # driving one cell costs 5 % battery

# Everything the simulation knows about the robot.
state = {
    "position": 0,  # cell number, the robot starts at the dock
    "battery": 70,  # in %, too little for the whole trip (16 cells = 80 %)
    "loaded": False,  # is the box on the robot?
    "delivered": False,  # was the box handed over at the dropoff?
}


def is_at(station):
    return state["position"] == STATIONS[station]


def goto(station):
    """Drive cell by cell to the station. Stop early if the battery is empty."""
    target = STATIONS[station]
    direction = 1 if target > state["position"] else -1
    cells_to_drive = abs(target - state["position"])

    for _ in range(cells_to_drive):
        if state["battery"] < BATTERY_PER_CELL:
            return f"stopped at cell {state['position']}, battery empty"
        state["position"] += direction
        state["battery"] -= BATTERY_PER_CELL

    return f"at {station}, battery {state['battery']} %"


def load():
    """A person at the pickup puts the box on the robot."""
    if not is_at("pickup"):
        return "error: not at the pickup"
    state["loaded"] = True
    return "box loaded"


def unload():
    """Hand over the box at the dropoff."""
    if not is_at("dropoff") or not state["loaded"]:
        return "error: no box here"
    state["loaded"] = False
    state["delivered"] = True
    return "box delivered"


def charge():
    """Fill the battery. This only works at the dock."""
    if not is_at("dock"):
        return "error: not at the dock"
    state["battery"] = 100
    return "battery 100 %"


def status():
    """The whole robot state as text, so the LLM can read it."""
    return str(state)


# The LLM asks for a tool by its name. This table says which Python function
# runs for that name. The names must match CORRIDOR_TOOLS in
# tool_descriptions.py.
FUNCTIONS = {
    "goto": goto,
    "load": load,
    "unload": unload,
    "charge": charge,
    "status": status,
}
