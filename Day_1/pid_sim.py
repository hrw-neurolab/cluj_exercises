"""PID control of a single robot joint lifting a link against gravity.

Robotics Fundamentals, Day 1, exercise "Tune the arm".

The joint model follows Lynch and Park, Modern Robotics, chapter 11:

    tau = M * theta_ddot + m * g * r * cos(theta) + b * theta_dot

theta is measured from the horizontal. The link starts hanging down
(theta = -90 deg) and the controller has to lift it to the target.

Usage examples:
    python3 pid_sim.py --kp 15
    python3 pid_sim.py --kp 15 --ki 20
    python3 pid_sim.py --kp 15 --ki 20 --kd 1.5
    python3 pid_sim.py --kp 15 --ki 20 --kd 1.5 --noise 0.5 --limit 8
    python3 pid_sim.py --kp 15 --ki 20 --kd 1.5 --save run.png

Needs Python 3 and matplotlib (pip install matplotlib).
Without matplotlib the script still runs and prints the key numbers.
"""

import argparse
import math
import random


class PID:
    def __init__(self, kp, ki, kd, dt):
        self.kp, self.ki, self.kd, self.dt = kp, ki, kd, dt
        self.integral = 0.0
        self.prev_error = None

    def update(self, target, measured):
        error = target - measured
        if self.prev_error is None:
            self.prev_error = error
        self.integral += error * self.dt
        derivative = (error - self.prev_error) / self.dt
        self.prev_error = error
        return (self.kp * error + self.ki * self.integral
                + self.kd * derivative)


# Physical parameters of the link
MASS = 1.0        # m, kg
COM_DIST = 0.5    # r, distance joint to center of mass, m
GRAVITY = 9.81    # g, m/s^2
INERTIA = MASS * COM_DIST ** 2   # M, kg m^2 (point mass)
FRICTION = 1.0    # b, viscous friction, Nm s/rad

CONTROL_DT = 0.01   # controller runs at 100 Hz
PHYSICS_STEPS = 10  # physics substeps per control step


def simulate(kp, ki, kd, target_deg=0.0, start_deg=-90.0, duration=4.0,
             noise_deg=0.0, limit=None, seed=0):
    """Run one simulation and return time, angle, measured angle, torque."""
    rng = random.Random(seed)
    pid = PID(kp, ki, kd, CONTROL_DT)
    theta = math.radians(start_deg)
    theta_dot = 0.0
    target = math.radians(target_deg)
    h = CONTROL_DT / PHYSICS_STEPS

    ts, angles, measured_angles, torques = [], [], [], []
    steps = int(round(duration / CONTROL_DT))
    for k in range(steps + 1):
        # Sense: the encoder reading, optionally with Gaussian noise
        measured = theta + math.radians(rng.gauss(0.0, noise_deg)) \
            if noise_deg > 0 else theta
        # Think: the PID controller computes a torque
        tau = pid.update(target, measured)
        # Act: the motor can only deliver a limited torque
        if limit is not None:
            tau = max(-limit, min(limit, tau))

        ts.append(k * CONTROL_DT)
        angles.append(math.degrees(theta))
        measured_angles.append(math.degrees(measured))
        torques.append(tau)

        # The world: integrate the joint dynamics until the next control step
        for _ in range(PHYSICS_STEPS):
            gravity = MASS * GRAVITY * COM_DIST * math.cos(theta)
            theta_ddot = (tau - gravity - FRICTION * theta_dot) / INERTIA
            theta_dot += theta_ddot * h
            theta += theta_dot * h

    return ts, angles, measured_angles, torques


def summary(ts, angles, torques, target_deg, band=2.0):
    """Overshoot, final angle, settling time and peak torque."""
    final = angles[-1]
    peak = max(angles)
    settle = None
    for i in range(len(angles) - 1, -1, -1):
        if abs(angles[i] - target_deg) > band:
            settle = ts[i + 1] if i + 1 < len(ts) else None
            break
    else:
        settle = 0.0
    return {
        "final angle (deg)": final,
        "highest angle (deg)": peak,
        "overshoot above target (deg)": max(0.0, peak - target_deg),
        "settling time into +-2 deg (s)": settle,
        "peak torque (Nm)": max(abs(t) for t in torques),
    }


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--kp", type=float, default=15.0, help="proportional gain")
    p.add_argument("--ki", type=float, default=0.0, help="integral gain")
    p.add_argument("--kd", type=float, default=0.0, help="derivative gain")
    p.add_argument("--target", type=float, default=0.0,
                   help="target angle in deg, 0 is horizontal")
    p.add_argument("--time", type=float, default=4.0, help="duration in s")
    p.add_argument("--noise", type=float, default=0.0,
                   help="encoder noise, standard deviation in deg")
    p.add_argument("--limit", type=float, default=None,
                   help="maximum motor torque in Nm (default: unlimited)")
    p.add_argument("--save", type=str, default=None,
                   help="save the plot to this file instead of showing it")
    args = p.parse_args()

    ts, angles, measured, torques = simulate(
        args.kp, args.ki, args.kd, target_deg=args.target,
        duration=args.time, noise_deg=args.noise, limit=args.limit)

    print(f"Kp={args.kp}  Ki={args.ki}  Kd={args.kd}  "
          f"noise={args.noise} deg  limit={args.limit} Nm")
    for key, value in summary(ts, angles, torques, args.target).items():
        text = "not settled" if value is None else f"{value:.2f}"
        print(f"  {key:32s} {text}")

    try:
        import matplotlib
        if args.save:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed, skipping the plot")
        return

    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(9, 6))
    if args.noise > 0:
        ax1.plot(ts, measured, color="0.75", lw=0.8, label="encoder reading")
    ax1.plot(ts, angles, color="#2A6496", lw=2, label="joint angle")
    ax1.axhline(args.target, color="#121A24", ls="--", lw=1, label="target")
    ax1.set_ylabel("angle (deg)")
    ax1.set_title(f"Kp={args.kp}, Ki={args.ki}, Kd={args.kd}")
    ax1.legend(loc="lower right")
    ax1.grid(alpha=0.3)

    ax2.plot(ts, torques, color="#9A4312", lw=1.5)
    if args.limit is not None:
        ax2.axhline(args.limit, color="0.5", ls=":", lw=1)
        ax2.axhline(-args.limit, color="0.5", ls=":", lw=1)
    ax2.set_ylabel("motor torque (Nm)")
    ax2.set_xlabel("time (s)")
    ax2.grid(alpha=0.3)

    fig.tight_layout()
    if args.save:
        fig.savefig(args.save, dpi=120)
        print(f"plot saved to {args.save}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
