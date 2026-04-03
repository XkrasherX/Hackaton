import numpy as np
import pandas as pd
import pymap3d as pm
from scipy.integrate import cumulative_trapezoid

def haversine(lat1, lon1, lat2, lon2) -> float:
    """Обчислення дистанції на сфері (гаверсинус)."""
    R = 6371000
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)

    a = np.sin(delta_phi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0) ** 2
    return R * (2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a)))

def wgs84_to_enu(lat, lon, alt, lat0, lon0, alt0) -> tuple:
    """Конвертація WGS84 -> ENU."""
    return pm.geodetic2enu(lat, lon, alt, lat0, lon0, alt0)

def trapezoidal_integration(data_array, time_array) -> np.ndarray:
    """Інтегрування методом трапецій з валідацією розмірностей."""
    if len(data_array) != len(time_array):
        raise ValueError("Масиви даних та часу повинні мати однакову довжину.")
    if len(time_array) < 2:
        return np.zeros_like(data_array)  # Захист від порожніх інтервалів
    
    return cumulative_trapezoid(data_array, time_array, initial=0)

def calculate_kinematics(df_gps: pd.DataFrame, df_imu: pd.DataFrame) -> dict:
    """ Обчислення кінематичних показників з повною перевіркою даних. """
    # 1. Базова перевірка наявності даних
    if df_gps is None or df_gps.empty:
        raise ValueError("GPS дані відсутні або порожні.")
    if df_imu is None or df_imu.empty:
        raise ValueError("IMU дані відсутні або порожні.")

    # 2. Перевірка структури даних (захист від неповного парсингу)
    req_imu_cols = {'AccX', 'AccY', 'AccZ', 'Time'}
    req_gps_cols = {'Alt', 'Time'}
    
    if not req_imu_cols.issubset(df_imu.columns):
        raise ValueError(f"В IMU не вистачає колонок. Очікуються: {req_imu_cols}")
    if not req_gps_cols.issubset(df_gps.columns):
        raise ValueError(f"В GPS не вистачає колонок. Очікуються: {req_gps_cols}")

    # 3. Очищення даних: видалення дублікатів часу, NaNs та сортування
    df_imu = df_imu.dropna(subset=list(req_imu_cols)).drop_duplicates(subset=['Time']).sort_values('Time')
    df_gps = df_gps.dropna(subset=list(req_gps_cols)).sort_values('Time')

    if len(df_imu) < 2 or len(df_gps) < 2:
        raise ValueError("Недостатньо валідних точок для інтегрування (мінімум 2).")

    # 4. Розрахунок прискорень
    accel_mag = np.sqrt(df_imu['AccX']**2 + df_imu['AccY']**2 + df_imu['AccZ']**2)
    accel_horiz = np.sqrt(df_imu['AccX']**2 + df_imu['AccY']**2)
    
    # Компенсація гравітації для чистої вертикальної швидкості
    accel_vert = df_imu['AccZ'] - 9.81 

    # 5. Інтегрування прискорень [cite: 19]
    vel_horiz = trapezoidal_integration(accel_horiz, df_imu['Time'])
    vel_vert = trapezoidal_integration(accel_vert, df_imu['Time'])

    # 6. Безпечне формування результату (nanmax ігнорує можливі NaN)
    return {
        "max_vel_horiz": float(np.nanmax(vel_horiz)),
        "max_vel_vert": float(np.nanmax(np.abs(vel_vert))),
        "max_accel": float(np.nanmax(accel_mag)),
        "max_alt_gain": float(df_gps['Alt'].max() - df_gps['Alt'].min()),
        "flight_duration": float(df_gps['Time'].max() - df_gps['Time'].min()),
        "total_distance": 0.0  # Розраховується окремо через координати
    }