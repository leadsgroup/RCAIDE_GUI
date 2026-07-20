# RCAIDE_GUI/tabs/geometry/widgets/powertrain/propulsors/turbojet_widget.py

import RCAIDE

from tabs.geometry.widgets.powertrain.propulsors.base_propulsor_widget import (
    BasePropulsorWidget,
    TURBOJET_COMPONENT_FIELDS,
)
from utilities import Units


class TurbojetWidget(BasePropulsorWidget):
    # Turbojet uses the gas-turbine core chain without a fan or propeller.
    propulsor_type = "Turbojet"
    propulsor_class = RCAIDE.Library.Components.Powertrain.Propulsors.Turbojet
    subcomponent_classes = {
        "ram": RCAIDE.Library.Components.Powertrain.Converters.Ram,
        "inlet_nozzle": RCAIDE.Library.Components.Powertrain.Converters.Compression_Nozzle,
        "low_pressure_compressor": RCAIDE.Library.Components.Powertrain.Converters.Compressor,
        "high_pressure_compressor": RCAIDE.Library.Components.Powertrain.Converters.Compressor,
        "low_pressure_turbine": RCAIDE.Library.Components.Powertrain.Converters.Turbine,
        "high_pressure_turbine": RCAIDE.Library.Components.Powertrain.Converters.Turbine,
        "combustor": RCAIDE.Library.Components.Powertrain.Converters.Combustor,
        "afterburner": RCAIDE.Library.Components.Powertrain.Converters.Combustor,
        "core_nozzle": RCAIDE.Library.Components.Powertrain.Converters.Expansion_Nozzle,
    }
    type_fields = [
        ("Turbojet Design", Units.Heading, ""),
        ("Bypass Ratio", Units.Unitless, "bypass_ratio"),
        ("Design Altitude", Units.Length, "design_altitude"),
        ("Afterburner Active", Units.Boolean, "afterburner_active"),
        ("Design Thrust", Units.Force, "design_thrust"),
        ("Design Mass Flow Rate", Units.Unitless, "design_mass_flow_rate"),
    ] + TURBOJET_COMPONENT_FIELDS
