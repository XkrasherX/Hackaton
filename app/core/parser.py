import pandas as pd
import numpy as np
from pymavlink import mavutil


class ArduPilotLogParser:

    def __init__(self, file_path):
        self.file_path = file_path
        self.log = mavutil.mavlink_connection(file_path)

        self.gps_data = []
        self.imu_data = []
        self.att_data = []
        self.pid_data = []

    # =====================================================
    # MAIN
    # =====================================================

    def parse(self):
        print("[*] Parsing log...")

        msg_counter = {}

        while True:
            msg = self.log.recv_match(blocking=False)
            if msg is None:
                break

            msg_type = msg.get_type()
            msg_counter[msg_type] = msg_counter.get(msg_type, 0) + 1

            if msg_type in ["GPS", "GPS_RAW_INT", "GPS2_RAW"]:
                self._parse_gps(msg)

            elif msg_type in ["IMU", "RAW_IMU", "SCALED_IMU", "SCALED_IMU2"]:
                self._parse_imu(msg)

            elif msg_type in ["ATT", "ATTITUDE"]:
                self._parse_att(msg)

            elif "PID" in msg_type or msg_type in ["RATE", "ATC"]:
                self._parse_pid(msg)

        print("[OK] Parsing complete")
        print("   Message types:", sorted(msg_counter.items()))

        return self._build_output()

    # =====================================================
    # SAFE TIME EXTRACTION
    # =====================================================

    def _extract_time_us(self, msg):
        if hasattr(msg, "TimeUS") and msg.TimeUS is not None:
            return msg.TimeUS

        if hasattr(msg, "TimeMS") and msg.TimeMS is not None:
            return msg.TimeMS * 1000

        if hasattr(msg, "Time") and msg.Time is not None:
            return msg.Time * 1000

        return None

    # =====================================================
    # GPS
    # =====================================================

    def _parse_gps(self, msg):
        msg_type = msg.get_type()
        t = self._extract_time_us(msg)

        lat = getattr(msg, "Lat", None)
        lon = getattr(msg, "Lng", getattr(msg, "Lon", None))
        alt = getattr(msg, "Alt", None)
        spd = getattr(msg, "Spd", getattr(msg, "Vel", None))

        # GPS_RAW_INT scaling
        if msg_type == "GPS_RAW_INT":
            if lat is not None:
                lat /= 1e7
            if lon is not None:
                lon /= 1e7
            if alt is not None:
                alt /= 1000
            if spd is not None:
                spd /= 100
        
        # Handle regular GPS messages - speed might be in cm/s
        if spd is not None and spd > 1000:  # If speed > 1000 m/s, likely in cm/s
            spd = spd / 100.0  # Convert cm/s to m/s

        self.gps_data.append({
            "TimeUS": t,
            "Lat_deg": lat,
            "Lon_deg": lon,
            "Alt_m": alt,
            "Vel_m_s": spd,
            "Satellites": getattr(msg, "NSats", getattr(msg, "Nsat", None))
        })

    # =====================================================
    # IMU
    # =====================================================

    def _parse_imu(self, msg):
        t = self._extract_time_us(msg)

        self.imu_data.append({
            "TimeUS": t,
            "AccX": getattr(msg, "AccX", getattr(msg, "xacc", None)),
            "AccY": getattr(msg, "AccY", getattr(msg, "yacc", None)),
            "AccZ": getattr(msg, "AccZ", getattr(msg, "zacc", None)),
            "GyrX": getattr(msg, "GyrX", getattr(msg, "xgyro", None)),
            "GyrY": getattr(msg, "GyrY", getattr(msg, "ygyro", None)),
            "GyrZ": getattr(msg, "GyrZ", getattr(msg, "zgyro", None)),
        })

    # =====================================================
    # ATTITUDE
    # =====================================================

    def _parse_att(self, msg):
        msg_type = msg.get_type()
        t = self._extract_time_us(msg)

        if msg_type == "ATTITUDE":
            roll = np.degrees(getattr(msg, "roll", 0))
            pitch = np.degrees(getattr(msg, "pitch", 0))
            yaw = np.degrees(getattr(msg, "yaw", 0))
        else:
            roll = getattr(msg, "Roll", None)
            pitch = getattr(msg, "Pitch", None)
            yaw = getattr(msg, "Yaw", None)

        self.att_data.append({
            "TimeUS": t,
            "Roll_deg": roll,
            "Pitch_deg": pitch,
            "Yaw_deg": yaw,
            "DesRoll_deg": getattr(msg, "DesRoll", None),
            "DesPitch_deg": getattr(msg, "DesPitch", None),
            "DesYaw_deg": getattr(msg, "DesYaw", None),
        })

    # =====================================================
    # PID
    # =====================================================

    def _parse_pid(self, msg):
        t = self._extract_time_us(msg)

        self.pid_data.append({
            "TimeUS": t,
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

    # =====================================================
    # BUILD OUTPUT
    # =====================================================

    def _build_output(self):

        gps_df = pd.DataFrame(self.gps_data)
        imu_df = pd.DataFrame(self.imu_data)
        att_df = pd.DataFrame(self.att_data)
        pid_df = pd.DataFrame(self.pid_data)

        for df in [gps_df, imu_df, att_df, pid_df]:
            if not df.empty and "TimeUS" in df:
                df = df.sort_values("TimeUS")
                valid_time = df["TimeUS"].dropna()

                if not valid_time.empty:
                    t0 = valid_time.min()
                    df["Time_sec"] = (df["TimeUS"] - t0) / 1e6

                    # Detect time reset
                    if np.any(np.diff(valid_time.values) < 0):
                        print("⚠ Warning: Time reset detected in log")

        sampling_info = {
            "GPS_Hz": self._estimate_freq(gps_df),
            "IMU_Hz": self._estimate_freq(imu_df),
            "ATT_Hz": self._estimate_freq(att_df),
            "PID_Hz": self._estimate_freq(pid_df),
        }

        meta_info = {
            "GPS": "Lat/Lon: degrees, Alt: meters, Speed: m/s",
            "IMU": "Acceleration: raw, Gyro: raw",
            "ATT": "Angles: degrees",
            "PID": "Controller internal units"
        }

        return gps_df, imu_df, att_df, pid_df, sampling_info, meta_info

    # =====================================================
    # FREQUENCY (ROBUST)
    # =====================================================

    def _estimate_freq(self, df):
        if df.empty or "TimeUS" not in df:
            return 0

        times = df["TimeUS"].dropna().values
        if len(times) < 3:
            return 0

        dt = np.diff(times) / 1e6
        dt = dt[dt > 0]

        if len(dt) == 0:
            return 0

        median_dt = np.median(dt)
        return 1.0 / median_dt


# =====================================================
# WRAPPER
# =====================================================

def parse_ardupilot_log(file_path):
    parser = ArduPilotLogParser(file_path)
    return parser.parse()


# =====================================================
# RUN
# =====================================================

if __name__ == "__main__":

    gps_df, imu_df, att_df, pid_df, sampling_info, meta_info = parse_ardupilot_log("flight_log.BIN")

    print("\nFlight durations:")
    if not gps_df.empty:
        print("GPS:", gps_df["Time_sec"].max())
    if not imu_df.empty:
        print("IMU:", imu_df["Time_sec"].max())
    if not att_df.empty:
        print("ATT:", att_df["Time_sec"].max())

    print("\nSampling frequencies:")
    for k, v in sampling_info.items():
        print(f"{k}: {v:.2f} Hz")