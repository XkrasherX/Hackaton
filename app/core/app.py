import streamlit as st
import pandas as pd
import numpy as np
import tempfile
import os

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


st.set_page_config(layout="wide")
st.title("🚀 ArduPilot Flight Log Analyzer")


uploaded_file = st.file_uploader(
    "Завантажте .BIN або .LOG файл",
    type=["bin", "log"]
)

if uploaded_file is not None:

    # Зберігаємо тимчасово файл
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name

    st.success("Файл успішно завантажено!")

    with st.spinner("Парсинг лог-файлу..."):
        gps_df, imu_df = parse_ardupilot_log(tmp_path)

    # Безпечне видалення
    try:
        os.remove(tmp_path)
    except PermissionError:
        pass

    if gps_df.empty:
        st.error("GPS дані не знайдені в лог-файлі.")
        st.stop()

    # === РОЗРАХУНКИ ===

    total_distance = compute_total_distance_haversine(gps_df)

    horizontal_speed, vertical_speed = compute_speed_components(gps_df)
    gps_df["speed"] = horizontal_speed

    max_horizontal_speed = np.nanmax(horizontal_speed)
    max_vertical_speed = np.nanmax(np.abs(vertical_speed))

    max_acc = compute_max_acceleration(imu_df)
    max_alt_gain = compute_max_altitude_gain(gps_df)
    duration = compute_duration(gps_df)

    # ENU
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

    # === ВІДОБРАЖЕННЯ МЕТРИК ===

    st.subheader("📊 Підсумкові метрики місії")

    col1, col2, col3 = st.columns(3)

    col1.metric("Тривалість польоту", f"{duration:.2f} с")
    col1.metric("Загальна дистанція", f"{total_distance:.2f} м")

    col2.metric("Макс горизонтальна швидкість", f"{max_horizontal_speed:.2f} м/с")
    col2.metric("Макс вертикальна швидкість", f"{max_vertical_speed:.2f} м/с")

    col3.metric("Макс прискорення", f"{max_acc:.2f} м/с²")
    col3.metric("Макс набір висоти", f"{max_alt_gain:.2f} м")

    # === 3D ВІЗУАЛІЗАЦІЯ ===

    st.subheader("🧭 3D траєкторія польоту (ENU)")

    color_mode = st.selectbox(
        "Колорування траєкторії:",
        ["speed", "time"]
    )

    fig = plot_3d_trajectory(gps_df, color_mode=color_mode)

    st.plotly_chart(fig, use_container_width=True)