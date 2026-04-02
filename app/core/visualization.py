import plotly.graph_objects as go
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Create 2D top-down view of flight path.

def plot_2d_top_view(df, color_mode="speed"):

    try:
        # Prepare color values
        if color_mode == "speed" and "speed" in df.columns:
            color_values = df["speed"].values
            color_title = "Speed (m/s)"
            color_scale = "Turbo"
        elif "time_us" in df.columns:
            color_values = (df["time_us"] / 1e6).values
            color_title = "Time (s)"
            color_scale = "Plasma"
        else:
            color_values = np.arange(len(df))
            color_title = "Progress (%)"
            color_scale = "Viridis"
        
        # Handle NaN values properly
        color_values = np.asarray(color_values, dtype=float)
        color_values = np.nan_to_num(color_values, nan=0.0, posinf=0.0, neginf=0.0)
        
        fig = go.Figure()
        
        # === MAIN PATH (line without colorscale) ===
        fig.add_trace(go.Scatter(
            x=df["east"],
            y=df["north"],
            mode='lines',
            line=dict(
                width=3,
                color='rgba(100, 150, 200, 0.6)'
            ),
            name="Flight Path",
            hovertemplate="<b>Position</b><br>East: %{x:.1f} m<br>North: %{y:.1f} m<extra></extra>",
            showlegend=False
        ))
        
        # === PATH MARKERS (with colorscale) ===
        fig.add_trace(go.Scatter(
            x=df["east"],
            y=df["north"],
            mode='markers',
            marker=dict(
                size=6,
                color=color_values,
                colorscale=color_scale,
                colorbar=dict(
                    title=f"<b>{color_title}</b>",
                    thickness=20,
                    len=0.7
                ),
                showscale=True,
                opacity=0.7
            ),
            name="Progress",
            hovertemplate="<b>Position</b><br>East: %{x:.1f} m<br>North: %{y:.1f} m<extra></extra>",
            showlegend=False
        ))
        
        # === START ===
        fig.add_trace(go.Scatter(
            x=[df["east"].iloc[0]],
            y=[df["north"].iloc[0]],
            mode='markers+text',
            marker=dict(size=15, color='#00CC00', symbol='diamond', line=dict(color='darkgreen', width=2)),
            text=['START'],
            textposition="top center",
            textfont=dict(size=11, color='darkgreen', family='Arial Black'),
            name='Start',
            hovertemplate="<b>START</b><extra></extra>",
            showlegend=True
        ))
        
        # === END ===
        fig.add_trace(go.Scatter(
            x=[df["east"].iloc[-1]],
            y=[df["north"].iloc[-1]],
            mode='markers+text',
            marker=dict(size=15, color='#FF3333', symbol='x', line=dict(color='darkred', width=2)),
            text=['LAND'],
            textposition="top center",
            textfont=dict(size=11, color='darkred', family='Arial Black'),
            name='Landing',
            hovertemplate="<b>LANDING</b><extra></extra>",
            showlegend=True
        ))
        
        # === DISTANCE & DIRECTION ===
        total_dist = np.sqrt((df["east"].iloc[-1] - df["east"].iloc[0])**2 + 
                            (df["north"].iloc[-1] - df["north"].iloc[0])**2)
        
        fig.update_layout(
            title={
                'text': f"<b>Flight Path - Top View</b><br><sub>Straight distance: {total_dist:.1f} m</sub>",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18}
            },
            xaxis=dict(
                title="<b>East (m)</b>",
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(200, 200, 200, 0.3)'
            ),
            yaxis=dict(
                title="<b>North (m)</b>",
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(200, 200, 200, 0.3)'
            ),
            width=800,
            height=700,
            showlegend=True,
            legend=dict(
                x=0.01,
                y=0.99,
                bgcolor='rgba(255, 255, 255, 0.9)',
                bordercolor='gray',
                borderwidth=1
            ),
            plot_bgcolor='rgba(240, 240, 245, 0.5)',
            paper_bgcolor='white',
            hovermode='closest'
        )
        
        return fig
    
    except Exception as e:
        logger.error(f"Error creating 2D top view: {e}")
        raise


