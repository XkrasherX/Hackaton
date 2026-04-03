import numpy as np
import logging

logger = logging.getLogger(__name__)

EARTH_RADIUS = 6371000  # meters


def haversine(lat1, lon1, lat2, lon2):
    """
    Compute distance between two WGS84 points in meters.
    Uses the Haversine formula for accurate geodetic distances.
    """
    
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = np.sin(dlat / 2) ** 2 + \
        np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2

    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    return EARTH_RADIUS * c


def compute_total_distance_haversine(gps_df):
    """
    Compute total horizontal distance traveled using Haversine formula.
    
    Args:
        gps_df: DataFrame with 'lat', 'lon' columns
        
    Returns:
        float: Total distance in meters
    """
    if gps_df.empty or len(gps_df) < 2:
        logger.warning("Empty or insufficient GPS data for distance calculation")
        return 0.0
    
    total = 0.0
    for i in range(1, len(gps_df)):
        d = haversine(
            gps_df["lat"].iloc[i - 1],
            gps_df["lon"].iloc[i - 1],
            gps_df["lat"].iloc[i],
            gps_df["lon"].iloc[i]
        )
        total += d
    return total


def compute_speed_components(gps_df):
    """
    Compute horizontal and vertical speed components from GPS data.
    
    Args:
        gps_df: DataFrame with 'lat', 'lon', 'alt', 'time_us' columns
        
    Returns:
        tuple: (horizontal_speed, vertical_speed) as numpy arrays
    """
    if gps_df.empty or len(gps_df) < 2:
        logger.warning("Empty or insufficient GPS data for speed calculation")
        return np.array([]), np.array([])
    
    dt = gps_df["time_us"].diff() / 1e6
    dt[0] = 1  # Avoid division by zero for first element
    dt = dt.replace(0, 1)  # Avoid division by zero
    dt = np.maximum(dt, 0.001)  # Minimum 1ms to avoid extreme values

    horizontal_dist = [
        haversine(
            gps_df["lat"].iloc[i - 1],
            gps_df["lon"].iloc[i - 1],
            gps_df["lat"].iloc[i],
            gps_df["lon"].iloc[i]
        )
        if i > 0 else 0
        for i in range(len(gps_df))
    ]

    horizontal_speed = np.array(horizontal_dist) / dt.values
    
    # Fix unrealistic speed values (likely GPS errors at start/end)
    # Max drone speed is typically ~100 m/s (360 km/h)
    # Filter out outliers using median absolute deviation
    valid_speeds = horizontal_speed[horizontal_speed < 200]  # Initial filter
    if len(valid_speeds) > 0:
        median_speed = np.median(valid_speeds)
        mad = np.median(np.abs(valid_speeds - median_speed))
        threshold = median_speed + 5 * mad if mad > 0 else 100
    else:
        threshold = 100
    
    # Replace extreme values with NaN (will be interpolated)
    horizontal_speed = np.where(horizontal_speed > threshold, np.nan, horizontal_speed)
    
    # Interpolate NaN values
    valid_mask = ~np.isnan(horizontal_speed)
    if valid_mask.sum() > 0:
        valid_indices = np.where(valid_mask)[0]
        horizontal_speed = np.interp(
            np.arange(len(horizontal_speed)),
            valid_indices,
            horizontal_speed[valid_indices],
            left=0,
            right=horizontal_speed[valid_indices[-1]] if len(valid_indices) > 0 else 0
        )
    
    # Handle missing altitude values
    if "alt" in gps_df.columns:
        vertical_speed = gps_df["alt"].diff() / dt.values
    else:
        vertical_speed = np.zeros_like(horizontal_speed)

    return horizontal_speed, vertical_speed


def compute_max_acceleration(imu_df):
    """
    Compute maximum acceleration magnitude from IMU data.
    
    Args:
        imu_df: DataFrame with 'acc_x', 'acc_y', 'acc_z' columns
        
    Returns:
        float: Maximum acceleration magnitude in m/s^2
    """
    if imu_df.empty or not all(col in imu_df.columns for col in ["acc_x", "acc_y", "acc_z"]):
        logger.warning("Empty or incomplete IMU data for acceleration calculation")
        return 0.0
    
    acc_mag = np.sqrt(
        imu_df["acc_x"]**2 +
        imu_df["acc_y"]**2 +
        imu_df["acc_z"]**2
    )
    return float(np.nanmax(acc_mag))


def compute_max_altitude_gain(gps_df):
    """
    Compute cumulative maximum altitude gain (only positive changes).
    
    Args:
        gps_df: DataFrame with 'alt' column
        
    Returns:
        float: Maximum cumulative altitude gain in meters
    """
    if gps_df.empty or len(gps_df) < 2:
        logger.warning("Empty or insufficient GPS data for altitude calculation")
        return 0.0
    
    cumulative_gain = 0
    max_gain = 0

    for i in range(1, len(gps_df)):
        diff = gps_df["alt"].iloc[i] - gps_df["alt"].iloc[i - 1]
        if diff > 0:
            cumulative_gain += diff
        max_gain = max(max_gain, cumulative_gain)

    return max_gain


def compute_duration(gps_df):
    """
    Compute flight duration from GPS timestamp range.
    
    Args:
        gps_df: DataFrame with 'time_us' column
        
    Returns:
        float: Duration in seconds
    """
    if gps_df.empty or len(gps_df) < 2:
        logger.warning("Empty or insufficient GPS data for duration calculation")
        return 0.0
    
    duration = (gps_df["time_us"].iloc[-1] - gps_df["time_us"].iloc[0]) / 1e6
    return float(duration)