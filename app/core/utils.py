import pandas as pd
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def merge_gps_coordinates(gps_df, east, north, up):

    #Merge ENU coordinates with GPS data.

    gps_df = gps_df.copy()
    gps_df["east"] = east
    gps_df["north"] = north
    gps_df["up"] = up
    return gps_df


def export_csv(df, filename="flight_data.csv"):

    #Export DataFrame to CSV file.

    try:
        path = Path(filename)
        df.to_csv(path, index=False)
        logger.info(f"Data exported to {path}")
        return str(path)
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        raise


def export_json(df, filename="flight_data.json"):

    #Export DataFrame to JSON file.

    try:
        path = Path(filename)
        df.to_json(path, orient='records')
        logger.info(f"Data exported to {path}")
        return str(path)
    except Exception as e:
        logger.error(f"Error exporting JSON: {e}")
        raise


def create_summary_report(gps_df, imu_df, metrics):

    #Create a summary report of flight analysis.

    report = []
    report.append("="*60)
    report.append("FLIGHT ANALYSIS REPORT")
    report.append("="*60)
    
    report.append("\nDATA SUMMARY:")
    report.append(f"  GPS Records: {len(gps_df)}")
    report.append(f"  IMU Records: {len(imu_df)}")
    
    report.append("\nFLIGHT METRICS:")
    for key, value in metrics.items():
        if isinstance(value, float):
            report.append(f"  {key}: {value:.2f}")
        else:
            report.append(f"  {key}: {value}")
    
    report.append("\nALTITUDE STATISTICS:")
    report.append(f"  Min: {gps_df['alt'].min():.2f} m")
    report.append(f"  Max: {gps_df['alt'].max():.2f} m")
    report.append(f"  Mean: {gps_df['alt'].mean():.2f} m")
    
    report.append("="*60)
    
    return "\n".join(report)