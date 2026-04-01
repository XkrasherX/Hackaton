import sys
import numpy as np

from core.parser import parse_ardupilot_log
from core.coordinates import wgs84_to_ecef, ecef_to_enu
from core.metrics import (
    compute_total_distance_haversine,
    compute_speed_components,
    compute_max_acceleration,
    compute_max_altitude_gain,
    compute_duration
)
from core.integration import compute_velocity_from_acc
from core.visualization import plot_3d_trajectory


def main(log_path):

    print("Parsing log...")
    gps_df, imu_df = parse_ardupilot_log(log_path)

    if gps_df.empty:
        print("No GPS data found.")
        return

    # Distance (HAVERSINE)
    total_distance = compute_total_distance_haversine(gps_df)

    # Speeds from GPS
    horizontal_speed, vertical_speed = compute_speed_components(gps_df)

    gps_df["speed"] = horizontal_speed

    max_horizontal_speed = np.nanmax(horizontal_speed)
    max_vertical_speed = np.nanmax(np.abs(vertical_speed))

    # Acceleration
    max_acc = compute_max_acceleration(imu_df)

    # Altitude
    max_alt_gain = compute_max_altitude_gain(gps_df)

    # Duration
    duration = compute_duration(gps_df)

    # IMU integration (trapezoidal)
    vx, vy, vz = compute_velocity_from_acc(imu_df)

    print("\n=== FLIGHT SUMMARY ===")
    print(f"Duration: {duration:.2f} s")
    print(f"Total distance (haversine): {total_distance:.2f} m")
    print(f"Max horizontal speed: {max_horizontal_speed:.2f} m/s")
    print(f"Max vertical speed: {max_vertical_speed:.2f} m/s")
    print(f"Max acceleration: {max_acc:.2f} m/s²")
    print(f"Max altitude gain: {max_alt_gain:.2f} m")

    # ENU conversion
    x, y, z = wgs84_to_ecef(
        gps_df["lat"].values,
        gps_df["lon"].values,
        gps_df["alt"].values
    )

    ref_lat = gps_df["lat"].iloc[0]
    ref_lon = gps_df["lon"].iloc[0]
    ref_alt = gps_df["alt"].iloc[0]

    east, north, up = ecef_to_enu(
        x, y, z,
        ref_lat, ref_lon, ref_alt
    )

    gps_df["east"] = east
    gps_df["north"] = north
    gps_df["up"] = up

    print("Rendering 3D visualization...")
    plot_3d_trajectory(gps_df, color_mode="speed")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py <logfile.BIN>")
    else:
        main(sys.argv[1])