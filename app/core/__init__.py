"""Core analysis modules for ArduPilot Flight Log Analyzer"""

from .parser import ArduPilotLogParser, parse_ardupilot_log
from .coordinates import wgs84_to_ecef, ecef_to_enu
from .metrics import (
    compute_total_distance_haversine,
    compute_speed_components,
    compute_max_acceleration,
    compute_max_altitude_gain,
    compute_duration,
    haversine
)
from .integration import compute_velocity_from_acc, trapezoidal_integration
from .visualization import plot_3d_trajectory, plot_2d_top_view, plot_altitude_profile, plot_flight_map
from .utils import merge_gps_coordinates, export_csv, export_json, create_summary_report
from .ai_analysis import analyze_flight_with_ai, format_analysis_for_display, fallback_flight_analysis
from theory import (
    quaternion_from_euler,
    euler_from_quaternion,
    quaternion_multiply,
    estimate_bias_from_data
)

__all__ = [
    "ArduPilotLogParser",
    "parse_ardupilot_log",
    "wgs84_to_ecef",
    "ecef_to_enu",
    "compute_total_distance_haversine",
    "compute_speed_components",
    "compute_max_acceleration",
    "compute_max_altitude_gain",
    "compute_duration",
    "haversine",
    "compute_velocity_from_acc",
    "trapezoidal_integration",
    "plot_3d_trajectory",
    "plot_2d_top_view",
    "plot_altitude_profile",
    "plot_flight_map",
    "merge_gps_coordinates",
    "export_csv",
    "export_json",
    "create_summary_report",
    "analyze_flight_with_ai",
    "format_analysis_for_display",
    "fallback_flight_analysis",
    "quaternion_from_euler",
    "euler_from_quaternion",
    "quaternion_multiply",
    "estimate_bias_from_data"
]
