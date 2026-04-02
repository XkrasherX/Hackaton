import plotly.graph_objects as go
import numpy as np
import logging

logger = logging.getLogger(__name__)


def plot_3d_trajectory(df, color_mode="speed"):
    """
    Create interactive 3D trajectory plot.
    
    Args:
        df: DataFrame with columns 'east', 'north', 'up' (and optionally 'speed', 'time_us')
        color_mode: "speed" or "time" - how to color the trajectory
        
    Returns:
        plotly figure object
        
    Raises:
        ValueError: If required columns are missing
    """
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
                color_values = df["time_us"] / 1e6 if "time_us" in df.columns else np.arange(len(df))
                color_title = "Time (s)"
            else:
                color_values = df["speed"]
                color_title = "Speed (m/s)"
        else:  # time mode
            if "time_us" not in df.columns:
                logger.warning("'time_us' column not found, using index as color")
                color_values = np.arange(len(df))
                color_title = "Sample Index"
            else:
                color_values = df["time_us"] / 1e6
                color_title = "Time (s)"
        
        # Handle NaN values
        color_values = np.nan_to_num(color_values, nan=0)
        
        # Create 3D scatter plot
        fig = go.Figure(data=[go.Scatter3d(
            x=df["east"],
            y=df["north"],
            z=df["up"],
            mode='lines',
            line=dict(
                width=6,
                color=color_values,
                colorscale="Viridis",
                colorbar=dict(
                    title=color_title,
                    thickness=15,
                    len=0.7,
                    x=1.02
                ),
                showscale=True
            ),
            name="Flight Path"
        )])
        
        # Add start and end markers
        fig.add_trace(go.Scatter3d(
            x=[df["east"].iloc[0]],
            y=[df["north"].iloc[0]],
            z=[df["up"].iloc[0]],
            mode='markers',
            marker=dict(size=10, color='green'),
            name='Start',
            showlegend=True
        ))
        
        fig.add_trace(go.Scatter3d(
            x=[df["east"].iloc[-1]],
            y=[df["north"].iloc[-1]],
            z=[df["up"].iloc[-1]],
            mode='markers',
            marker=dict(size=10, color='red'),
            name='End',
            showlegend=True
        ))
        
        # Update layout
        fig.update_layout(
            title="3D Flight Trajectory (ENU Coordinates)",
            scene=dict(
                xaxis=dict(title="East (m)"),
                yaxis=dict(title="North (m)"),
                zaxis=dict(title="Up/Altitude (m)"),
                aspectmode='data'
            ),
            width=1000,
            height=800,
            showlegend=True,
            legend=dict(
                x=0.02,
                y=0.98,
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='black',
                borderwidth=1
            )
        )
        
        return fig
    
    except Exception as e:
        logger.error(f"Error creating 3D visualization: {e}")
        raise