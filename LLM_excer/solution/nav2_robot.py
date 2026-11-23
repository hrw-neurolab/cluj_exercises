"""Part 2: the simulated robot of delivery_bt (day 8), driven by Nav2.

SOLUTION of the battery task in INSTALL_day9.md. New compared to
../nav2_robot.py: the subscription and the service client in connect(), and
the functions on_battery_state, battery and charge.

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
from sensor_msgs.msg import BatteryState
from std_srvs.srv import Trigger

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
charge_client = None  # client of the service /dock/charge, created by connect()
battery_level = None  # latest value of /battery_state, from 0 to 1


def connect():
    """Start ROS and wait for Nav2. Call this once before the agent starts."""
    global navigator, charge_client
    rclpy.init()
    navigator = BasicNavigator()

    # navigator is a ROS node, so it can also listen to the battery and call
    # the dock. The callback runs whenever the node spins: in spin_once below,
    # and while navigator waits for Nav2 in goto.
    navigator.create_subscription(BatteryState, "battery_state", on_battery_state, 10)
    charge_client = navigator.create_client(Trigger, "/dock/charge")

    navigator.waitUntilNav2Active()  # waits until Nav2 knows the initial pose


def disconnect():
    rclpy.shutdown()


def on_battery_state(msg):
    """Callback of /battery_state: remember the latest level."""
    global battery_level
    battery_level = msg.percentage  # 0 to 1, so 0.54 means 54 %


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


def battery():
    """The battery level in %, as text for the LLM."""
    rclpy.spin_once(navigator, timeout_sec=0.5)  # lets on_battery_state run
    if battery_level is None:
        return "error: no message on /battery_state yet"
    return f"battery {battery_level * 100:.0f} %"


def charge():
    """Plug in at the dock and wait until the battery is full."""
    if not charge_client.wait_for_service(timeout_sec=2.0):
        return "error: service /dock/charge is not available"

    future = charge_client.call_async(Trigger.Request())
    rclpy.spin_until_future_complete(navigator, future)
    answer = future.result()
    if not answer.success:
        return f"error: {answer.message}"  # e.g. "not on the dock, 1.50 m away"

    # /dock/charge only starts charging and answers at once. Wait here until
    # the battery is full, or the LLM would drive away with half a battery.
    while battery_level is None or battery_level < 1.0:
        rclpy.spin_once(navigator, timeout_sec=0.1)
    return "battery 100 %"


def ask_human(question):
    """Show the question in the terminal and return what the person types."""
    return input(f"ROBOT: {question}\nYOU: ")


# The LLM asks for a tool by its name. This table says which Python function
# runs for that name. The names must match NAV2_TOOLS in tool_descriptions.py.
FUNCTIONS = {
    "goto": goto,
    "ask_human": ask_human,
    "battery": battery,
    "charge": charge,
}
