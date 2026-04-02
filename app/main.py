import sys
import os
import numpy as np
import logging
from pathlib import Path

# Add core directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from parser import parse_ardupilot_log
from coordinates import wgs84_to_ecef, ecef_to_enu
from metrics import (
    compute_total_distance_haversine,
    compute_speed_components,
    compute_max_acceleration,
    compute_max_altitude_gain,
    compute_duration
)
from integration import compute_velocity_from_acc
from visualization import plot_3d_trajectory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main(log_path):
    """
    Main function to analyze ArduPilot flight log.
    
    Args:
        log_path: Path to .BIN or .LOG file
    """
    
    log_path = Path(log_path)
    
    # Validate file exists
    if not log_path.exists():
        logger.error(f"File not found: {log_path}")
        return False
    
    if log_path.suffix.lower() not in ['.bin', '.log']:
        logger.error(f"Invalid file type: {log_path.suffix}. Expected .BIN or .LOG")
        return False
    
    try:
        logger.info(f"Parsing log: {log_path}")
        gps_df, imu_df = parse_ardupilot_log(str(log_path))

        if gps_df.empty:
            logger.error("No GPS data found in log file.")
            return False

        logger.info(f"Parsed {len(gps_df)} GPS records and {len(imu_df)} IMU records")

        # === CALCULATIONS ===
        
        logger.info("Computing flight metrics...")
        
        # Distance (HAVERSINE)
        total_distance = compute_total_distance_haversine(gps_df)

        # Speeds from GPS
        horizontal_speed, vertical_speed = compute_speed_components(gps_df)
        gps_df["speed"] = horizontal_speed

        max_horizontal_speed = np.nanmax(horizontal_speed)
        max_vertical_speed = np.nanmax(np.abs(vertical_speed))

        # Acceleration
        max_acc = compute_max_acceleration(imu_df) if not imu_df.empty else 0.0

        # Altitude
        max_alt_gain = compute_max_altitude_gain(gps_df)

        # Duration
        duration = compute_duration(gps_df)

        # IMU integration (trapezoidal)
        if not imu_df.empty:
            vx, vy, vz = compute_velocity_from_acc(imu_df)
        else:
            logger.warning("No IMU data available")
            vx, vy, vz = None, None, None

        # === OUTPUT RESULTS ===
        
        print("\n" + "="*50)
        print("FLIGHT ANALYSIS SUMMARY")
        print("="*50)
        print(f"Log file: {log_path.name}")
        print("-"*50)
        
        print("\nTiming:")
        print(f"  Duration: {duration:.2f} s")
        
        print("\nDistance & Speed:")
        print(f"  Total distance (Haversine): {total_distance:.2f} m")
        print(f"  Max horizontal speed: {max_horizontal_speed:.2f} m/s")
        print(f"  Max vertical speed: {max_vertical_speed:.2f} m/s")
        
        print("\nAltitude:")
        print(f"  Max altitude gain: {max_alt_gain:.2f} m")
        print(f"  Altitude range: {gps_df['alt'].min():.2f} - {gps_df['alt'].max():.2f} m")
        
        if not imu_df.empty:
            print("\nAcceleration:")
            print(f"  Max acceleration: {max_acc:.2f} m/s^2")
            
            if vx is not None:
                total_velocity = np.sqrt(vx**2 + vy**2 + vz**2)
                print(f"  Max integrated velocity: {np.max(total_velocity):.2f} m/s")
        
        print("\nData Summary:")
        print(f"  GPS samples: {len(gps_df)}")
        print(f"  IMU samples: {len(imu_df)}")
        print("="*50 + "\n")

        # Convert to ENU
        logger.info("Converting coordinates to ENU...")
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

        # Create visualization
        logger.info("Creating 3D visualization...")
        fig = plot_3d_trajectory(gps_df, color_mode="speed")
        
        # Save visualization
        output_path = log_path.parent / f"{log_path.stem}_trajectory.html"
        fig.write_html(str(output_path))
        logger.info(f"Saved visualization to: {output_path}")

        # Export data
        csv_path = log_path.parent / f"{log_path.stem}_processed.csv"
        gps_df.to_csv(str(csv_path), index=False)
        logger.info(f"Saved processed GPS data to: {csv_path}")

        return True

    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        return False
    except ValueError as e:
        logger.error(f"Data error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return False


def print_usage():
    """Print usage information."""
    print("ArduPilot Flight Log Analyzer")
    print("-" * 40)
    print(f"Usage: python {sys.argv[0]} <logfile.BIN|.LOG>")
    print("\nExample:")
    print(f"  python {sys.argv[0]} flight_log.BIN")
    print(f"  python {sys.argv[0]} /path/to/log_file.LOG")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    success = main(sys.argv[1])
    sys.exit(0 if success else 1)