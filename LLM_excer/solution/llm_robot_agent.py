"""Day 9: an LLM drives a delivery robot with tool calls.

SOLUTION of the battery task in INSTALL_day9.md: only NAV2_SYSTEM_PROMPT is
new in this file. Start it with: python3 solution/llm_robot_agent.py nav2

The idea: the LLM never moves the robot itself. It only answers "please call
tool X with arguments Y". Our Python code runs that function, sends the result
back, and asks again. This repeats until the LLM answers with plain text.

Part 1, corridor simulation (needs only Ollama and `pip install openai`):
    python3 llm_robot_agent.py

Part 2, the simulated robot of delivery_bt (day 8) with Nav2. Needs ROS 2,
see INSTALL_day9.md. First start the world in its own terminal, then the agent:
    ros2 launch delivery_bt delivery.launch.py world:=room
    python3 llm_robot_agent.py nav2

Files:
    llm_robot_agent.py    this file: LLM connection, agent loop, missions
    corridor_robot.py     part 1: what the corridor robot can do (Python)
    nav2_robot.py         part 2: what the Nav2 robot can do (Python + Nav2)
    tool_descriptions.py  what the LLM reads about these tools (JSON schema)
"""
import json
import sys
import time

from openai import OpenAI

import corridor_robot
from tool_descriptions import CORRIDOR_TOOLS, NAV2_TOOLS


# ============================================================================
# 1. Connection to the LLM
# ============================================================================
# Ollama runs locally and speaks the same API as OpenAI, so the openai package
# works with it. Ollama ignores the api_key, but the package needs one.
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
MODEL = "gemma4:12b"  # or "qwen3:8b", see INSTALL_day9.md
MAX_STEPS = 20  # safety limit, in case the LLM never finishes


# ============================================================================
# 2. The agent loop (the same for part 1 and part 2)
# ============================================================================
def call_tool(call, functions):
    """Run the Python function the LLM asked for. Return its result as text."""
    name = call.function.name  # e.g. "goto"
    arguments = json.loads(call.function.arguments or "{}")  # e.g. {"station": "pickup"}
    try:
        result = functions[name](**arguments)
    except Exception as error:  # unknown tool or wrong arguments: tell the LLM
        result = f"error: {error!r}"
    print(f"TOOL:     {name} {arguments} -> {result}")
    return result


def run_agent(system_prompt, task, tools, functions):
    """Let the LLM call tools until it answers with plain text (its report).

    tools:     the descriptions the LLM reads (from tool_descriptions.py)
    functions: tool name -> Python function that runs (FUNCTIONS of a robot)
    """
    # The whole conversation. The LLM gets all of it again in every step.
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task},
    ]

    for step in range(1, MAX_STEPS + 1):
        # 1. Send the conversation to the LLM and get its next move.
        start = time.time()
        response = client.chat.completions.create(
            model=MODEL, messages=messages, tools=tools
        )
        reply = response.choices[0].message
        messages.append(reply)  # so the LLM remembers which tools it called

        print(f"\n=== step {step}, {time.time() - start:.1f} s")
        # Thinking models (qwen3, gemma4) send their reasoning in an extra field.
        print("THINKING:", getattr(reply, "reasoning", None) or "(none)")
        print("TEXT:    ", reply.content or "(none)")

        # 2. No tool call means the LLM is done. Its text is the report.
        if not reply.tool_calls:
            return reply.content

        # 3. Run every tool it asked for and add each result to the conversation.
        #    The tool_call_id tells the LLM which call the result belongs to.
        for call in reply.tool_calls:
            result = call_tool(call, functions)
            messages.append(
                {"role": "tool", "tool_call_id": call.id, "content": result}
            )

    return "stopped after too many steps"


# ============================================================================
# 3. The missions
# ============================================================================
TASK = "Take the box from the pickup to the dropoff, then return to the dock."

CORRIDOR_SYSTEM_PROMPT = """You control a delivery robot on a straight corridor.
Cells: dock 0, pickup 3, dropoff 8. The robot starts at the dock.
Driving costs 5 % battery per cell. Charging works only at the dock.
Plan your moves in advance so you dont run out of battery.
Use the tools, one call at a time. Finish with a one line report."""

# The battery costs were measured in the world "room" (9 % per metre).
# Charging once at the start is not enough: 100 - 16 - 50 = 34 %, but the way
# back from the dropoff needs 40 %. The LLM has to charge after the pickup.
NAV2_SYSTEM_PROMPT = """You control a delivery robot that drives with Nav2.
A person loads and unloads the box, ask them and wait for the answer.
If a drive fails, decide what to do and explain it in the report.
The robot starts at the dock. Charging works only at the dock.
A drive costs about: dock-pickup 16 %, pickup-dropoff 50 %, dock-dropoff 40 %.
At 0 % the robot stops for good. Check the battery before every drive.
In the report, say when and why you charged."""


def run_corridor_mission():
    run_agent(CORRIDOR_SYSTEM_PROMPT, TASK, CORRIDOR_TOOLS, corridor_robot.FUNCTIONS)
    print("\nFINAL STATE:", corridor_robot.state)


def run_nav2_delivery():
    import nav2_robot  # needs ROS, so it is only imported here

    nav2_robot.connect()
    run_agent(NAV2_SYSTEM_PROMPT, TASK, NAV2_TOOLS, nav2_robot.FUNCTIONS)
    nav2_robot.disconnect()


# ============================================================================
# 4. Start
# ============================================================================
if __name__ == "__main__":
    if "nav2" in sys.argv[1:]:
        run_nav2_delivery()
    else:
        run_corridor_mission()
