"""The tool descriptions the LLM reads, for part 1 and part 2.

SOLUTION of the battery task in INSTALL_day9.md: battery and charge are new
in NAV2_TOOLS.

The LLM never sees the Python functions in corridor_robot.py or nav2_robot.py.
It only sees these lists: the name, the description and the parameters of
every tool, in the JSON schema format of the OpenAI API. From the
descriptions it decides what to call and when.
"""

# Part 1: the corridor robot (functions in corridor_robot.py)
CORRIDOR_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "goto",
            "description": "Drive to a station. Costs 5 % battery per cell.",
            "parameters": {
                "type": "object",
                "properties": {
                    "station": {
                        "type": "string",
                        "enum": ["dock", "pickup", "dropoff"],  # only these
                    },
                },
                "required": ["station"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "load",
            "description": "Wait at the pickup until a person loads the box.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "unload",
            "description": "Hand over the box at the dropoff.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "charge",
            "description": "Charge the battery to 100 %. Only at the dock.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "status",
            "description": "Position, battery, loaded and delivered.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

# Part 2: the robot of delivery_bt with Nav2 (functions in nav2_robot.py)
NAV2_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "goto",
            "description": "Drive to a station with Nav2.",
            "parameters": {
                "type": "object",
                "properties": {
                    "station": {
                        "type": "string",
                        "enum": ["pickup", "dropoff", "dock"],  # only these
                    },
                },
                "required": ["station"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ask_human",
            "description": "Ask the person at the robot, e.g. to load or unload.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string"},
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "battery",
            "description": "Battery level in %.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "charge",
            "description": "Charge the battery to 100 %. Only at the dock. "
            "Returns when the battery is full.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]
