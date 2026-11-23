import numpy as np


def rot_z(theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s, 0, 0], [s, c, 0, 0],
                     [0, 0, 1, 0], [0, 0, 0, 1]])


def trans_x(length):
    T = np.eye(4)
    T[0, 3] = length
    return T


def fk(q, links=(0.5, 0.3)):
    T = np.eye(4)
    for theta, length in zip(q, links):
        T = T @ rot_z(theta) @ trans_x(length)
    return T


if __name__ == "__main__":
    # Example from the slides. Replace the angles with the ones from the exercise.
    T = fk(np.radians([90, -90]))
    print("position:", T[:3, 3].round(3))
    yaw = np.degrees(np.arctan2(T[1, 0], T[0, 0]))
    print("orientation in degrees:", round(yaw, 1))