def plot_altitude_profile(df):
    """
    Create altitude vs. distance profile for detailed analysis.
"""
    try:
        # Calculate cumulative distance along path
        distances = np.sqrt(np.diff(df["east"])**2 + np.diff(df["north"])**2)
        cumulative_dist = np.concatenate(([0], np.cumsum(distances)))
        
        # Create figure with secondary y-axis for speed
        fig = go.Figure()
        
        # === ALTITUDE LINE ===
        fig.add_trace(go.Scatter(
            x=cumulative_dist,
            y=df["up"],
            mode='lines',
            name='Altitude',
            line=dict(color='#1f77b4', width=3),
            yaxis='y1',
            fill='tozeroy',
            fillcolor='rgba(31, 119, 180, 0.2)',
            hovertemplate="<b>Position</b><br>Distance: %{x:.1f} m<br>Altitude: %{y:.1f} m<extra></extra>",
            showlegend=True
        ))
        
        # === SPEED OVERLAY (if available) ===
        if "speed" in df.columns:
            fig.add_trace(go.Scatter(
                x=cumulative_dist,
                y=df["speed"],
                mode='lines',
                name='Speed',
                line=dict(color='#ff7f0e', width=2, dash='dash'),
                yaxis='y2',
                hovertemplate="<b>Speed</b><br>Distance: %{x:.1f} m<br>Speed: %{y:.2f} m/s<extra></extra>",
                showlegend=True,
                opacity=0.7
            ))
        
        fig.update_layout(
            title="<b>Altitude Profile & Speed Dynamics</b>",
            xaxis=dict(
                title="<b>Distance Along Path (m)</b>",
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(200, 200, 200, 0.3)'
            ),
            yaxis=dict(
                title=dict(text="<b>Altitude (m)</b>", font=dict(color='#1f77b4')),
                tickfont=dict(color='#1f77b4'),
                showgrid=True,
                gridwidth=1,
                gridcolor='rgba(200, 200, 200, 0.3)'
            ),
            yaxis2=dict(
                title=dict(text="<b>Speed (m/s)</b>", font=dict(color='#ff7f0e')),
                tickfont=dict(color='#ff7f0e'),
                anchor='free',
                overlaying='y',
                side='right',
                position=0.99
            ),
            width=1000,
            height=500,
            showlegend=True,
            legend=dict(
                x=0.01,
                y=0.99,
                bgcolor='rgba(255, 255, 255, 0.9)',
                bordercolor='gray',
                borderwidth=1
            ),
            plot_bgcolor='rgba(240, 240, 245, 0.5)',
            paper_bgcolor='white',
            hovermode='x unified'
        )
        
        return fig
    
    except Exception as e:
        logger.error(f"Error creating altitude profile: {e}")
        raise

