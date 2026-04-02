from pymavlink import DFReader
import pandas as pd
import os


def parse_ardupilot_log(file_path: str):

    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    log = DFReader.DFReader_binary(file_path)

    gps_data = []
    imu_data = []

    try:
        while True:
            msg = log.recv_msg()
            if msg is None:
                break

            msg_type = msg.get_type()

            if msg_type.startswith("GPS"):
                if hasattr(msg, "Lat") and hasattr(msg, "Lng"):
                    gps_data.append({
                        "time_us": getattr(msg, "TimeUS", 0),
                        "lat": msg.Lat / 1e7,
                        "lon": msg.Lng / 1e7,
                        "alt": msg.Alt / 1000.0,
                    })

            if msg_type.startswith("IMU"):
                imu_data.append({
                    "time_us": getattr(msg, "TimeUS", 0),
                    "acc_x": getattr(msg, "AccX", 0),
                    "acc_y": getattr(msg, "AccY", 0),
                    "acc_z": getattr(msg, "AccZ", 0),
                    "gyro_x": getattr(msg, "GyrX", 0),
                    "gyro_y": getattr(msg, "GyrY", 0),
                    "gyro_z": getattr(msg, "GyrZ", 0),
                })

    finally:
        # 🔥 ОБОВ'ЯЗКОВО закриваємо файл
        log.close()

    gps_df = pd.DataFrame(gps_data)
    imu_df = pd.DataFrame(imu_data)

    return gps_df, imu_df