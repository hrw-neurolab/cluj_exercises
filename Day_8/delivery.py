import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
GOAL = dict(TO_PICKUP=(3.3, 0.2), TO_DROPOFF=(-0.9, 1.74), TO_DOCK=(0.0, 0.0))  # set your stations, floats in meters
ON_OK = dict(TO_PICKUP="TO_DROPOFF", TO_DROPOFF="TO_DOCK", TO_DOCK="IDLE")
ON_FAIL = dict(TO_PICKUP="TO_DOCK", TO_DROPOFF="TO_DOCK", TO_DOCK="IDLE")
rclpy.init()
nav = BasicNavigator()
nav.waitUntilNav2Active()  # set the pose in RViz first
state = "TO_PICKUP"
while state != "IDLE":
    goal = PoseStamped()
    goal.header.frame_id = "map"
    goal.pose.position.x, goal.pose.position.y = GOAL[state]
    goal.pose.orientation.w = 1.0
    nav.goToPose(goal)
    while not nav.isTaskComplete(): pass
    ok = nav.getResult() == TaskResult.SUCCEEDED
    print(state, "reached" if ok else "failed")
    state = (ON_OK if ok else ON_FAIL)[state]
