"""ik_two_link.py

Robotics Fundamentals, Day 5: inverse kinematics of a planar two link arm
with L1 = 0.5 m and L2 = 0.3 m, the same arm as on day 4.

Code from the slides:
    fk()          forward kinematics, day 4, slide 13
    ik()          analytic solution, elbow down or elbow up, day 5, slide 7
    jacobian()    finite difference Jacobian, day 5, slide 13
    ik_dls()      numerical solution with damped least squares, day 5, slide 13

For the comparison on slide 11 the file also contains the pseudoinverse and
the Jacobian transpose step.

Run it with
    python3 ik_two_link.py
to reproduce the numbers on slides 6, 7, 11, 12 and 13. Requires numpy.
All angles are in radians, only the printed output is converted to degrees.
"""

import numpy as np


# ---------------------------------------------------------------------------
# Forward kinematics, day 4, slide 13
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Analytic inverse kinematics, day 5, slide 7
# elbow=+1 gives elbow down, elbow=-1 gives elbow up
# ---------------------------------------------------------------------------

def ik(x, y, links=(0.5, 0.3), elbow=+1):
    L1, L2 = links
    D = (x**2 + y**2 - L1**2 - L2**2) / (2 * L1 * L2)
    if abs(D) > 1:
        return None  # outside the ring
    t2 = elbow * np.arccos(D)
    t1 = np.arctan2(y, x) - np.arctan2(L2 * np.sin(t2),
                                       L1 + L2 * np.cos(t2))
    return np.array([t1, t2])


# ---------------------------------------------------------------------------
# Numerical inverse kinematics, day 5, slide 13
# ---------------------------------------------------------------------------

def jacobian(q, h=1e-6):
    p0 = fk(q)[:2, 3]
    J = np.zeros((2, len(q)))
    for i in range(len(q)):
        dq = np.eye(len(q))[i] * h
        J[:, i] = (fk(q + dq)[:2, 3] - p0) / h
    return J


def ik_dls(target, q0, lam=0.05, tol=1e-6, max_iter=200):
    q = np.array(q0, dtype=float)
    for _ in range(max_iter):
        e = target - fk(q)[:2, 3]
        if np.linalg.norm(e) < tol:
            return q
        J = jacobian(q)
        A = J @ J.T + lam**2 * np.eye(2)
        q = q + J.T @ np.linalg.solve(A, e)
    return None  # gave up


# ---------------------------------------------------------------------------
# The three update rules from slide 11, for the comparison
# Each one returns the step dq for the Jacobian J and the error e.
# ---------------------------------------------------------------------------

def step_pinv(J, e):
    return np.linalg.pinv(J) @ e


def step_transpose(J, e, alpha=1.0):
    return alpha * J.T @ e


def step_dls(J, e, lam=0.05):
    A = J @ J.T + lam**2 * np.eye(2)
    return J.T @ np.linalg.solve(A, e)


def iterate(step, target, q0, tol=1e-6, max_iter=5000):
    """The loop from slide 9 with any update rule.

    Returns the joint angles and the number of steps,
    or None and max_iter if the tolerance was not reached.
    """
    q = np.array(q0, dtype=float)
    target = np.asarray(target, dtype=float)
    for n in range(max_iter):
        e = target - fk(q)[:2, 3]
        if np.linalg.norm(e) < tol:
            return q, n
        q = q + step(jacobian(q), e)
    return None, max_iter


# ---------------------------------------------------------------------------
# Reproduce the numbers on the slides
# ---------------------------------------------------------------------------

def deg(q):
    return np.degrees(q).round(1)


if __name__ == "__main__":
    p = [0.433, 0.55]

    print("Slides 6 and 7, analytic solution for the target", p)
    for elbow, name in ((+1, "elbow down"), (-1, "elbow up")):
        q = ik(*p, elbow=elbow)
        print(f"  {name:10s}  q = {deg(q)} deg   fk(q) = {fk(q)[:3, 3].round(3)}")

    print("\nSlide 11, steps until |e| < 1e-6 m")
    rules = (("Pseudoinverse", step_pinv),
             ("Jacobian transpose", step_transpose),
             ("Damped least squares", step_dls))
    for name, step in rules:
        row = []
        for q0 in ([0.5, 0.5], [0.0, 0.0]):
            q, n = iterate(step, p, q0)
            largest = np.abs(np.degrees(q)).max()
            row.append(f"start {q0}: {n:4d} steps, largest angle {largest:.3g} deg")
        print(f"  {name:21s} " + "   ".join(row))

    print("\nSlide 12, from theta = (0 deg, 1 deg) move the tool 1 cm in")
    q_start = np.radians([0.0, 1.0])
    target = fk(q_start)[:2, 3] - np.array([0.01, 0.0])
    e = target - fk(q_start)[:2, 3]
    J = jacobian(q_start)
    print(f"  exact answer          dq = {deg(ik(*target) - q_start)} deg")
    print(f"  pseudoinverse, step 1 dq = {deg(step_pinv(J, e))} deg")
    print(f"  DLS, step 1           dq = {deg(step_dls(J, e))} deg")
    q, n = iterate(step_dls, target, q_start)
    print(f"  DLS reaches dq = {deg(q - q_start)} deg after {n} steps")

    print("\nSlide 13, damped least squares from two start values")
    print("  ik_dls(p, q0=[0, 0])      ->", deg(ik_dls(p, [0, 0])), "deg")
    print("  ik_dls(p, q0=[1.5, -0.5]) ->", deg(ik_dls(p, [1.5, -0.5])), "deg")
