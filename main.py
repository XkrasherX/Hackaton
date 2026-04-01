import os
import tempfile
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pymavlink import mavutil
import pymap3d as pm
from scipy.integrate import cumulative_trapezoid


# --- 1. МАТЕМАТИЧНЕ ЯДРО ---

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


# --- 2. ПАРСИНГ ТЕЛЕМЕТРІЇ ---

def parse_ardupilot_log(file_path):
    """Витягує повідомлення GPS та IMU з бінарного логу [cite: 16, 17]"""
    mlog = mavutil.mavlink_connection(file_path)

    gps_data = []
    imu_data = []

    while True:
        msg = mlog.recv_match(type=['GPS', 'IMU'], blocking=False)
        if msg is None:
            break

        msg_type = msg.get_type()
        timestamp = msg._timestamp

        if msg_type == 'GPS':
            gps_data.append({
                'Time': timestamp,
                'Lat': msg.Lat,
                'Lng': msg.Lng,
                'Alt': msg.Alt
            })
        elif msg_type == 'IMU':
            imu_data.append({
                'Time': timestamp,
                'AccX': msg.AccX,
                'AccY': msg.AccY,
                'AccZ': msg.AccZ
            })

    df_gps = pd.DataFrame(gps_data)
    df_imu = pd.DataFrame(imu_data)
    return df_gps, df_imu


# --- 3. STREAMLIT UI ТА ЛОГІКА ---

st.set_page_config(page_title="UAV Telemetry Analyzer", layout="wide")
st.title("Система аналізу телеметрії та 3D-візуалізації польотів БПЛА [cite: 5]")

uploaded_file = st.file_uploader("Завантажте бінарний лог-файл (.bin/.log) [cite: 24]", type=['bin', 'log'])

if uploaded_file is not None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bin") as tmp_file:
        tmp_file.write(uploaded_file.getbuffer())
        temp_path = tmp_file.name

    with st.spinner('Парсинг сирих бінарних даних...'):
        df_gps, df_imu = parse_ardupilot_log(temp_path)

    if not df_gps.empty and not df_imu.empty:
        # Обробка GPS даних (перетворення форматів, якщо потрібно)
        # В Ardupilot Lat/Lng зазвичай в 1e7
        df_gps['Lat'] = df_gps['Lat'] / 1e7
        df_gps['Lng'] = df_gps['Lng'] / 1e7

        # Обчислення дистанції (Haversine) [cite: 19]
        total_distance = 0
        for i in range(1, len(df_gps)):
            total_distance += haversine(
                df_gps['Lat'].iloc[i - 1], df_gps['Lng'].iloc[i - 1],
                df_gps['Lat'].iloc[i], df_gps['Lng'].iloc[i]
            )

        # Обчислення швидкостей через інтегрування IMU [cite: 19]
        # Для простоти беремо модуль прискорення
        accel_mag = np.sqrt(df_imu['AccX'] ** 2 + df_imu['AccY'] ** 2 + df_imu['AccZ'] ** 2)
        velocity_array = trapezoidal_integration(accel_mag, df_imu['Time'])

        # Підсумкові метрики [cite: 18]
        max_speed = np.max(velocity_array)
        max_accel = np.max(accel_mag)
        max_alt_gain = df_gps['Alt'].max() - df_gps['Alt'].min()
        flight_duration = df_gps['Time'].max() - df_gps['Time'].min()

        st.subheader("Ключові кінематичні показники [cite: 18]")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Пройдена дистанція", f"{total_distance:.2f} м")
        col2.metric("Макс. швидкість (IMU)", f"{max_speed:.2f} м/с")
        col3.metric("Макс. прискорення", f"{max_accel:.2f} м/с²")
        col4.metric("Набір висоти", f"{max_alt_gain:.2f} м")
        col5.metric("Тривалість польоту", f"{flight_duration:.2f} с")

        # Перетворення координат WGS-84 -> ENU [cite: 21]
        lat0, lon0, alt0 = df_gps['Lat'].iloc[0], df_gps['Lng'].iloc[0], df_gps['Alt'].iloc[0]
        enu_coords = df_gps.apply(lambda row: wgs84_to_enu(row['Lat'], row['Lng'], row['Alt'], lat0, lon0, alt0),
                                  axis=1)
        df_gps['E'], df_gps['N'], df_gps['U'] = zip(*enu_coords)

        st.subheader("3D Просторова траєкторія (ENU) [cite: 20]")
        # Побудова графіка з висотою як третьою віссю та динамічним колоруванням [cite: 22]
        fig = px.line_3d(df_gps, x='E', y='N', z='U', color='Time',
                         labels={'E': 'East (m)', 'N': 'North (m)', 'U': 'Up (m)'},
                         title="Траєкторія руху БПЛА відносно точки старту")
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.error("Не вдалося знайти GPS або IMU повідомлення у файлі.")