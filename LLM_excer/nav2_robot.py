"""Part 2: the simulated robot of delivery_bt (day 8), driven by Nav2.

Same idea as corridor_robot.py, but goto sends a goal to Nav2, and instead of
load/unload the robot asks the person. This file needs ROS 2, so
llm_robot_agent.py only imports it when you start it with `nav2`.

Before you start, launch the world of day 8 in its own terminal:
    ros2 launch delivery_bt delivery.launch.py world:=room
It starts the simulator, the map, AMCL, Nav2 and RViz. The robot starts on the
dock, the origin of the map, and AMCL starts there too, so no 2D Pose
Estimate is needed.
"""
import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult

# The stations of the world "room" in frame map, (x, y) in meters, from the
# README of delivery_bt. For world:=loop: pickup (4.0, 0.0), dropoff (4.0, -4.0).
# Other points: run `ros2 topic echo /clicked_point`, then click on the map
# with "Publish Point" in RViz. Copy point.x and point.y from the terminal.
STATIONS = {
    "pickup": (-0.7, 1.5),
    "dropoff": (3.9, 1.3),
    "dock": (0.0, 0.0),  # the robot starts here
}

navigator = None  # the connection to Nav2, created by connect()


def connect():
    """Start ROS and wait for Nav2. Call this once before the agent starts."""
    global navigator
    rclpy.init()
    navigator = BasicNavigator()
    navigator.waitUntilNav2Active()  # waits until Nav2 knows the initial pose


def disconnect():
    rclpy.shutdown()


def goto(station):
    """Send the station as a goal to Nav2 and wait until the drive ends."""
    x, y = STATIONS[station]
    goal = PoseStamped()
    goal.header.frame_id = "map"
    goal.pose.position.x = x
    goal.pose.position.y = y
    goal.pose.orientation.w = 1.0  # quaternion for "no rotation"
    navigator.goToPose(goal)

    # isTaskComplete() waits up to 0.1 s for news from Nav2 on each call,
    # so this loop does not need its own sleep.
    while not navigator.isTaskComplete():
        pass

    if navigator.getResult() == TaskResult.SUCCEEDED:
        return f"reached {station}"
    return f"failed to reach {station}"


def ask_human(question):
    """Show the question in the terminal and return what the person types."""
    return input(f"ROBOT: {question}\nYOU: ")


# The LLM asks for a tool by its name. This table says which Python function
# runs for that name. The names must match NAV2_TOOLS in tool_descriptions.py.
FUNCTIONS = {
    "goto": goto,
    "ask_human": ask_human,
}
