import numpy as np
from pyproj import Transformer


def wgs84_to_ecef(lat, lon, alt):
    transformer = Transformer.from_crs(
        "epsg:4326", "epsg:4978", always_xy=True
    )
    x, y, z = transformer.transform(lon, lat, alt)
    return np.array(x), np.array(y), np.array(z)


def ecef_to_enu(x, y, z, ref_lat, ref_lon, ref_alt):
    transformer = Transformer.from_crs(
        "epsg:4326", "epsg:4978", always_xy=True
    )

    ref_x, ref_y, ref_z = transformer.transform(
        ref_lon, ref_lat, ref_alt
    )

    dx = x - ref_x
    dy = y - ref_y
    dz = z - ref_z

    # rotation matrix
    lat_rad = np.radians(ref_lat)
    lon_rad = np.radians(ref_lon)

    R = np.array([
        [-np.sin(lon_rad), np.cos(lon_rad), 0],
        [-np.sin(lat_rad) * np.cos(lon_rad),
         -np.sin(lat_rad) * np.sin(lon_rad),
         np.cos(lat_rad)],
        [np.cos(lat_rad) * np.cos(lon_rad),
         np.cos(lat_rad) * np.sin(lon_rad),
         np.sin(lat_rad)]
    ])

    enu = R @ np.vstack((dx, dy, dz))

    return enu[0], enu[1], enu[2]