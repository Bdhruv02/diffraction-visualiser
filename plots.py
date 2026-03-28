import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from physics import wavelength_to_rgb, intensity_to_screen_positions


def _wl_color(wl):
    r, g, b = wavelength_to_rgb(wl)
    return f"rgb({r},{g},{b})"


def _wl_color_alpha(wl, alpha=0.25):
    r, g, b = wavelength_to_rgb(wl)
    return f"rgba({r},{g},{b},{alpha})"


PLOT_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#aaaaaa", size=12),
    margin=dict(l=50, r=20, t=40, b=50),
    legend=dict(
        bgcolor="rgba(20,20,30,0.7)",
        bordercolor="rgba(255,255,255,0.1)",
        borderwidth=1,
        font=dict(size=11),
    ),
)

AXIS_STYLE = dict(
    showgrid=True,
    gridcolor="rgba(255,255,255,0.07)",
    zeroline=True,
    zerolinecolor="rgba(255,255,255,0.15)",
    zerolinewidth=1,
    color="#888888",
)


def make_intensity_plot(
    angles,
    intensity,
    wavelength_nm,
    title="Intensity vs Angle",
    pinned_intensity=None,
    pinned_label="Pinned",
    show_envelope=False,
    envelope=None,
    use_log=False,
):
    """
    Main intensity vs angle line chart.
    Optionally overlays a pinned comparison curve.
    Optionally overlays the sinc² diffraction envelope.
    Supports linear and log scale on Y axis.
    """
    angles_deg = np.rad2deg(angles)
    color = _wl_color(wavelength_nm)
    fill_color = _wl_color_alpha(wavelength_nm, 0.18)

    y_data = np.log10(np.clip(intensity, 1e-6, None)) if use_log else intensity
    y_label = "log₁₀(Intensity)" if use_log else "Normalised intensity"

    fig = go.Figure()

    # Pinned comparison curve (ghost)
    if pinned_intensity is not None:
        y_pinned = np.log10(np.clip(pinned_intensity, 1e-6, None)) if use_log else pinned_intensity
        fig.add_trace(go.Scatter(
            x=angles_deg, y=y_pinned,
            mode="lines",
            name=pinned_label,
            line=dict(color="rgba(180,180,180,0.5)", width=1.5, dash="dash"),
        ))

    # Diffraction envelope
    if show_envelope and envelope is not None:
        y_env = np.log10(np.clip(envelope, 1e-6, None)) if use_log else envelope
        fig.add_trace(go.Scatter(
            x=angles_deg, y=y_env,
            mode="lines",
            name="Sinc² envelope",
            line=dict(color="rgba(255,200,80,0.55)", width=1.2, dash="dot"),
        ))

    # Main intensity curve (filled)
    fig.add_trace(go.Scatter(
        x=angles_deg, y=y_data,
        mode="lines",
        name=f"λ = {wavelength_nm} nm",
        line=dict(color=color, width=2.5),
        fill="tozeroy",
        fillcolor=fill_color,
    ))

    fig.update_layout(
        **PLOT_LAYOUT,
        title=dict(text=title, font=dict(size=14, color="#cccccc"), x=0.01),
        xaxis=dict(title="Angle θ (degrees)", **AXIS_STYLE),
        yaxis=dict(title=y_label, **AXIS_STYLE),
        height=360,
    )
    return fig


def make_screen_heatmap(angles, intensity, wavelength_nm, screen_distance_m=1.0):
    """
    2-D false-colour heatmap simulating the diffraction pattern on a screen.
    The horizontal axis is position (mm), the vertical axis adds visual height.
    """
    pos_mm = intensity_to_screen_positions(angles, screen_distance_m)
    r, g, b = wavelength_to_rgb(wavelength_nm)

    # Build a 2D array (repeat rows for visual height)
    n_rows = 60
    screen_2d = np.tile(intensity, (n_rows, 1))

    # Custom colour scale: black → light colour
    colorscale = [
        [0.0, "rgb(0,0,0)"],
        [0.3, f"rgb({r//3},{g//3},{b//3})"],
        [0.7, f"rgb({r//2},{g//2},{b//2})"],
        [1.0, f"rgb({r},{g},{b})"],
    ]

    fig = go.Figure(go.Heatmap(
        z=screen_2d,
        x=pos_mm,
        y=list(range(n_rows)),
        colorscale=colorscale,
        showscale=False,
        hoverinfo="skip",
    ))

    fig.update_layout(
        **PLOT_LAYOUT,
        title=dict(text="Screen simulation", font=dict(size=14, color="#cccccc"), x=0.01),
        xaxis=dict(
            title="Position on screen (mm)",
            **AXIS_STYLE,
            range=[pos_mm.min(), pos_mm.max()],
        ),
        yaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
        height=200,
    )
    return fig


def make_grating_order_plot(angles, intensity, wavelength_nm, slit_sep_um):
    """
    Mark the theoretical principal maxima on the intensity plot
    (where d*sin(theta) = m*lambda for integer m).
    """
    lam = wavelength_nm * 1e-9
    d = slit_sep_um * 1e-6
    angles_deg = np.rad2deg(angles)
    color = _wl_color(wavelength_nm)
    fill_color = _wl_color_alpha(wavelength_nm, 0.18)

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=angles_deg, y=intensity,
        mode="lines",
        line=dict(color=color, width=2.5),
        fill="tozeroy",
        fillcolor=fill_color,
        name="Intensity",
    ))

    # Annotate principal maxima
    for m in range(-5, 6):
        sin_val = m * lam / d
        if abs(sin_val) > 0.99:
            continue
        th_m = np.rad2deg(np.arcsin(sin_val))
        fig.add_vline(
            x=th_m,
            line=dict(color="rgba(255,220,100,0.4)", width=1, dash="dot"),
            annotation_text=f"m={m}" if m != 0 else "m=0",
            annotation_font=dict(size=9, color="rgba(255,220,100,0.7)"),
            annotation_position="top",
        )

    fig.update_layout(
        **PLOT_LAYOUT,
        title=dict(text="Grating — principal maxima", font=dict(size=14, color="#cccccc"), x=0.01),
        xaxis=dict(title="Angle θ (degrees)", **AXIS_STYLE),
        yaxis=dict(title="Normalised intensity", **AXIS_STYLE),
        height=360,
    )
    return fig


def make_comparison_overlay(
    angles,
    curves: list,  # list of (intensity_array, wavelength_nm, label)
):
    """
    Overlay multiple intensity curves (for comparison mode).
    Each entry: (intensity, wavelength_nm, label_str)
    """
    angles_deg = np.rad2deg(angles)
    fig = go.Figure()

    for (intens, wl, label) in curves:
        color = _wl_color(wl)
        fill_color = _wl_color_alpha(wl, 0.12)
        fig.add_trace(go.Scatter(
            x=angles_deg, y=intens,
            mode="lines",
            name=label,
            line=dict(color=color, width=2),
            fill="tozeroy",
            fillcolor=fill_color,
        ))

    fig.update_layout(
        **PLOT_LAYOUT,
        title=dict(text="Multi-curve comparison", font=dict(size=14, color="#cccccc"), x=0.01),
        xaxis=dict(title="Angle θ (degrees)", **AXIS_STYLE),
        yaxis=dict(title="Normalised intensity", **AXIS_STYLE),
        height=380,
    )
    return fig
