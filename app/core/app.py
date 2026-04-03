import streamlit as st
import pandas as pd
import numpy as np
import tempfile
import os
import logging
import plotly.graph_objects as go

from parser import parse_ardupilot_log, ArduPilotLogParser
from coordinates import wgs84_to_ecef, ecef_to_enu
from metrics import (
    compute_total_distance_haversine,
    compute_speed_components,
    compute_max_acceleration,
    compute_max_altitude_gain,
    compute_duration
)
from integration import compute_velocity_from_acc
from visualization import plot_3d_trajectory, plot_2d_top_view, plot_altitude_profile, plot_flight_map
from ai_analysis import analyze_flight_with_ai, format_analysis_for_display

try:
    import streamlit_folium
except ImportError:
    streamlit_folium = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config (MUST be first Streamlit command)
st.set_page_config(
    page_title="ArduPilot Flight Analyzer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# DARK THEME - APPLIED GLOBALLY
# =====================================================

# Dark theme colors
DARK_THEME = {
    "bg_primary": "#0f172a",      # Main background
    "bg_secondary": "#1e293b",    # Cards, containers
    "bg_tertiary": "#334155",     # Hover, borders
    "text_primary": "#f1f5f9",    # Main text
    "text_secondary": "#cbd5e1",  # Secondary text
    "accent": "#3b82f6",          # Primary accent (blue)
    "success": "#10b981",         # Success green
    "warning": "#f59e0b",         # Warning orange
    "error": "#ef4444",           # Error red
}

# Apply dark theme globally
st.markdown(
    f"""
    <style>
    /* Root variables */
    :root {{
        --bg-primary: {DARK_THEME['bg_primary']};
        --bg-secondary: {DARK_THEME['bg_secondary']};
        --bg-tertiary: {DARK_THEME['bg_tertiary']};
        --text-primary: {DARK_THEME['text_primary']};
        --text-secondary: {DARK_THEME['text_secondary']};
        --accent: {DARK_THEME['accent']};
    }}

    /* Main app background */
    html, body {{
        background-color: {DARK_THEME['bg_primary']} !important;
        color: {DARK_THEME['text_primary']} !important;
    }}

    .stApp {{
        background-color: {DARK_THEME['bg_primary']} !important;
    }}

    [data-testid="stAppViewContainer"] {{
        background-color: {DARK_THEME['bg_primary']} !important;
    }}

    /* Sidebar */
    [data-testid="stSidebar"] {{
        background-color: {DARK_THEME['bg_secondary']} !important;
    }}

    [data-testid="stSidebar"] > div {{
        background-color: {DARK_THEME['bg_secondary']} !important;
    }}

    /* Text elements */
    body, .stMarkdown, .stText, p, span, div {{
        color: {DARK_THEME['text_primary']} !important;
    }}

    /* Headers */
    h1, h2, h3, h4, h5, h6 {{
        color: {DARK_THEME['accent']} !important;
    }}

    /* Metric containers */
    [data-testid="metric-container"] {{
        background-color: {DARK_THEME['bg_secondary']} !important;
        border-left: 4px solid {DARK_THEME['accent']} !important;
    }}

    /* Buttons */
    .stButton > button {{
        background-color: {DARK_THEME['accent']} !important;
        color: white !important;
        border: none !important;
    }}

    .stButton > button:hover {{
        background-color: #2563eb !important;
    }}

    /* Input fields */
    input, textarea, select {{
        background-color: {DARK_THEME['bg_secondary']} !important;
        color: {DARK_THEME['text_primary']} !important;
        border: 1px solid {DARK_THEME['bg_tertiary']} !important;
    }}

    input::placeholder {{
        color: {DARK_THEME['text_secondary']} !important;
    }}

    /* Expander */
    .streamlit-expanderHeader {{
        background-color: {DARK_THEME['bg_secondary']} !important;
        color: {DARK_THEME['text_primary']} !important;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        background-color: {DARK_THEME['bg_secondary']} !important;
    }}

    .stTabs [data-baseweb="tab"] {{
        color: {DARK_THEME['text_secondary']} !important;
    }}

    .stTabs [aria-selected="true"] {{
        color: {DARK_THEME['accent']} !important;
    }}

    /* Checkboxes and radio buttons */
    .stCheckbox > label {{
        color: {DARK_THEME['text_primary']} !important;
    }}

    /* Select box */
    .stSelectbox > div > div {{
        background-color: {DARK_THEME['bg_secondary']} !important;
        color: {DARK_THEME['text_primary']} !important;
        border: 1px solid {DARK_THEME['bg_tertiary']} !important;
    }}

    /* Slider */
    .stSlider > div > div > div {{
        color: {DARK_THEME['text_primary']} !important;
    }}

    /* Tooltip and help text */
    [data-tooltip] {{
        background-color: {DARK_THEME['bg_secondary']} !important;
        color: {DARK_THEME['text_primary']} !important;
        border: 1px solid {DARK_THEME['bg_tertiary']} !important;
    }}

    /* Info, warning, error boxes */
    .stAlert {{
        background-color: {DARK_THEME['bg_secondary']} !important;
        color: {DARK_THEME['text_primary']} !important;
        border-left: 4px solid {DARK_THEME['accent']} !important;
    }}

    /* Success box */
    .success-box {{
        background-color: rgba(16, 185, 129, 0.1) !important;
        color: {DARK_THEME['success']} !important;
        border-left: 4px solid {DARK_THEME['success']} !important;
        padding: 15px !important;
        border-radius: 5px !important;
    }}

    /* Warning box */
    .warning-box {{
        background-color: rgba(245, 158, 11, 0.1) !important;
        color: {DARK_THEME['warning']} !important;
        border-left: 4px solid {DARK_THEME['warning']} !important;
        padding: 15px !important;
        border-radius: 5px !important;
    }}

    /* Danger box */
    .danger-box {{
        background-color: rgba(239, 68, 68, 0.1) !important;
        color: {DARK_THEME['error']} !important;
        border-left: 4px solid {DARK_THEME['error']} !important;
        padding: 15px !important;
        border-radius: 5px !important;
    }}

    /* Table styling */
    .stDataFrame {{
        background-color: {DARK_THEME['bg_secondary']} !important;
    }}

    .dataframe {{
        background-color: {DARK_THEME['bg_secondary']} !important;
        color: {DARK_THEME['text_primary']} !important;
    }}

    /* Links */
    a {{
        color: {DARK_THEME['accent']} !important;
    }}

    a:hover {{
        color: #2563eb !important;
    }}

    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("""
<h1 style='text-align: center;'>🚀 ArduPilot Flight Log Analyzer</h1>
<p style='text-align: center; font-size:18px;'>
Professional drone telemetry analysis platform
</p>
""", unsafe_allow_html=True)

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
    
    st.markdown("---")
    st.header("🔗 Links")

    st.markdown("[GitHub](https://github.com/XkrasherX/Hackaton.git)")
    st.markdown("[Documentation](https://github.com/XkrasherX/Hackaton/blob/master/README.md)")
    st.markdown("[Support](https://github.com/Nestors1234/ArduPilot-Flight-Log-Analyzer/issues)")
    
    st.markdown("---")
    st.markdown("""
    <small> **ArduPilot Flight Log Analyzer**  
    Advanced analysis tool for drone flight logs  
    Version 0.4 | April 2026</small>
    """, unsafe_allow_html=True)

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

    st.success("[OK] File uploaded successfully!")

    # Parse log file
    try:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("Parsing log file...")
        progress_bar.progress(10)
        
        parser = ArduPilotLogParser(tmp_path)
        gps_df, imu_df, att_df, pid_df, sampling_info, meta_info = parser.parse()

        # Rename columns for consistency with metrics functions
        gps_df = gps_df.rename(columns={
            "Lat_deg": "lat",
            "Lon_deg": "lon",
            "Alt_m": "alt",
            "TimeUS": "time_us"
        })
        imu_df = imu_df.rename(columns={
            "TimeUS": "time_us",
            "AccX": "acc_x",
            "AccY": "acc_y",
            "AccZ": "acc_z",
            "GyrX": "gyr_x",
            "GyrY": "gyr_y",
            "GyrZ": "gyr_z"
        })
        att_df = att_df.rename(columns={"TimeUS": "time_us"})
        pid_df = pid_df.rename(columns={"TimeUS": "time_us"})

        # Debug: Check raw GPS data
        logger.info(f"Raw GPS records: {len(gps_df)}")
        logger.info(f"GPS columns: {gps_df.columns.tolist() if not gps_df.empty else 'empty'}")
        if not gps_df.empty:
            logger.info(f"GPS null counts: {gps_df.isnull().sum().to_dict()}")

        # Clean GPS data - only require lat and lon
        gps_df = gps_df.dropna(subset=["lat", "lon"])
        
        # Clean IMU data - check for renamed columns
        if "acc_x" in imu_df.columns and "acc_y" in imu_df.columns and "acc_z" in imu_df.columns:
            imu_df = imu_df.dropna(subset=["acc_x", "acc_y", "acc_z"])
        
        # Fill missing altitude values with interpolation
        if "alt" in gps_df.columns:
            gps_df["alt"] = gps_df["alt"].interpolate(method="linear", limit_direction="both")
        
        # Fill missing time_us with forward fill then backward fill
        if "time_us" in gps_df.columns and gps_df["time_us"].isnull().any():
            gps_df["time_us"] = gps_df["time_us"].ffill().bfill()

        # Clean up temporary file
        try:
            os.remove(tmp_path)
        except PermissionError:
            pass

        # Validate data
        if gps_df.empty:
            st.error("[ERROR] No valid GPS data found in log file. Check file format and try another file.")
            logger.error(f"GPS dataframe empty after cleaning. Original size: {len(imu_df)}")
            st.stop()

        logger.info(f"Parsed {len(gps_df)} GPS records and {len(imu_df)} IMU records")
        
        progress_bar.progress(30)
        status_text.text("Computing metrics...")

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
        status_text.text("Converting coordinates...")

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
        status_text.text("Analysis complete!")
        
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

        # === ALTITUDE & SPEED PROFILES ===
        
        with st.expander("🏔️ Altitude Profile Over Time", expanded=False):
            alt_data = pd.DataFrame({
                'Time (s)': (gps_df['time_us'] - gps_df['time_us'].iloc[0]) / 1e6,
                'Altitude (m)': gps_df['alt']
            })
            
            fig_alt = go.Figure()
            fig_alt.add_trace(go.Scatter(
                x=alt_data['Time (s)'],
                y=alt_data['Altitude (m)'],
                mode='lines',
                name='Altitude',
                line=dict(color='#1f77b4', width=2),
                showlegend=True
            ))
            fig_alt.update_layout(
                title="Altitude Profile Over Time",
                xaxis_title="Time (s)",
                yaxis_title="Altitude (m)",
                hovermode='x unified',
                dragmode=False,
                width=None,
                height=400
            )
            st.plotly_chart(fig_alt, use_container_width=True)

        with st.expander("💨 Speed Profile Over Time", expanded=False):
            speed_data = pd.DataFrame({
                'Time (s)': (gps_df['time_us'] - gps_df['time_us'].iloc[0]) / 1e6,
                'Horiz. Speed (m/s)': horizontal_speed,
                'Vert. Speed (m/s)': vertical_speed
            })
            
            fig_speed = go.Figure()
            fig_speed.add_trace(go.Scatter(
                x=speed_data['Time (s)'],
                y=speed_data['Horiz. Speed (m/s)'],
                mode='lines',
                name='Horiz. Speed',
                line=dict(color='#1f77b4', width=2)
            ))
            fig_speed.add_trace(go.Scatter(
                x=speed_data['Time (s)'],
                y=speed_data['Vert. Speed (m/s)'],
                mode='lines',
                name='Vert. Speed',
                line=dict(color='#ff7f0e', width=2, dash='dash')
            ))
            fig_speed.update_layout(
                title="Speed Profile Over Time",
                xaxis_title="Time (s)",
                yaxis_title="Speed (m/s)",
                hovermode='x unified',
                dragmode=False,
                width=None,
                height=400
            )
            st.plotly_chart(fig_speed, use_container_width=True)

        # === VISUALIZATION TABS ===

        st.markdown("## 🗺️ Flight Visualizations")
        
        # Create tabs for different visualization types
        tab1, tab2, tab3, tab4 = st.tabs(["🧭 3D Trajectory", "🗺️ Top View", "📈 Altitude Profile", "🌍 Flight Map"])
        
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
        
        with tab4:
            st.markdown("### Interactive Flight Map")
            
            st.markdown("""
            **🌍 Interactive Map Legend:**
            - 🟢 **Green Marker (START)**: Takeoff location
            - 🔴 **Red Marker (LANDING)**: Landing location
            - 🟠 **Orange Marker (⬆)**: Maximum altitude point
            - 🔵 **Blue Dots & Line**: Flight path with speed indicators (dot size = speed)
            - 📍 **Info Box** (bottom-right): Flight statistics
            """)
            
            try:
                if streamlit_folium:
                    map_flight = plot_flight_map(gps_df)
                    streamlit_folium.folium_static(map_flight)
                else:
                    st.warning("Folium not available. Install with: pip install folium streamlit-folium")
            except Exception as e:
                st.error(f"Error creating flight map: {e}")
                logger.error(f"Flight map error: {e}")

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
                st.success("[OK] No significant anomalies detected")
            
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
        
        col_gps, col_imu, col_combined = st.columns(3)
        
        with col_gps:
            csv_gps = gps_df.to_csv(index=False)
            st.download_button(
                label="📍 GPS Data (CSV)",
                data=csv_gps,
                file_name=f"{os.path.splitext(uploaded_file.name)[0]}_gps.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col_imu:
            if not imu_df.empty:
                csv_imu = imu_df.to_csv(index=False)
                st.download_button(
                    label="📊 IMU Data (CSV)",
                    data=csv_imu,
                    file_name=f"{os.path.splitext(uploaded_file.name)[0]}_imu.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.info("No IMU data available")
        
        with col_combined:
            # Create combined CSV with both GPS and IMU data
            try:
                combined_df = gps_df.merge(
                    imu_df,
                    left_on='time_us',
                    right_on='time_us',
                    how='outer'
                ).sort_values('time_us')
                csv_combined = combined_df.to_csv(index=False)
                st.download_button(
                    label="🔗 All Data (CSV)",
                    data=csv_combined,
                    file_name=f"{os.path.splitext(uploaded_file.name)[0]}_combined.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            except Exception as e:
                st.info("Combined export unavailable")

    except FileNotFoundError as e:
        st.error(f"[ERROR] File error: {e}")
        logger.error(f"File not found: {e}")
    except ValueError as e:
        st.error(f"[ERROR] Data error: {e}")
        logger.error(f"Data validation error: {e}")
    except Exception as e:
        st.error(f"[ERROR] Unexpected error: {e}")
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
**ArduPilot Flight Log Analyzer** |  
[GitHub](https://github.com/XkrasherX/Hackaton.git) • [Documentation](https://github.com/XkrasherX/Hackaton/blob/master/README.md) • [Support](https://github.com)
""")