  <p align="center">
    <img src="https://github.com/leadsgroup/RCAIDE_Website/blob/main/assets/img/RCAIDE_Logo_No_Background.png" width=25% height=25%> 
  </p> 

  # 
  <div align="center">

  <!-- [![CI](https://github.com/leadsgroup/RCAIDE_LEADS/actions/workflows/CI.yml/badge.svg?branch=master)](https://github.com/leadsgroup/RCAIDE_LEADS/actions/workflows/CI.yml)
  [![Documentation](https://github.com/leadsgroup/RCAIDE_LEADS/actions/workflows/sphinx_docs.yml/badge.svg)](https://github.com/leadsgroup/RCAIDE_LEADS/actions/workflows/sphinx_docs.yml)
  [![codecov](https://codecov.io/gh/leadsgroup/RCAIDE_LEADS/graph/badge.svg?token=WZOFW5EKWJ)](https://codecov.io/gh/leadsgroup/RCAIDE_LEADS)
  [![PyPI Downloads](https://static.pepy.tech/badge/rcaide-leads)](https://pepy.tech/projects/rcaide-leads) -->



  </div>

  [RCAIDE: Graphical User Interface]([link](https://www.rcaide.leadsresearchgroup.com/gui/))
  =======
  The Research Community Aircraft Interdisciplinary Design Environment (RCAIDE) Graphical User Interface (GUI) is an interactive, visual workflow for RCAIDE, a powerful open-source Python platform that revolutionizes aircraft design and analysis at a high-fidelity. The GUI provides an intuitive desktop application that allows aerospace engineers, researchers, and students to accelerate aircraft development and explore innovative designs without the need to write complex Python scripts. The software is developed and maintained by the [Lab for Electric Aircraft Design and Sustainability](https://www.leadsresearchgroup.com/)

  [Find more information on RCAIDE, its capabilities, external interfaces, and how to download here.](https://www.docs.rcaide.leadsresearchgroup.com/install.html)
  
  ## RCAIDE GUI Architecture 
   The RCAIDE GUI is structured into tabs to flow with the aircraft design process.

  * **Vehicle Setup**: This is the foundation of designing your aircraft - defining your aircraft's geometry. Using a component tree, add wings, fuselages, nacelles, landing gear, booms, and propulsors. Then, specify parameters and dimensions to build up your aircraft. This tab also features a live 3D preview of the aircraft to instantly verify geometric dimensions and placements.
  * **Geometry Visualization**: A complete 3D rendering environment powered by VTK. Using this tab, users can inspect their aircraft, check component placement, and export top, front, and side view visualization images before conducting further analysis.
  * **Configurations Setup**: Define the physical states of the aircraft during different phases of flight. Users can set up base, takeoff, cruise, and landing configurations by specifying control surface deflections, landing gear deployment states, and active propulsors.
  * **Analyses Setup**: Define the analysis for RCAIDE's multidisciplinary solvers. Users can toggle and select their analyses requirements and configure the fidelity of the physics models, including aerodynamic solvers, atmospheric conditions, weights, and aeroacoustic parameters.
  * **Mission Setup**: Construct the flight profile. Users can chain together flight segments (takeoff, climb, cruise, descent). Each segment is customized with specific altitudes and speeds, and is linked to previously defined aircraft configurations and analyses.
  * **Mission Simulation**: The tab that displays your results. Once the vehicle, analyses, and mission are defined, the tab runs the backend RCAIDE solvers and returns numerical and graphical outputs (such as performance data, payload-range charts, and stability metrics) for the user to evaluate and export.

  ```mermaid
  %%{init: {'flowchart': {'curve': 'linear', 'nodeSpacing': 50, 'rankSpacing': 50}}}%%
  flowchart LR
      Vehicle Setup[Vehicle Setup]
      Geometry Visualization[Geometry Visualization]
      Configurations Setup[Configurations Setup]
      Analyses Setup[Analyses Setup]
      Mission Setup[Mission Setup]
      Mission Simulation[Mission Simulation]
      
      
      Vehicle Setup ---> Geometry Visualization
      Geometry Visualization ---> Configurations Setup
      Configurations Setup ---> Analyses Setup
      Analyses Setup ---> Mission Setup
      Mission Setup ---> Mission Simulation


      style Vehicle Setup fill:#0d6dc5,color:#fff
      style Geometry Visualization fill:#0d6dc5,color:#fff
      style RCAIDE_LEADS fill:#0d6dc5,color:#fff
      style Configurations Setup fill:#0d6dc5,color:#fff
      style Mission Setup fill:#0d6dc5,color:#fff
      style Mission Simulation fill:#0d6dc5,color:#fff
  ```

  **Getting Involved**   

  If you'd like to help us develop RCAIDE by adding new methods, writing documentation, or fixing embarrassing bugs, please look at these [guidelines](https://www.docs.rcaide.leadsresearchgroup.com/contributing.html).

  Submit improvements or new features with a [pull request](https://github.com/leadsgroup/RCAIDE_LEADS/pulls)

  ## Get in touch

  Share feedback, report issues, and request features via or [Github Issues](https://github.com/leadsgroup/RCAIDE_LEADS/issues)

  Engage with peers and maintainers in [Discussions](https://github.com/leadsgroup/RCAIDE_LEADS/discussions)