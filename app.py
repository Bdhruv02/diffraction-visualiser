import streamlit as st
import numpy as np
from physics import (
    compute_angles,
    single_slit_intensity,
    double_slit_intensity,
    grating_intensity,
    wavelength_to_rgb,
    PRESETS,
)
from plots import (
    make_intensity_plot,
    make_screen_heatmap,
    make_grating_order_plot,
    make_comparison_overlay,
)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Diffraction Pattern Visualizer",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

  html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0d0d14;
    color: #c8c8d4;
  }
  .stApp { background-color: #0d0d14; }

  /* Sidebar */
  section[data-testid="stSidebar"] {
    background-color: #12121e;
    border-right: 1px solid rgba(255,255,255,0.06);
  }
  section[data-testid="stSidebar"] .stMarkdown p {
    color: #888899;
    font-size: 0.78rem;
    letter-spacing: 0.06em;
    text-transform: uppercase;
  }

  /* Cards / metric tiles */
  div[data-testid="metric-container"] {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 14px;
  }
  div[data-testid="metric-container"] label {
    color: #666677 !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
  }
  div[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #e0e0f0 !important;
    font-size: 1.5rem !important;
    font-weight: 500;
  }

  /* Sliders */
  .stSlider > div[data-baseweb="slider"] {
    padding-top: 4px;
  }

  /* Section dividers */
  hr { border-color: rgba(255,255,255,0.06); margin: 1rem 0; }

  /* Pin button accent */
  .pin-btn button {
    background: rgba(100, 80, 220, 0.15) !important;
    border: 1px solid rgba(120, 100, 255, 0.3) !important;
    color: #b0a0ff !important;
  }

  /* Tabs */
  button[data-baseweb="tab"] {
    color: #888899;
    font-size: 0.85rem;
  }
  button[data-baseweb="tab"][aria-selected="true"] {
    color: #e0e0f0;
    border-bottom-color: #7060f0 !important;
  }
</style>
""", unsafe_allow_html=True)


# ── Session state defaults ─────────────────────────────────────────────────────
if "pinned" not in st.session_state:
    st.session_state.pinned = None
if "comparison_curves" not in st.session_state:
    st.session_state.comparison_curves = []


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🌊 Diffraction Visualizer")
    st.markdown("---")

    # Mode selector
    st.markdown("**mode**")
    mode = st.radio(
        "",
        ["Single slit", "Double slit", "Diffraction grating"],
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Preset selector
    st.markdown("**presets**")
    preset_name = st.selectbox("", list(PRESETS.keys()), label_visibility="collapsed")
    preset = PRESETS[preset_name]
    if preset_name != "Custom":
        st.caption(f"_{preset['description']}_")

    use_preset = st.button("Apply preset", use_container_width=True)

    st.markdown("---")

    # Parameters
    st.markdown("**parameters**")

    default_wl = preset["wavelength"] if use_preset else st.session_state.get("wavelength", 550)
    default_sw = preset["slit_width"] if use_preset else st.session_state.get("slit_width", 1.5)
    default_sd = preset["slit_sep"] if use_preset else st.session_state.get("slit_sep", 5.0)
    default_n = preset["n_slits"] if use_preset else st.session_state.get("n_slits", 6)

    wavelength = st.slider("Wavelength λ (nm)", 380, 750, default_wl, step=1)
    slit_width = st.slider("Slit width a (µm)", 0.1, 100.0, float(default_sw), step=0.1)

    if mode != "Single slit":
        slit_sep = st.slider("Slit separation d (µm)", 1.0, 20.0, float(default_sd), step=0.1)
    else:
        slit_sep = 5.0

    if mode == "Diffraction grating":
        n_slits = st.slider("Number of slits N", 2, 50, int(default_n), step=1)
    else:
        n_slits = 2

    screen_dist = st.slider("Screen distance D (m)", 0.1, 5.0, 1.0, step=0.1)

    # Save to session state
    st.session_state["wavelength"] = wavelength
    st.session_state["slit_width"] = slit_width
    st.session_state["slit_sep"] = slit_sep
    st.session_state["n_slits"] = n_slits

    st.markdown("---")

    # Display options
    st.markdown("**display options**")
    show_envelope = st.checkbox("Show sinc² envelope", value=False)
    use_log = st.checkbox("Log scale (Y axis)", value=False)
    show_orders = st.checkbox("Mark grating orders", value=True) if mode == "Diffraction grating" else False

    st.markdown("---")

    # Comparison mode
    st.markdown("**comparison mode**")
    col_pin, col_clear = st.columns(2)
    with col_pin:
        if st.button("📌 Pin current", use_container_width=True):
            st.session_state.pinned = {
                "intensity": None,  # filled below after compute
                "wavelength": wavelength,
                "label": f"λ={wavelength}nm a={slit_width:.1f}µm",
            }
            st.session_state["pin_pending"] = True
    with col_clear:
        if st.button("🗑 Clear pin", use_container_width=True):
            st.session_state.pinned = None

    add_to_compare = st.button("➕ Add to comparison", use_container_width=True)
    if st.button("Clear comparison", use_container_width=True):
        st.session_state.comparison_curves = []


# ── Compute intensity ──────────────────────────────────────────────────────────
angles = compute_angles(n_points=2000, max_angle_deg=8.0)

if mode == "Single slit":
    intensity = single_slit_intensity(angles, wavelength, slit_width)
    envelope = intensity.copy()
elif mode == "Double slit":
    intensity = double_slit_intensity(angles, wavelength, slit_width, slit_sep)
    envelope = single_slit_intensity(angles, wavelength, slit_width)
else:
    intensity = grating_intensity(angles, wavelength, slit_width, slit_sep, n_slits)
    envelope = single_slit_intensity(angles, wavelength, slit_width)

# Normalise
if intensity.max() > 0:
    intensity = intensity / intensity.max()
    envelope = envelope / envelope.max()

# Handle pin pending (need intensity computed first)
if st.session_state.get("pin_pending"):
    if st.session_state.pinned is not None:
        st.session_state.pinned["intensity"] = intensity.copy()
    st.session_state["pin_pending"] = False

if add_to_compare:
    label = f"{mode[:1]}S λ={wavelength} a={slit_width:.1f}"
    st.session_state.comparison_curves.append((intensity.copy(), wavelength, label))


# ── Header ─────────────────────────────────────────────────────────────────────
r, g, b = wavelength_to_rgb(wavelength)
color_hex = f"#{r:02x}{g:02x}{b:02x}"

st.markdown(
    f"""
    <div style='display:flex; align-items:center; gap:14px; margin-bottom:8px;'>
      <div style='width:18px;height:18px;border-radius:50%;
                  background:{color_hex};box-shadow:0 0 12px {color_hex}88;'></div>
      <h1 style='margin:0; font-size:1.5rem; font-weight:500; color:#e0e0f0;'>
        {mode}  —  λ = {wavelength} nm
      </h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# Metric tiles
mc1, mc2, mc3, mc4 = st.columns(4)
with mc1:
    st.metric("Wavelength", f"{wavelength} nm")
with mc2:
    st.metric("Slit width", f"{slit_width:.1f} µm")
with mc3:
    label_3 = "Slit sep." if mode != "Single slit" else "—"
    val_3 = f"{slit_sep:.1f} µm" if mode != "Single slit" else "n/a"
    st.metric(label_3, val_3)
with mc4:
    label_4 = f"N slits" if mode == "Diffraction grating" else "Screen dist."
    val_4 = str(n_slits) if mode == "Diffraction grating" else f"{screen_dist:.1f} m"
    st.metric(label_4, val_4)

st.markdown("---")


# ── Main tabs ──────────────────────────────────────────────────────────────────
tab_main, tab_compare = st.tabs(["📈 Pattern & Screen", "🔀 Comparison"])

with tab_main:
    # Pinned curve reference
    pinned_intensity = None
    pinned_label = "Pinned"
    if st.session_state.pinned and st.session_state.pinned.get("intensity") is not None:
        pinned_intensity = st.session_state.pinned["intensity"]
        pinned_label = st.session_state.pinned["label"]

    # Intensity vs angle plot
    if mode == "Diffraction grating" and show_orders:
        fig_intensity = make_grating_order_plot(angles, intensity, wavelength, slit_sep)
    else:
        fig_intensity = make_intensity_plot(
            angles, intensity, wavelength,
            title=f"{mode} — intensity vs angle",
            pinned_intensity=pinned_intensity,
            pinned_label=pinned_label,
            show_envelope=show_envelope,
            envelope=envelope,
            use_log=use_log,
        )

    st.plotly_chart(fig_intensity, use_container_width=True)

    # Screen heatmap
    fig_screen = make_screen_heatmap(angles, intensity, wavelength, screen_dist)
    st.plotly_chart(fig_screen, use_container_width=True)

    # Fringe spacing info
    if mode != "Single slit":
        lam_m = wavelength * 1e-9
        d_m = slit_sep * 1e-6
        fringe_spacing_mm = (lam_m / d_m) * screen_dist * 1000
        st.info(
            f"**Fringe spacing** (first-order): "
            f"Δy = λD/d = **{fringe_spacing_mm:.2f} mm** at D = {screen_dist:.1f} m"
        )

with tab_compare:
    if not st.session_state.comparison_curves:
        st.info(
            "Add curves using **➕ Add to comparison** in the sidebar. "
            "Change parameters between additions to compare different configurations."
        )
    else:
        fig_comp = make_comparison_overlay(angles, st.session_state.comparison_curves)
        st.plotly_chart(fig_comp, use_container_width=True)

        st.markdown("**Curves in comparison:**")
        for i, (_, wl, lbl) in enumerate(st.session_state.comparison_curves):
            r2, g2, b2 = wavelength_to_rgb(wl)
            st.markdown(
                f"<span style='display:inline-block;width:10px;height:10px;"
                f"border-radius:2px;background:rgb({r2},{g2},{b2});margin-right:8px;'></span>"
                f"`{lbl}`",
                unsafe_allow_html=True,
            )


# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='font-size:0.72rem;color:#444455;text-align:center;'>"
    "Fraunhofer (far-field) approximation · intensities normalised to peak · "
    "built with Streamlit + Plotly + NumPy"
    "</p>",
    unsafe_allow_html=True,
)
