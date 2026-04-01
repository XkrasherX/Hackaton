import plotly.graph_objects as go


def plot_3d_trajectory(df, color_mode="speed"):

    if color_mode == "speed":
        color_values = df["speed"]
        color_title = "Speed (m/s)"
    else:
        color_values = df["time_us"] / 1e6
        color_title = "Time (s)"

    fig = go.Figure(data=[go.Scatter3d(
        x=df["east"],
        y=df["north"],
        z=df["up"],
        mode='lines',
        line=dict(
            width=6,
            color=color_values,
            colorscale="Turbo",
            colorbar=dict(title=color_title)
        )
    )])

    fig.update_layout(
        scene=dict(
            xaxis_title="East (m)",
            yaxis_title="North (m)",
            zaxis_title="Up (m)"
        )
    )

    return fig