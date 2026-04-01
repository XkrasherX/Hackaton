import numpy as np


EARTH_RADIUS = 6371000  # meters


def haversine(lat1, lon1, lat2, lon2):
    """
    Compute distance between two WGS84 points in meters.
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
    dt = gps_df["time_us"].diff() / 1e6

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

    horizontal_speed = np.array(horizontal_dist) / dt
    vertical_speed = gps_df["alt"].diff() / dt

    return horizontal_speed, vertical_speed


def compute_max_acceleration(imu_df):
    acc_mag = np.sqrt(
        imu_df["acc_x"]**2 +
        imu_df["acc_y"]**2 +
        imu_df["acc_z"]**2
    )
    return acc_mag.max()


def compute_max_altitude_gain(gps_df):
    cumulative_gain = 0
    max_gain = 0

    for i in range(1, len(gps_df)):
        diff = gps_df["alt"].iloc[i] - gps_df["alt"].iloc[i - 1]
        if diff > 0:
            cumulative_gain += diff
        max_gain = max(max_gain, cumulative_gain)

    return max_gain


def compute_duration(gps_df):
    return (gps_df["time_us"].iloc[-1] -
            gps_df["time_us"].iloc[0]) / 1e6