import numpy as np


def trapezoidal_integration(time_us, values):
    """
    Numerical integration using trapezoidal rule.
    time_us: microseconds
    values: numpy array
    """
    t = time_us / 1e6
    dt = np.diff(t)

    integral = np.zeros_like(values)
    for i in range(1, len(values)):
        integral[i] = integral[i - 1] + 0.5 * (values[i] + values[i - 1]) * dt[i - 1]

    return integral


def compute_velocity_from_acc(imu_df):
    """
    Integrate acceleration → velocity (body frame).
    """

    vx = trapezoidal_integration(imu_df["time_us"].values,
                                  imu_df["acc_x"].values)

    vy = trapezoidal_integration(imu_df["time_us"].values,
                                  imu_df["acc_y"].values)

    vz = trapezoidal_integration(imu_df["time_us"].values,
                                  imu_df["acc_z"].values)

    return vx, vy, vz