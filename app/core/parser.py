from pymavlink import mavutil
import pandas as pd


def parse_ardupilot_log(file_path: str):
    """
    Parse ArduPilot DataFlash log (.BIN or .LOG)
    Extract GPS and IMU messages.
    """

    mlog = mavutil.mavlink_connection(file_path)

    gps_data = []
    imu_data = []

    while True:
        msg = mlog.recv_match(blocking=False)
        if msg is None:
            break

        msg_type = msg.get_type()

        if msg_type == "GPS":
            gps_data.append({
                "time_us": msg.TimeUS,
                "lat": msg.Lat / 1e7,     # deg
                "lon": msg.Lng / 1e7,     # deg
                "alt": msg.Alt / 1000.0,  # mm → m
                "vel": msg.Spd / 100.0,   # cm/s → m/s
                "satellites": msg.NSats
            })

        elif msg_type == "IMU":
            imu_data.append({
                "time_us": msg.TimeUS,
                "acc_x": msg.AccX,
                "acc_y": msg.AccY,
                "acc_z": msg.AccZ,
                "gyro_x": msg.GyrX,
                "gyro_y": msg.GyrY,
                "gyro_z": msg.GyrZ
            })

    gps_df = pd.DataFrame(gps_data)
    imu_df = pd.DataFrame(imu_data)

    return gps_df, imu_df


def compute_sampling_rate(df, time_column="time_us"):
    dt = df[time_column].diff().dropna() / 1e6
    return 1.0 / dt.mean()