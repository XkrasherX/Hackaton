import streamlit as st
import pandas as pd
import numpy as np
import tempfile
import os
import logging

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
from visualization import plot_3d_trajectory, plot_2d_top_view, plot_altitude_profile
from ai_analysis import analyze_flight_with_ai, format_analysis_for_display

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="ArduPilot Flight Analyzer",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #28a745;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #ffc107;
    }
    .danger-box {
        background-color: #f8d7da;
        padding: 15px;
        border-radius: 5px;
        border-left: 4px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

st.title("🚀 ArduPilot Flight Log Analyzer")

# Sidebar
with st.sidebar:
    st.header("📋 About")
    st.markdown("""
    Advanced flight log analysis tool for ArduPilot-based systems.
    
    **Features:**
    - Parse binary .BIN and .LOG files
    - Compute flight metrics (distance, speed, acceleration)
    - 3D trajectory visualization
    - AI-powered flight analysis
    - Export processed data
    
    **Supported Formats:**
    - ArduPilot Binary Logs (.BIN)
    - ArduPilot Text Logs (.LOG)
    """)
    
    st.markdown("---")
    st.header("⚙️ Options")
    
    enable_ai = st.checkbox(
        "Enable AI Analysis",
        value=True,
        help="Use LLM to analyze flight patterns and generate insights"
    )
    
    groq_api_key = st.text_input(
        "Groq API Key (Optional)",
        type="password",
        help="Get free key from https://console.groq.com/"
    )

st.markdown("""
**Advanced flight analysis for ArduPilot flight controllers**

Upload your log files to analyze flight characteristics, detect anomalies, and visualize trajectories.
""")

uploaded_file = st.file_uploader(
    "📤 Upload .BIN or .LOG file",
    type=["bin", "log"],
    help="Select your ArduPilot flight log file"
)

if uploaded_file is not None:

    # Save file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
        tmp_file.write(uploaded_file.read())
        tmp_path = tmp_file.name

    st.success("✅ File uploaded successfully!")

    # Parse log file
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("🔍 Parsing log file...")
        progress_bar.progress(10)
        
        gps_df, imu_df = parse_ardupilot_log(tmp_path)

        # Clean up temporary file
        try:
            os.remove(tmp_path)
        except PermissionError:
            pass

        # Validate data
        if gps_df.empty:
            st.error("❌ No GPS data found in log file.")
            st.stop()

        logger.info(f"Parsed {len(gps_df)} GPS records and {len(imu_df)} IMU records")
        
        progress_bar.progress(30)
        status_text.text("📊 Computing metrics...")

        # === CALCULATIONS ===
        
        total_distance = compute_total_distance_haversine(gps_df)

        horizontal_speed, vertical_speed = compute_speed_components(gps_df)
        gps_df["speed"] = horizontal_speed

        max_horizontal_speed = np.nanmax(horizontal_speed)
        max_vertical_speed = np.nanmax(np.abs(vertical_speed))

        max_acc = compute_max_acceleration(imu_df) if not imu_df.empty else 0.0
        max_alt_gain = compute_max_altitude_gain(gps_df)
        duration = compute_duration(gps_df)
        
        progress_bar.progress(50)
        status_text.text("🌍 Converting coordinates...")

        # Convert to ENU coordinate system
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
        
        progress_bar.progress(70)

        # === CREATE METRICS DICTIONARY ===
        metrics = {
            "Total Distance": total_distance,
            "Max Horizontal Speed": max_horizontal_speed,
            "Max Vertical Speed": max_vertical_speed,
            "Max Acceleration": max_acc,
            "Max Altitude Gain": max_alt_gain,
            "Flight Duration (s)": duration
        }
        
        progress_bar.progress(100)
        status_text.text("✅ Analysis complete!")
        
        # Clear progress indicators
        import time
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()

        # === DISPLAY METRICS ===
        
        st.markdown("## 📊 Flight Metrics Dashboard")
        
        # Create columns for metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "⏱️ Flight Duration",
                f"{duration:.2f} s",
                f"{duration/60:.2f} min"
            )
            st.metric(
                "📏 Total Distance",
                f"{total_distance:.2f} m",
                f"{total_distance/1000:.3f} km"
            )

        with col2:
            st.metric(
                "🏃 Max Horiz. Speed",
                f"{max_horizontal_speed:.2f} m/s",
                f"{max_horizontal_speed*3.6:.1f} km/h"
            )
            st.metric(
                "📈 Max Vert. Speed",
                f"{max_vertical_speed:.2f} m/s",
                f"{max_vertical_speed*3.6:.1f} km/h"
            )

        with col3:
            st.metric(
                "⚡ Max Acceleration",
                f"{max_acc:.2f} m/s²",
                f"{max_acc/9.81:.2f}g"
            )
            st.metric(
                "📊 Max Alt. Gain",
                f"{max_alt_gain:.2f} m"
            )

        # Altitude profile
        st.markdown("## 🏔️ Altitude Profile")
        
        alt_data = pd.DataFrame({
            'Time (s)': (gps_df['time_us'] - gps_df['time_us'].iloc[0]) / 1e6,
            'Altitude (m)': gps_df['alt']
        })
        
        st.line_chart(alt_data.set_index('Time (s)'), use_container_width=True)

        # Speed profile
        st.markdown("## 💨 Speed Profile")
        
        speed_data = pd.DataFrame({
            'Time (s)': (gps_df['time_us'] - gps_df['time_us'].iloc[0]) / 1e6,
            'Horiz. Speed (m/s)': horizontal_speed,
            'Vert. Speed (m/s)': vertical_speed
        })
        
        st.line_chart(speed_data.set_index('Time (s)'), use_container_width=True)

        # === VISUALIZATION TABS ===

        st.markdown("## 🗺️ Flight Visualizations")
        
        # Create tabs for different visualization types
        tab1, tab2, tab3 = st.tabs(["🧭 3D Trajectory", "🗺️ Top View", "📈 Altitude Profile"])
        
        with tab1:
            st.markdown("### Interactive 3D Flight Path")
            col_color, col_type = st.columns(2)
            
            with col_color:
                color_mode = st.selectbox(
                    "Trajectory coloring:",
                    ["speed", "time"],
                    help="Color trajectory by speed or elapsed time",
                    key="3d_color"
                )

            try:
                fig = plot_3d_trajectory(gps_df, color_mode=color_mode)
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("""
                **How to use:**
                - 🖱️ **Rotate**: Click and drag to rotate
                - 🔍 **Zoom**: Scroll wheel to zoom in/out
                - 📍 **Pan**: Right-click and drag to move
                - 🏠 **Reset**: Double-click to reset view
                """)
            except Exception as e:
                st.error(f"Error creating 3D visualization: {e}")
                logger.error(f"3D Visualization error: {e}")
        
        with tab2:
            st.markdown("### Flight Path - Birds Eye View")
            col_color2, _ = st.columns(2)
            
            with col_color2:
                color_mode2 = st.selectbox(
                    "Path coloring:",
                    ["speed", "time"],
                    help="Color path by speed or elapsed time",
                    key="2d_color"
                )
            
            try:
                fig2d = plot_2d_top_view(gps_df, color_mode=color_mode2)
                st.plotly_chart(fig2d, use_container_width=True)
                st.markdown("""
                **Top-down view shows:**
                - Direct flight path (East-North plane)
                - Start (🟢 green diamond) and landing point (❌ red cross)
                - Direct distance between start and end
                - Horizontal routing patterns
                """)
            except Exception as e:
                st.error(f"Error creating 2D visualization: {e}")
                logger.error(f"2D Visualization error: {e}")
        
        with tab3:
            st.markdown("### Altitude & Speed Dynamics")
            
            try:
                fig_alt = plot_altitude_profile(gps_df)
                st.plotly_chart(fig_alt, use_container_width=True)
                st.markdown("""
                **Profile Analysis:**
                - 🔵 **Blue line**: Altitude over distance (left axis)
                - 🟠 **Orange dashed line**: Speed over distance (right axis)
                - Shows climb/descent patterns and speed changes
                - Useful for identifying maneuvers and flight phases
                """)
            except Exception as e:
                st.error(f"Error creating altitude profile: {e}")
                logger.error(f"Altitude profile error: {e}")

        # === AI ANALYSIS ===
        
        if enable_ai:
            st.markdown("## 🤖 AI Flight Analysis")
            
            with st.spinner("🔮 Analyzing flight with AI..."):
                analysis = analyze_flight_with_ai(
                    metrics,
                    gps_df,
                    imu_df,
                    api_key=groq_api_key if groq_api_key else None
                )
            
            # Display AI analysis
            st.markdown("### 📋 Summary")
            st.info(analysis.get('summary', ''))
            
            st.markdown("### ⚠️ Anomalies")
            anomalies = analysis.get('anomalies', '')
            if anomalies and "No major anomalies" not in anomalies:
                st.warning(anomalies)
            else:
                st.success("✅ No significant anomalies detected")
            
            st.markdown("### 💡 Recommendations")
            st.success(analysis.get('recommendations', ''))

        # === ADVANCED STATISTICS ===
        
        with st.expander("📈 Advanced Statistics"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**GPS Statistics**")
                st.text(f"Latitude range: {gps_df['lat'].min():.6f} to {gps_df['lat'].max():.6f}°")
                st.text(f"Longitude range: {gps_df['lon'].min():.6f} to {gps_df['lon'].max():.6f}°")
                st.text(f"Altitude range: {gps_df['alt'].min():.2f} to {gps_df['alt'].max():.2f} m")
                st.text(f"Mean altitude: {gps_df['alt'].mean():.2f} m")
                st.text(f"Std dev altitude: {gps_df['alt'].std():.2f} m")
            
            with col2:
                st.markdown("**IMU Statistics**")
                if not imu_df.empty:
                    acc_mag = np.sqrt(imu_df['acc_x']**2 + imu_df['acc_y']**2 + imu_df['acc_z']**2)
                    st.text(f"Mean acceleration: {acc_mag.mean():.2f} m/s²")
                    st.text(f"Std dev accel: {acc_mag.std():.2f} m/s²")
                    st.text(f"Samples per second: {len(imu_df)/duration:.0f} Hz")
                else:
                    st.text("No IMU data available")

        # === DATA EXPORT ===
        
        st.markdown("## 📥 Export Data")
        
        col_gps, col_imu = st.columns(2)
        
        with col_gps:
            csv_gps = gps_df.to_csv(index=False)
            st.download_button(
                label="📥 Download GPS Data (CSV)",
                data=csv_gps,
                file_name=f"{os.path.splitext(uploaded_file.name)[0]}_gps.csv",
                mime="text/csv"
            )
        
        with col_imu:
            if not imu_df.empty:
                csv_imu = imu_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download IMU Data (CSV)",
                    data=csv_imu,
                    file_name=f"{os.path.splitext(uploaded_file.name)[0]}_imu.csv",
                    mime="text/csv"
                )

    except FileNotFoundError as e:
        st.error(f"❌ File error: {e}")
        logger.error(f"File not found: {e}")
    except ValueError as e:
        st.error(f"❌ Data error: {e}")
        logger.error(f"Data validation error: {e}")
    except Exception as e:
        st.error(f"❌ Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}", exc_info=True)
        
        # Clean up on error
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except:
            pass

# Footer
st.markdown("---")
st.markdown("""
**ArduPilot Flight Log Analyzer** | Powered by Python, Streamlit, and AI  
[GitHub](https://github.com) • [Documentation](https://github.com) • [Support](https://github.com)
""")