# Create interactive 3D trajectory plot with key points.
def plot_3d_trajectory(df, color_mode="speed"):

    required_cols = ["east", "north", "up"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing columns for visualization: {missing_cols}")
    
    if df.empty:
        raise ValueError("Empty DataFrame")
    
    try:
        # Prepare color values
        if color_mode == "speed":
            if "speed" not in df.columns:
                logger.warning("'speed' column not found, using time as color")
                color_values = (df["time_us"] / 1e6).values if "time_us" in df.columns else np.arange(len(df))
                color_title = "Time (s)"
                color_scale = "Blues"
            else:
                color_values = df["speed"].values
                color_title = "Speed (m/s)"
                color_scale = "Turbo"
        else:  # time mode
            if "time_us" not in df.columns:
                logger.warning("'time_us' column not found, using index as color")
                color_values = np.arange(len(df))
                color_title = "Sample Index"
                color_scale = "Viridis"
            else:
                color_values = (df["time_us"] / 1e6).values
                color_title = "Time (s)"
                color_scale = "Plasma"
        
        # Handle NaN values properly and convert to list for Plotly
        color_values = np.asarray(color_values, dtype=float)
        color_values = np.nan_to_num(color_values, nan=0.0, posinf=0.0, neginf=0.0)
        color_values = color_values.tolist()  # Convert numpy array to Python list
        
        # === MAIN TRAJECTORY LINE ===
        fig = go.Figure(data=[go.Scatter3d(
            x=df["east"],
            y=df["north"],
            z=df["up"],
            mode='lines',
            line=dict(
                width=8,
                color=color_values,
                colorscale=color_scale,
                colorbar=dict(
                    title=f"<b>{color_title}</b>",
                    thickness=20,
                    len=0.7,
                    x=1.08,
                    tickfont=dict(size=11)
                ),
                showscale=True
            ),
            name="Flight Path",
            hovertemplate="<b>Trajectory</b><br>" +
                          "East: %{x:.1f} m<br>" +
                          "North: %{y:.1f} m<br>" +
                          "Altitude: %{z:.1f} m<extra></extra>",
            showlegend=False
        )])
        
        # === START POINT ===
        fig.add_trace(go.Scatter3d(
            x=[df["east"].iloc[0]],
            y=[df["north"].iloc[0]],
            z=[df["up"].iloc[0]],
            mode='markers+text',
            marker=dict(
                size=8,
                color='#00CC00',
                line=dict(color='darkgreen', width=3),
                opacity=0.9
            ),
            text=["START"],
            textposition="top center",
            textfont=dict(size=12, color='black', family='Arial Black'),
            name='Start Point',
            hovertemplate="<b>START</b><br>" +
                          "East: %{x:.1f} m<br>" +
                          "North: %{y:.1f} m<br>" +
                          "Altitude: %{z:.1f} m<extra></extra>",
            showlegend=True
        ))
        
        # === END POINT ===
        fig.add_trace(go.Scatter3d(
            x=[df["east"].iloc[-1]],
            y=[df["north"].iloc[-1]],
            z=[df["up"].iloc[-1]],
            mode='markers+text',
            marker=dict(
                size=4,
                color='#FF3333',
                symbol='x',
                line=dict(color='red', width=3),
                opacity=0.9
            ),
            text=["LAND"],
            textposition="top center",
            textfont=dict(size=12, color='black', family='Arial Black'),
            name='Landing Point',
            hovertemplate="<b>LANDING</b><br>" +
                          "East: %{x:.1f} m<br>" +
                          "North: %{y:.1f} m<br>" +
                          "Altitude: %{z:.1f} m<extra></extra>",
            showlegend=True
        ))
        
        # === KEY ALTITUDE POINTS ===
        if "up" in df.columns:
            max_alt_idx = df["up"].idxmax()
            min_alt_idx = df["up"].idxmin()
            
            if max_alt_idx != df.index[0] and max_alt_idx != df.index[-1]:
                fig.add_trace(go.Scatter3d(
                    x=[df.loc[max_alt_idx, "east"]],
                    y=[df.loc[max_alt_idx, "north"]],
                    z=[df.loc[max_alt_idx, "up"]],
                    mode='markers+text',
                    marker=dict(
                        size=8,
                        color='#FFD700',
                        symbol='diamond-open',
                        line=dict(color='orange', width=2)
                    ),
                    text=[f"MAX: {df.loc[max_alt_idx, 'up']:.1f}m"],
                    textposition="top center",
                    textfont=dict(size=10, color='orange'),
                    name='Max Altitude',
                    hovertemplate="<b>MAX ALTITUDE</b><br>" +
                                  "Altitude: %{z:.1f} m<extra></extra>",
                    showlegend=True
                ))
        
        # === SPEED MARKERS (every 25% of flight for visual guides) ===
        if len(df) > 4:
            step = len(df) // 4
            for i in range(1, 4):
                idx = i * step
                if idx < len(df):
                    fig.add_trace(go.Scatter3d(
                        x=[df.iloc[idx]["east"]],
                        y=[df.iloc[idx]["north"]],
                        z=[df.iloc[idx]["up"]],
                        mode='markers',
                        marker=dict(
                            size=6,
                            color='rgba(100, 100, 255, 0.5)',
                            symbol='circle'
                        ),
                        showlegend=False,
                        hovertemplate="<b>Waypoint " + str(i) + "</b><br>" +
                                      "Progress: " + str(int(100*i/4)) + "%<extra></extra>"
                    ))
        
        # === REFERENCE PLANE (ground level) ===
        min_east = df["east"].min()
        max_east = df["east"].max()
        min_north = df["north"].min()
        max_north = df["north"].max()
        
        # Add ground reference plane
        fig.add_trace(go.Surface(
            x=[[min_east, max_east], [min_east, max_east]],
            y=[[min_north, min_north], [max_north, max_north]],
            z=[[0, 0], [0, 0]],
            colorscale=[[0, 'rgba(200, 200, 200, 0.1)'], [1, 'rgba(200, 200, 200, 0.1)']],
            showscale=False,
            hoverinfo='skip',
            opacity=0.2,
            name='Ground Level'
        ))
        
        # === LAYOUT ===
        fig.update_layout(
            title={
                'text': "<b>3D Flight Trajectory Analysis</b><br>" +
                        "<sub>Interactive 3D visualization of flight path (ENU coordinates)</sub>",
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 20}
            },
            scene=dict(
                xaxis=dict(
                    title="<b>East (m)</b>",
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(200, 200, 200, 0.3)',
                    zeroline=True,
                    zerolinewidth=2,
                    zerolinecolor='rgba(100, 100, 100, 0.5)'
                ),
                yaxis=dict(
                    title="<b>North (m)</b>",
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(200, 200, 200, 0.3)',
                    zeroline=True,
                    zerolinewidth=2,
                    zerolinecolor='rgba(100, 100, 100, 0.5)'
                ),
                zaxis=dict(
                    title="<b>Altitude (m)</b>",
                    showgrid=True,
                    gridwidth=1,
                    gridcolor='rgba(200, 200, 200, 0.3)',
                    zeroline=True,
                    zerolinewidth=2,
                    zerolinecolor='rgba(100, 100, 100, 0.5)'
                ),
                aspectmode='data',
                bgcolor='rgba(245, 245, 250, 0.5)',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.3)  # Better default viewing angle
                )
            ),
            width=1200,
            height=800,
            showlegend=True,
            legend=dict(
                x=0.01,
                y=0.99,
                bgcolor='rgba(255, 255, 255, 0.9)',
                bordercolor='rgba(100, 100, 100, 0.5)',
                borderwidth=2,
                font=dict(size=11),
                tracegroupgap=10
            ),
            margin=dict(l=0, r=150, t=100, b=0),
            font=dict(family='Arial, sans-serif', size=12, color='#333333'),
            plot_bgcolor='rgba(240, 240, 245, 0.5)',
            paper_bgcolor='white',
            hovermode='closest'
        )
        
        # Add interaction instructions
        fig.add_annotation(
            text="💡 <b>Rotate</b>: Click + Drag | <b>Zoom</b>: Scroll",
            xref="paper", yref="paper",
            x=0.01, y=0.01,
            showarrow=False,
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="gray",
            borderwidth=1,
            font=dict(size=10, color="gray"),
            align="left"
        )
        
        return fig
    
    except Exception as e:
        logger.error(f"Error creating 3D visualization: {e}")
        raise