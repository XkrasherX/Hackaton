import numpy as np
import pymap3d as pm
from scipy.integrate import cumulative_trapezoid

def haversine(lat1, lon1, lat2, lon2):
    """Обчислення дистанції на сфері за формулою гаверсинусів [cite: 19]"""
    R = 6371000  # Радіус Землі в метрах
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    delta_phi = np.radians(lat2 - lat1)
    delta_lambda = np.radians(lon2 - lon1)

    a = np.sin(delta_phi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(delta_lambda / 2.0) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c

def trapezoidal_integration(accel_array, time_array):
    """Чисельне інтегрування методом трапецій для знаходження швидкості [cite: 19]"""
    # Початкова швидкість 0. Інтегруємо прискорення по часу.
    velocity = cumulative_trapezoid(accel_array, time_array, initial=0)
    return velocity


def wgs84_to_enu(lat, lon, alt, lat0, lon0, alt0):
    """Конвертація глобальних координат у локальну декартову систему ENU [cite: 21]"""
    # Використовуємо pymap3d для точної математичної конвертації
    e, n, u = pm.geodetic2enu(lat, lon, alt, lat0, lon0, alt0)
    return e, n, u