# 🌊 Diffraction Pattern Visualizer

An interactive simulation for visualising single-slit, double-slit, and diffraction grating patterns — built with **Streamlit**, **NumPy**, and **Plotly**.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-red)
![Plotly](https://img.shields.io/badge/Plotly-5.22+-purple)

---

## Features

- **Three diffraction modes** — single slit, double slit, diffraction grating
- **Real-time sliders** for wavelength (λ), slit width (a), slit separation (d), number of slits (N), and screen distance (D)
- **2D screen simulation** — heatmap showing how the pattern looks on a physical screen
- **Sinc² envelope overlay** — visualise the single-slit modulation on interference patterns
- **Log scale toggle** — reveal weak secondary maxima hidden on linear scale
- **Grating order markers** — principal maxima annotated with diffraction order m
- **Pin & compare mode** — pin a curve, change parameters, see the difference overlaid
- **Multi-curve comparison tab** — add multiple configurations and compare side by side
- **Real-world presets** — sodium lamp, red laser, blue LED, CD grating, human hair

---

## Project structure

```
diffraction-visualizer/
├── app.py            # Streamlit UI — sliders, layout, tabs
├── physics.py        # NumPy maths — all intensity calculations
├── plots.py          # Plotly chart builders
├── requirements.txt  # Python dependencies
└── .gitignore
```

---

## Quick start

### 1. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/diffraction-visualizer.git
cd diffraction-visualizer
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
streamlit run app.py
```

The app will open automatically at `http://localhost:8501`.

---

## Physics background

All calculations use the **Fraunhofer (far-field) approximation**, valid when the screen distance D >> slit dimensions.

| Mode | Formula |
|------|---------|
| Single slit | I(θ) = sinc²(β), where β = πa sinθ / λ |
| Double slit | I(θ) = sinc²(β) · cos²(δ), where δ = πd sinθ / λ |
| Grating (N slits) | I(θ) = sinc²(β) · [sin(Nδ) / (N·sin(δ))]² |

---

## Extending the project

- Add **Fresnel diffraction** for near-field behaviour
- Add **circular aperture** (Airy disc) — `J₁(x)/x` Bessel function
- Export the intensity array as CSV for further analysis
- Add a **wavelength sweep animation** showing how fringe spacing changes with colour

---

## License

MIT
