import pandas as pd
from pymavlink import mavutil

def parse_ardupilot_log(file_path):
    """Витягує повідомлення GPS та IMU з бінарного логу [cite: 16, 17]"""
    mlog = mavutil.mavlink_connection(file_path)

    gps_data = []
    imu_data = []

    while True:
        msg = mlog.recv_match(type=['GPS', 'IMU'], blocking=False)
        if msg is None:
            break

        msg_type = msg.get_type()
        timestamp = msg._timestamp

        if msg_type == 'GPS':
            gps_data.append({
                'Time': timestamp,
                'Lat': msg.Lat,
                'Lng': msg.Lng,
                'Alt': msg.Alt
            })
        elif msg_type == 'IMU':
            imu_data.append({
                'Time': timestamp,
                'AccX': msg.AccX,
                'AccY': msg.AccY,
                'AccZ': msg.AccZ
            })

    df_gps = pd.DataFrame(gps_data)
    df_imu = pd.DataFrame(imu_data)
    return df_gps, df_imu