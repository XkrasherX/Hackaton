import pandas as pd
import numpy as np
from pymavlink import mavutil
from collections import defaultdict


class ArduPilotLogParser:

    def __init__(self, file_path):
        self.file_path = file_path
        self.log = mavutil.mavlink_connection(file_path)

        self.gps_data = []
        self.imu_data = []
        self.att_data = []
        self.pid_data = []

    # -------------------------------------------------
    # MAIN PARSER
    # -------------------------------------------------

    def parse(self):
        print("[*] Parsing log...")

        msg_types_found = {}

        while True:
            msg = self.log.recv_match(blocking=False)
            if msg is None:
                break

            msg_type = msg.get_type()
            msg_types_found[msg_type] = msg_types_found.get(msg_type, 0) + 1

            if msg_type in ["GPS", "GPS_RAW_INT", "GPS2_RAW"]:
                self._parse_gps(msg)

            elif msg_type in ["IMU", "RAW_IMU", "SCALED_IMU", "SCALED_IMU2"]:
                self._parse_imu(msg)

            elif msg_type in ["ATT", "ATTITUDE"]:
                self._parse_attitude(msg)

            elif "PID" in msg_type or msg_type in ["RATE", "ATC"]:
                self._parse_pid(msg)

        print("[OK] Parsing complete")
        print(f"   Message types found: {sorted(msg_types_found.items())}")
        print(f"   GPS records: {len(self.gps_data)}, IMU records: {len(self.imu_data)}")

        return self._build_output()

    # -------------------------------------------------
    # GPS
    # -------------------------------------------------

    def _parse_gps(self, msg):
        # Handle both old and new field naming conventions
        # Note: ArduPilot uses "Lng" not "Lon" for longitude
        lat = getattr(msg, "Lat", None)
        lng = getattr(msg, "Lng", getattr(msg, "Lon", None))  # Try Lng first, then Lon
        alt = getattr(msg, "Alt", None)
        spd = getattr(msg, "Spd", getattr(msg, "Vel", None))
        
        # Values from ArduPilot GPS messages are already in proper units:
        # - Lat/Lng: decimal degrees
        # - Alt: meters
        # - Spd: m/s
        
        self.gps_data.append({
            "TimeUS": getattr(msg, "TimeUS", None),
            "Lat_deg": lat,  # Already in degrees
            "Lon_deg": lng,  # Already in degrees
            "Alt_m": alt,    # Already in meters
            "Vel_m_s": spd,  # Already in m/s
            "Satellites": getattr(msg, "NSats", getattr(msg, "Nsat", None)),
        })

    # -------------------------------------------------
    # IMU
    # -------------------------------------------------

    def _parse_imu(self, msg):
        self.imu_data.append({
            "TimeUS": getattr(msg, "TimeUS", None),
            "AccX": getattr(msg, "AccX", getattr(msg, "xacc", None)),
            "AccY": getattr(msg, "AccY", getattr(msg, "yacc", None)),
            "AccZ": getattr(msg, "AccZ", getattr(msg, "zacc", None)),
            "GyrX": getattr(msg, "GyrX", getattr(msg, "xgyro", None)),
            "GyrY": getattr(msg, "GyrY", getattr(msg, "ygyro", None)),
            "GyrZ": getattr(msg, "GyrZ", getattr(msg, "zgyro", None)),
        })

    # -------------------------------------------------
    # ATTITUDE
    # -------------------------------------------------

    def _parse_attitude(self, msg):
        self.att_data.append({
            "TimeUS": getattr(msg, "TimeUS", None),
            "Roll_deg": np.degrees(getattr(msg, "Roll", getattr(msg, "roll", 0))),
            "Pitch_deg": np.degrees(getattr(msg, "Pitch", getattr(msg, "pitch", 0))),
            "Yaw_deg": np.degrees(getattr(msg, "Yaw", getattr(msg, "yaw", 0))),
            "DesRoll_deg": getattr(msg, "DesRoll", None),
            "DesPitch_deg": getattr(msg, "DesPitch", None),
            "DesYaw_deg": getattr(msg, "DesYaw", None),
        })

    # -------------------------------------------------
    # PID
    # -------------------------------------------------

    def _parse_pid(self, msg):
        self.pid_data.append({
            "TimeUS": getattr(msg, "TimeUS", None),
            "Tar": getattr(msg, "Tar", None),
            "Act": getattr(msg, "Act", None),
            "Err": getattr(msg, "Err", None),
            "P": getattr(msg, "P", None),
            "I": getattr(msg, "I", None),
            "D": getattr(msg, "D", None),
            "FF": getattr(msg, "FF", None),
            "DFF": getattr(msg, "DFF", None),
            "Dmod": getattr(msg, "Dmod", None),
            "SRate": getattr(msg, "SRate", None),
            "Flags": getattr(msg, "Flags", None),
        })

    # -------------------------------------------------
    # BUILD OUTPUT
    # -------------------------------------------------

    def _build_output(self):
        gps_df = pd.DataFrame(self.gps_data)
        imu_df = pd.DataFrame(self.imu_data)
        att_df = pd.DataFrame(self.att_data)
        pid_df = pd.DataFrame(self.pid_data)

        # Normalize time (µs → seconds from start)
        for df in [gps_df, imu_df, att_df, pid_df]:
            if not df.empty and "TimeUS" in df:
                df["Time_sec"] = (df["TimeUS"] - df["TimeUS"].iloc[0]) / 1e6

        sampling_info = {
            "GPS_Hz": self._estimate_freq(gps_df),
            "IMU_Hz": self._estimate_freq(imu_df),
            "ATT_Hz": self._estimate_freq(att_df),
            "PID_Hz": self._estimate_freq(pid_df),
        }

        meta_info = {
            "GPS": "Lat/Lon: degrees, Alt: meters",
            "IMU": "Acceleration: raw or m/s^2, Gyro: rad/s",
            "ATT": "Angles: degrees",
            "PID": "Controller internal units"
        }

        return gps_df, imu_df, att_df, pid_df, sampling_info, meta_info

    # -------------------------------------------------
    # FREQUENCY ESTIMATION
    # -------------------------------------------------

    def _estimate_freq(self, df):
        if df.empty or "TimeUS" not in df:
            return 0

        times = df["TimeUS"].dropna().values
        if len(times) < 2:
            return 0

        dt = np.diff(times) / 1e6
        mean_dt = np.mean(dt)

        return 1.0 / mean_dt if mean_dt > 0 else 0


# -------------------------------------------------
# RUN
# -------------------------------------------------

if __name__ == "__main__":

    parser = ArduPilotLogParser("flight_log.BIN")

    gps_df, imu_df, att_df, pid_df, sampling_info, meta_info = parser.parse()

    print("\n📡 Sampling frequencies:")
    for k, v in sampling_info.items():
        print(f"{k}: {v:.2f} Hz")

    print("\n📊 Data samples:")
    print("GPS:", gps_df.shape)
    print("IMU:", imu_df.shape)
    print("ATT:", att_df.shape)
    print("PID:", pid_df.shape)