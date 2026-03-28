import numpy as np


def compute_angles(n_points=2000, max_angle_deg=8.0):
    """Return an array of angles in radians from -max to +max."""
    max_rad = np.deg2rad(max_angle_deg)
    return np.linspace(-max_rad, max_rad, n_points)


def single_slit_intensity(angles, wavelength_nm, slit_width_um):
    """
    Single-slit Fraunhofer diffraction intensity.

    I(theta) = sinc^2(beta)
    where beta = pi * a * sin(theta) / lambda
    """
    lam = wavelength_nm * 1e-9
    a = slit_width_um * 1e-6

    sin_theta = np.sin(angles)
    beta = np.pi * a * sin_theta / lam

    # sinc: handle beta=0 to avoid division by zero
    sinc = np.where(np.abs(beta) < 1e-12, 1.0, np.sin(beta) / beta)
    return sinc ** 2


def double_slit_intensity(angles, wavelength_nm, slit_width_um, slit_sep_um):
    """
    Double-slit interference × single-slit diffraction envelope.

    I(theta) = sinc^2(beta) * cos^2(delta)
    where beta = pi*a*sin/lam, delta = pi*d*sin/lam
    """
    lam = wavelength_nm * 1e-9
    a = slit_width_um * 1e-6
    d = slit_sep_um * 1e-6

    sin_theta = np.sin(angles)
    beta = np.pi * a * sin_theta / lam
    delta = np.pi * d * sin_theta / lam

    sinc = np.where(np.abs(beta) < 1e-12, 1.0, np.sin(beta) / beta)
    envelope = sinc ** 2
    interference = np.cos(delta) ** 2

    return envelope * interference


def grating_intensity(angles, wavelength_nm, slit_width_um, slit_sep_um, n_slits):
    """
    Diffraction grating: single-slit envelope × grating factor.

    I(theta) = sinc^2(beta) * [sin(N*delta) / (N*sin(delta))]^2
    """
    lam = wavelength_nm * 1e-9
    a = slit_width_um * 1e-6
    d = slit_sep_um * 1e-6
    N = n_slits

    sin_theta = np.sin(angles)
    beta = np.pi * a * sin_theta / lam
    delta = np.pi * d * sin_theta / lam

    sinc = np.where(np.abs(beta) < 1e-12, 1.0, np.sin(beta) / beta)
    envelope = sinc ** 2

    num = np.sin(N * delta)
    den = np.sin(delta)
    grating = np.where(np.abs(den) < 1e-9, float(N), num / den)
    grating_factor = (grating / N) ** 2

    return envelope * grating_factor


def intensity_to_screen_positions(angles, screen_distance_m=1.0):
    """Convert angles to physical positions on screen (in mm)."""
    return np.tan(angles) * screen_distance_m * 1000  # mm


def wavelength_to_rgb(wavelength_nm):
    """
    Approximate conversion of visible wavelength (380–750nm) to RGB tuple (0–255).
    Based on Dan Bruton's algorithm.
    """
    wl = wavelength_nm
    if wl < 380 or wl > 750:
        return (128, 0, 128)

    if 380 <= wl < 440:
        r = -(wl - 440) / 60
        g = 0.0
        b = 1.0
    elif 440 <= wl < 490:
        r = 0.0
        g = (wl - 440) / 50
        b = 1.0
    elif 490 <= wl < 510:
        r = 0.0
        g = 1.0
        b = -(wl - 510) / 20
    elif 510 <= wl < 580:
        r = (wl - 510) / 70
        g = 1.0
        b = 0.0
    elif 580 <= wl < 645:
        r = 1.0
        g = -(wl - 645) / 65
        b = 0.0
    else:
        r = 1.0
        g = 0.0
        b = 0.0

    # Intensity falloff near edges of visible spectrum
    if 380 <= wl < 420:
        factor = 0.3 + 0.7 * (wl - 380) / 40
    elif 700 < wl <= 750:
        factor = 0.3 + 0.7 * (750 - wl) / 50
    else:
        factor = 1.0

    r_int = int(round(r * 255 * factor))
    g_int = int(round(g * 255 * factor))
    b_int = int(round(b * 255 * factor))
    return (r_int, g_int, b_int)


PRESETS = {
    "Sodium lamp (589 nm)": {
        "wavelength": 589,
        "slit_width": 1.0,
        "slit_sep": 4.0,
        "n_slits": 5,
        "description": "Yellow-orange light from a sodium vapour lamp — common in street lighting."
    },
    "Laser pointer — red (650 nm)": {
        "wavelength": 650,
        "slit_width": 0.8,
        "slit_sep": 3.5,
        "n_slits": 2,
        "description": "Standard red laser pointer, classic double-slit demo."
    },
    "Blue LED (470 nm)": {
        "wavelength": 470,
        "slit_width": 1.2,
        "slit_sep": 5.0,
        "n_slits": 8,
        "description": "Blue LED through a fine grating — tight fringes visible."
    },
    "CD track grating (~780 nm)": {
        "wavelength": 780,
        "slit_width": 2.0,
        "slit_sep": 1.6,
        "n_slits": 15,
        "description": "CD tracks act as a reflection grating with ~1.6 µm pitch."
    },
    "Human hair (~70 µm width)": {
        "wavelength": 550,
        "slit_width": 70.0,
        "slit_sep": 5.0,
        "n_slits": 2,
        "description": "A human hair diffracts green light into a very narrow central peak."
    },
    "Custom": {
        "wavelength": 550,
        "slit_width": 1.5,
        "slit_sep": 5.0,
        "n_slits": 6,
        "description": "Set your own parameters using the sliders."
    },
}
