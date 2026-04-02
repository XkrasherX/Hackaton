#!/usr/bin/env python3
"""
Example script demonstrating ArduPilot Flight Log Analyzer usage.

This script shows how to use the analyzer library to parse logs,
compute metrics, and create visualizations.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core import (
    parse_ardupilot_log,
    compute_total_distance_haversine,
    compute_speed_components,
    compute_max_acceleration,
    compute_max_altitude_gain,
    compute_duration,
    wgs84_to_ecef,
    ecef_to_enu,
    plot_3d_trajectory,
    create_summary_report,
    export_csv
)


def analyze_flight_log(log_path):
    """
    Analyze ArduPilot flight log and generate report.
    
    Args:
        log_path: Path to log file (.BIN or .LOG)
    """
    
    log_path = Path(log_path)
    
    print(f"\n📖 Analyzing: {log_path.name}")
    print("=" * 70)
    
    # Parse log file
    print("\n[1] Parsing log file...")
    gps_df, imu_df = parse_ardupilot_log(str(log_path))
    print(f"    ✓ {len(gps_df)} GPS records, {len(imu_df)} IMU records")
    
    # Compute metrics
    print("\n[2] Computing metrics...")
    
    total_distance = compute_total_distance_haversine(gps_df)
    h_speed, v_speed = compute_speed_components(gps_df)
    gps_df["speed"] = h_speed
    max_h_speed = h_speed.max()
    max_v_speed = abs(v_speed).max()
    
    max_acc = compute_max_acceleration(imu_df) if not imu_df.empty else 0
    max_alt_gain = compute_max_altitude_gain(gps_df)
    duration = compute_duration(gps_df)
    
    print(f"    ✓ Metrics computed")
    
    # Coordinate transformation
    print("\n[3] Converting coordinates (WGS84 → ENU)...")
    x, y, z = wgs84_to_ecef(gps_df["lat"], gps_df["lon"], gps_df["alt"])
    east, north, up = ecef_to_enu(
        x, y, z,
        gps_df["lat"].iloc[0],
        gps_df["lon"].iloc[0],
        gps_df["alt"].iloc[0]
    )
    gps_df["east"] = east
    gps_df["north"] = north
    gps_df["up"] = up
    print(f"    ✓ Coordinates transformed")
    
    # Create summary
    print("\n[4] Creating analysis report...")
    metrics = {
        "Total Distance": total_distance,
        "Max Horizontal Speed": max_h_speed,
        "Max Vertical Speed": max_v_speed,
        "Max Acceleration": max_acc,
        "Max Altitude Gain": max_alt_gain,
        "Flight Duration (s)": duration
    }
    
    report = create_summary_report(gps_df, imu_df, metrics)
    print(report)
    
    # Create visualization
    print("\n[5] Creating 3D visualization...")
    fig = plot_3d_trajectory(gps_df, color_mode="speed")
    
    # Save outputs
    html_path = log_path.parent / f"{log_path.stem}_trajectory.html"
    csv_path = log_path.parent / f"{log_path.stem}_analysis.csv"
    
    fig.write_html(str(html_path))
    gps_df.to_csv(str(csv_path), index=False)
    
    print(f"    ✓ Saved visualization: {html_path.name}")
    print(f"    ✓ Saved data: {csv_path.name}")
    
    print("\n" + "=" * 70)
    print("✅ Analysis complete!")
    

if __name__ == "__main__":
    
    if len(sys.argv) < 2:
        print("ArduPilot Flight Log Analyzer - Example")
        print("-" * 70)
        print(f"Usage: python {sys.argv[0]} <log_file.BIN>")
        print(f"\nExample: python {sys.argv[0]} data/00000001.BIN")
        sys.exit(1)
    
    log_file = sys.argv[1]
    
    try:
        analyze_flight_log(log_file)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
