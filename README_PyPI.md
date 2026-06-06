# RCAIDE GUI: Research Community Aircraft Interdisciplinary Design Environment — Graphical User Interface

The RCAIDE GUI is an interactive desktop application for [RCAIDE](https://pypi.org/project/RCAIDE-LEADS/), a powerful open-source Python platform for aircraft design and analysis. It provides an intuitive visual workflow for aerospace engineers, researchers, and students to design, configure, and simulate aircraft without writing Python scripts directly.

## Features

- **Vehicle Setup** — Build up aircraft geometry using a component tree (wings, fuselages, nacelles, landing gear, booms, propulsors) with a live 3D preview
- **Geometry Visualization** — Full 3D VTK rendering environment; inspect component placement and export top/front/side view images
- **Configurations Setup** — Define base, takeoff, cruise, and landing configurations with control surface deflections and active propulsor settings
- **Analyses Setup** — Configure multidisciplinary solvers (aerodynamics, atmosphere, weights, acoustics) and toggle fidelity levels
- **Mission Setup** — Chain flight segments (takeoff, climb, cruise, descent) with custom altitudes, speeds, and linked analyses
- **Mission Simulation** — Execute the backend RCAIDE solvers and view numerical and graphical results (performance, payload-range, stability)

## Installation

```bash
pip install RCAIDE-GUI
```

Installing `RCAIDE-GUI` automatically installs [RCAIDE-LEADS](https://pypi.org/project/RCAIDE-LEADS/) and all required dependencies.

## Launch

```bash
rcaide-gui
```

Or via Python:

```bash
python -m main
```

## Requirements

- Python ≥ 3.9
- PyQt6
- pyvista / pyvistaqt
- RCAIDE-LEADS (installed automatically)

Refer to the [installation guide](https://www.docs.rcaide.leadsresearchgroup.com/install.html) for platform-specific notes.

## Contributing

We welcome contributions! Please see our [contribution guidelines](https://www.docs.rcaide.leadsresearchgroup.com/contributing.html).

## Contact

For feedback, issues, or feature requests, use our [GitHub Issues](https://github.com/leadsgroup/RCAIDE_GUI/issues) or join our [Discussions](https://github.com/leadsgroup/RCAIDE_GUI/discussions).
