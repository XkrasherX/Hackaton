import numpy as np
from pyproj import Transformer
import logging

logger = logging.getLogger(__name__)


def wgs84_to_ecef(lat, lon, alt):
    """
    Convert WGS84 geographic coordinates to ECEF (Earth-Centered, Earth-Fixed).
    
    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        alt: Altitude in meters
        
    Returns:
        tuple: (x, y, z) ECEF coordinates in meters
    """
    try:
        transformer = Transformer.from_crs(
            "epsg:4326", "epsg:4978", always_xy=True
        )
        x, y, z = transformer.transform(lon, lat, alt)
        return np.array(x), np.array(y), np.array(z)
    except Exception as e:
        logger.error(f"Error in WGS84 to ECEF conversion: {e}")
        raise


def ecef_to_enu(x, y, z, ref_lat, ref_lon, ref_alt):
    """
    Convert ECEF coordinates to ENU (East-North-Up) local coordinates.
    
    Args:
        x, y, z: ECEF coordinates in meters
        ref_lat: Reference latitude in degrees
        ref_lon: Reference longitude in degrees
        ref_alt: Reference altitude in meters
        
    Returns:
        tuple: (east, north, up) ENU coordinates relative to reference point in meters
    """
    try:
        transformer = Transformer.from_crs(
            "epsg:4326", "epsg:4978", always_xy=True
        )

        # Get reference point in ECEF
        ref_x, ref_y, ref_z = transformer.transform(
            ref_lon, ref_lat, ref_alt
        )

        # Compute ECEF deltas
        dx = x - ref_x
        dy = y - ref_y
        dz = z - ref_z

        # Build rotation matrix from geodetic coordinates
        lat_rad = np.radians(ref_lat)
        lon_rad = np.radians(ref_lon)

        # Rotation matrix from ECEF to ENU
        # Formula from: https://en.wikipedia.org/wiki/Geographic_coordinate_system#Local_tangent_plane
        R = np.array([
            [-np.sin(lon_rad), np.cos(lon_rad), 0],
            [-np.sin(lat_rad) * np.cos(lon_rad),
             -np.sin(lat_rad) * np.sin(lon_rad),
             np.cos(lat_rad)],
            [np.cos(lat_rad) * np.cos(lon_rad),
             np.cos(lat_rad) * np.sin(lon_rad),
             np.sin(lat_rad)]
        ])

        # Apply rotation
        enu = R @ np.vstack((dx, dy, dz))

        return enu[0], enu[1], enu[2]
    except Exception as e:
        logger.error(f"Error in ECEF to ENU conversion: {e}")
        raise