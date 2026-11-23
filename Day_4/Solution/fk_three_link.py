import itertools

import numpy as np
import matplotlib.pyplot as plt


def rot_z(theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s, 0, 0], [s, c, 0, 0],
                     [0, 0, 1, 0], [0, 0, 0, 1]])


def trans_x(length):
    T = np.eye(4)
    T[0, 3] = length
    return T


def fk(q, links=(0.5, 0.3, 0.1)):
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

    # Workspace: sample all three joints at the same time over [-pi, pi]
    # and scatter the resulting tip positions.
    angles = np.linspace(-np.pi, np.pi, 40)

    points = np.array([fk(q)[:2, 3]
                       for q in itertools.product(angles, repeat=3)])

    plt.figure(figsize=(6, 6))
    plt.scatter(points[:, 0], points[:, 1], s=1, alpha=0.1)
    plt.title(f"Workspace of the 3-link arm ({len(points)} samples)")
    plt.xlabel("x [m]")
    plt.ylabel("y [m]")
    plt.gca().set_aspect("equal")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("workspace_three_link.png", dpi=150)
    plt.show()
