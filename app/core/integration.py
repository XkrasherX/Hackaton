import numpy as np
import logging

logger = logging.getLogger(__name__)


def trapezoidal_integration(time_us, values):

    #Numerical integration using trapezoidal rule.

    if len(time_us) != len(values):
        raise ValueError("Time and values arrays must have same length")
    
    if len(time_us) < 2:
        logger.warning("Insufficient data for integration")
        return np.zeros_like(values)
    
    t = time_us / 1e6  # Convert to seconds
    dt = np.diff(t)
    
    # Ensure no zero or negative time deltas
    if np.any(dt <= 0):
        logger.warning("Non-positive time deltas detected, may affect integration accuracy")
        dt = np.maximum(dt, 1e-6)  # Minimum 1 microsecond

    integral = np.zeros_like(values, dtype=float)
    for i in range(1, len(values)):
        integral[i] = integral[i - 1] + 0.5 * (values[i] + values[i - 1]) * dt[i - 1]

    return integral


def compute_velocity_from_acc(imu_df):
    """
    Integrate acceleration to obtain velocity using body frame.
    
    Uses trapezoidal integration on acceleration data to compute
    velocity components in the aircraft's body frame (x, y, z axes).
    """
    required_cols = ['time_us', 'acc_x', 'acc_y', 'acc_z']
    missing_cols = [col for col in required_cols if col not in imu_df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing columns in IMU data: {missing_cols}")
    
    if imu_df.empty:
        logger.warning("Empty IMU DataFrame")
        return np.array([]), np.array([]), np.array([])
    
    try:
        vx = trapezoidal_integration(imu_df["time_us"].values,
                                      imu_df["acc_x"].values)

        vy = trapezoidal_integration(imu_df["time_us"].values,
                                      imu_df["acc_y"].values)

        vz = trapezoidal_integration(imu_df["time_us"].values,
                                      imu_df["acc_z"].values)

        return vx, vy, vz
    except Exception as e:
        logger.error(f"Error in velocity integration: {e}")
        raise