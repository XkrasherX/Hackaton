from pymavlink import DFReader
import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)


def parse_ardupilot_log(file_path: str):
    """
    Parse ArduPilot binary log file and extract GPS and IMU data.
    
    Args:
        file_path: Path to .BIN or .LOG file
        
    Returns:
        tuple: (gps_df, imu_df) - DataFrames with GPS and IMU data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is empty or corrupted
    """
    
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if os.path.getsize(file_path) == 0:
        raise ValueError(f"Log file is empty: {file_path}")

    log = DFReader.DFReader_binary(file_path)

    gps_data = []
    imu_data = []
    messages_parsed = 0

    try:
        while True:
            msg = log.recv_msg()
            if msg is None:
                break

            messages_parsed += 1
            msg_type = msg.get_type()

            try:
                if msg_type.startswith("GPS"):
                    if hasattr(msg, "Lat") and hasattr(msg, "Lng"):
                        # Validate GPS coordinates
                        lat = msg.Lat / 1e7
                        lon = msg.Lng / 1e7
                        alt = msg.Alt / 1000.0
                        
                        # Basic sanity checks
                        if -90 <= lat <= 90 and -180 <= lon <= 180:
                            gps_data.append({
                                "time_us": getattr(msg, "TimeUS", 0),
                                "lat": lat,
                                "lon": lon,
                                "alt": alt,
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
            except Exception as e:
                logger.warning(f"Error parsing message {msg_type}: {e}")
                continue

    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        raise ValueError(f"Error reading log file: {e}")
    finally:
        log.close()

    gps_df = pd.DataFrame(gps_data)
    imu_df = pd.DataFrame(imu_data)
    
    logger.info(f"Parsed {messages_parsed} messages: {len(gps_df)} GPS, {len(imu_df)} IMU")
    
    if gps_df.empty and imu_df.empty:
        raise ValueError("No GPS or IMU data found in log file")

    return gps_df, imu_df